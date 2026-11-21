# Solventa — Cliente Móvil

Autoservicio en movilidad para el cliente asegurado: cotización embebida, aviso de siniestro con cámara/geoetiquetado, pólizas y billetera de depósitos recibidos, notificaciones, autenticación biométrica.

**Stack:** Android Kotlin + Jetpack Compose (Clean Architecture + MVVM + Repository)
**Pruebas:** JUnit E2E (Compose UI Test), JUnit unitarias por capa, recursos por locale (i18n)

## E2E local (instrumentadas)

Desde este workspace:

```bash
cd Solventa
./scripts/run-connected-android-tests.sh
```

El script espera `sys.boot_completed` aunque `adb` ya liste un dispositivo. Si no hay ninguno, arranca el primer AVD. En macOS el emulador abre ventana con la GPU del host; en Linux puede ir sin ventana. Si el proceso muere o el procesador no es compatible, el script termina sin agotar la espera. En GitHub Actions el workflow ya deja el emulador listo y este script no arranca otro.

## Mapa de prestadores

La clave de Google Maps se toma de `-PmapsApiKey=…` o de `maps.apiKey` en `apps/mobile/Solventa/local.properties`, que no se versiona. Sin clave la pantalla muestra solo la lista de prestadores.

Los pines se agrupan con `com.google.maps.android:maps-compose-utils` (trae `android-maps-utils`). `ZoomCappedAlgorithm` agrupa por distancia en pantalla (60 dp) y desde zoom 14 deja cada pin suelto; los prestadores a menos de 10 m comparten un pin y abren una tarjeta con todos. Los pines y grupos se dibujan en `ProviderClusterRenderer`, que también les pone la descripción para TalkBack.

Para probar la ubicación en un emulador, abre *Extended controls → Location* y fija un punto, o desde la terminal:

```bash
adb emu geo fix -74.0631 4.6432
```

`geo fix` recibe longitud antes que latitud; ese punto cae en Chapinero, Bogotá. Para ver el modo ciudad, deniega el permiso de ubicación: el mapa abre en la primera ciudad del país de la región elegida en Perfil.

## Push (FCM)

`apps/mobile/Solventa/app/google-services.json` no se versiona. Sin ese archivo el plugin de Google Services no se aplica y `FirebasePushToken` no se usa, así que `./gradlew :app:testDebugUnitTest` corre en CI.

Para un APK que reciba push, coloca el JSON del proyecto Firebase de `com.grupo8_uniandes.solventa` en esa ruta y arma `./gradlew :app:assembleRemote`. En GitHub Actions el workflow `mobile-apk` lo escribe desde el secreto `GOOGLE_SERVICES_JSON` cuando el secreto está definido.

El identificador que se guarda es el Firebase Installation ID. `FirebaseMessaging.register()` lo vincula con FCM y el servicio lo reenvía en `onRegistered`. El cierre de sesión lee el FID con `FirebaseInstallations` y lo desactiva, sin pedir un token de registro.

Prueba local sin Firebase: los tests de `push/`, `bff/PushTest` y `shell/MainActivityPushIntentTest` cubren el permiso, el alta del identificador y el toque de la notificación. Con un dispositivo y el JSON presente, al abrir la sesión (registro o ingreso) la app publica el FID en `notificaciones.dispositivo_push` aunque el permiso de notificaciones siga pendiente. En API 33 o superior ese permiso se pide al terminar el registro y al ingresar, para que el aviso pueda mostrarse en la bandeja.
