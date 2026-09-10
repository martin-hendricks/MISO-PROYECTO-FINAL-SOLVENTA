# Registra la campana en el Programador de tareas de Windows y la arranca.
#
# Por que el Programador de tareas y no una terminal: la campana dura ~10 horas
# y no puede depender de que una ventana siga abierta, de que VS Code no se
# actualice de madrugada ni de que una sesion de Claude Code siga viva. Como
# tarea, sigue corriendo aunque se cierre todo lo demas.
#
#   .\scripts\programar_campana.ps1            # registra y lanza la campana
#   .\scripts\programar_campana.ps1 -Prueba    # solo comprueba el entorno
#   .\scripts\programar_campana.ps1 -Bloques "3"        # solo la compuerta
#   .\scripts\programar_campana.ps1 -Bloques "1 2 4"    # el resto
#   .\scripts\programar_campana.ps1 -Quitar    # borra las tareas registradas
#
# Seguimiento:  Get-Content results\campana_estado.txt
#               Get-Content results\campana.log -Wait -Tail 20
# Detener:      Stop-ScheduledTask -TaskName HA01-campana
param(
    [switch]$Prueba,
    [switch]$Quitar,
    [string]$Bloques = "3 1 2 4"
)

$nombres = @("HA01-campana", "HA01-prueba")
if ($Quitar) {
    foreach ($n in $nombres) {
        Unregister-ScheduledTask -TaskName $n -Confirm:$false -ErrorAction SilentlyContinue
    }
    "tareas HA01 eliminadas"
    return
}

$nombre   = if ($Prueba) { "HA01-prueba" } else { "HA01-campana" }
$pwsh     = (Get-Command pwsh -ErrorAction SilentlyContinue).Source
if (-not $pwsh) { $pwsh = (Get-Command powershell).Source }
$lanzador = Join-Path $PSScriptRoot "lanzar_campana.ps1"
$argumentos = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$lanzador`""
if ($Prueba) { $argumentos += " -Prueba" } else { $argumentos += " -Bloques `"$Bloques`"" }

$accion = New-ScheduledTaskAction -Execute $pwsh -Argument $argumentos
# Sesion interactiva del propio usuario: es la que tiene acceso a Docker Desktop.
$quien  = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
$ajustes = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 14) `
    -MultipleInstances IgnoreNew
# Un corte de corriente de unos segundos no debe matar diez horas de campana:
# por defecto Windows detiene las tareas al pasar a bateria.

Register-ScheduledTask -TaskName $nombre -Action $accion -Principal $quien `
    -Settings $ajustes -Description "Experimento HA-01 (Solventa)" -Force | Out-Null
Start-ScheduledTask -TaskName $nombre
"tarea '$nombre' registrada y lanzada (bloques: $Bloques)"
