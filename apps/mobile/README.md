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

## Push (FCM)

`apps/mobile/Solventa/app/google-services.json` no se versiona. Sin ese archivo el plugin de Google Services no se aplica y `FirebasePushToken` no se usa, así que `./gradlew :app:testDebugUnitTest` corre en CI.

Para un APK que reciba push, coloca el JSON del proyecto Firebase de `com.grupo8_uniandes.solventa` en esa ruta y arma `./gradlew :app:assembleRemote`. En GitHub Actions el workflow `mobile-apk` lo escribe desde el secreto `GOOGLE_SERVICES_JSON` cuando el secreto está definido.

El identificador que se guarda es el Firebase Installation ID. `FirebaseMessaging.register()` lo vincula con FCM y el servicio lo reenvía en `onRegistered`. El cierre de sesión lee el FID con `FirebaseInstallations` y lo desactiva, sin pedir un token de registro.

Prueba local sin Firebase: los tests de `push/`, `bff/PushTest` y `shell/MainActivityPushIntentTest` cubren el permiso, el alta del identificador y el toque de la notificación. Con un dispositivo y el JSON presente, inicia sesión en API 33 o superior, acepta el permiso y confirma una fila activa en `notificaciones.dispositivo_push`.
