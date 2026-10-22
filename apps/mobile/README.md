# Solventa — Cliente Móvil

Autoservicio en movilidad para el cliente asegurado: cotización embebida, aviso de siniestro con cámara/geoetiquetado, billetera de pólizas, notificaciones, autenticación biométrica.

**Stack:** Android Kotlin + Jetpack Compose (Clean Architecture + MVVM + Repository)
**Pruebas:** JUnit E2E (Compose UI Test), JUnit unitarias por capa, recursos por locale (i18n)

## E2E local (instrumentadas)

Desde este workspace:

```bash
cd Solventa
./scripts/run-connected-android-tests.sh
```

El script espera `sys.boot_completed` aunque `adb` ya liste un dispositivo. Si no hay ninguno, arranca el primer AVD. En macOS el emulador abre ventana con la GPU del host; en Linux puede ir sin ventana. Si el proceso muere o el procesador no es compatible, el script termina sin agotar la espera. En GitHub Actions el workflow ya deja el emulador listo y este script no arranca otro.
