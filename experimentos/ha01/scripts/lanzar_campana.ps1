# Lo ejecuta el Programador de tareas. No lanzarlo a mano: usar
# programar_campana.ps1, que registra la tarea y la arranca.
#
# La campana corre en bash (Git Bash) porque todo el protocolo esta escrito
# para bash. Este envoltorio solo existe para que el Programador de tareas
# pueda invocarlo con la ventana oculta y sin depender de ninguna terminal.
param(
    # En vez de la campana, comprueba que desde el contexto de la tarea se
    # ven Docker, Python, curl y la API. Escribe results/prueba_tarea.log.
    [switch]$Prueba,
    # Bloques a ejecutar y en que orden. Por defecto la campana completa.
    [string]$Bloques = "3 1 2 4"
)

$raiz = Split-Path -Parent $PSScriptRoot
$bash = Join-Path $env:ProgramFiles "Git\bin\bash.exe"
if (-not (Test-Path $bash)) { throw "No se encuentra Git Bash en $bash" }

if ($Prueba) {
    $comando = "{ date; whoami; command -v docker python curl; " +
               "docker info --format 'docker {{.ServerVersion}} | {{.MemTotal}} bytes'; " +
               "python --version; " +
               "curl -s -o /dev/null -w 'api /health: %{http_code}\n' http://localhost:8000/health; " +
               "echo PRUEBA_OK; } > results/prueba_tarea.log 2>&1"
} else {
    $comando = "CAMPANA_BLOQUES='$Bloques' ./scripts/run_campana.sh >> results/campana.log 2>&1"
}

# Git Bash acepta rutas de Windows con barras normales.
$raizBash = $raiz -replace '\\', '/'
& $bash -lc "cd '$raizBash' && $comando"
exit $LASTEXITCODE
