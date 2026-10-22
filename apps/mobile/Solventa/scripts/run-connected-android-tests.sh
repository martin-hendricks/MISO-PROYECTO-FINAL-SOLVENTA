#!/usr/bin/env bash

set -euo pipefail

# Connected Android tests.
# The suite starts only after adb reports state "device" and
# sys.boot_completed=1. offline and unauthorized are not ready.
# GitHub Actions already starts the emulator, so this script does not
# start a second one there. A local macOS boot keeps a window and the
# host GPU. If that process dies, or the log says the CPU is incompatible,
# the script exits instead of waiting out the boot cap.

ROOT_DIR="$(CDPATH="" cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

emulator_pid=""
EMULATOR_LOG="/tmp/solventa-emulator.log"

is_device_ready() {
  adb devices | awk 'NR>1 && $2 == "device" { found = 1 } END { exit !found }'
}

emulator_failed() {
  [ -n "$emulator_pid" ] || return 1
  if ! kill -0 "$emulator_pid" >/dev/null 2>&1; then
    return 0
  fi
  if [ -f "$EMULATOR_LOG" ] && grep -qi "Incompatible processor" "$EMULATOR_LOG"; then
    return 0
  fi
  return 1
}

disable_animations() {
  adb shell settings put global window_animation_scale 0 >/dev/null 2>&1 || true
  adb shell settings put global transition_animation_scale 0 >/dev/null 2>&1 || true
  adb shell settings put global animator_duration_scale 0 >/dev/null 2>&1 || true
}

wait_for_boot() {
  local max_seconds="${1:-360}"
  local elapsed=0
  while [ "$elapsed" -lt "$max_seconds" ]; do
    if emulator_failed; then
      return 1
    fi
    if is_device_ready; then
      if adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r' | grep -qx "1"; then
        disable_animations
        return 0
      fi
    fi
    sleep 2
    elapsed=$((elapsed + 2))
  done
  return 1
}

report_emulator_boot_error() {
  echo "El emulador no alcanzó sys.boot_completed=1."
  if [ -f "$EMULATOR_LOG" ] && grep -qi "Incompatible processor" "$EMULATOR_LOG"; then
    echo "El AVD seleccionado no es compatible con esta CPU. Crea un AVD compatible con $(uname -m) y vuelve a correr el script."
  fi
  if [ -f "$EMULATOR_LOG" ]; then
    echo "Revisa $EMULATOR_LOG"
    tail -n 40 "$EMULATOR_LOG" || true
  fi
}

clear_stale_emulator() {
  local running_dir="${HOME}/Library/Caches/TemporaryItems/avd/running"
  local ini pid
  [ -d "$running_dir" ] || return 0
  for ini in "$running_dir"/pid_*.ini; do
    [ -f "$ini" ] || continue
    pid="$(basename "$ini")"
    pid="${pid#pid_}"
    pid="${pid%.ini}"
    if ! kill -0 "$pid" >/dev/null 2>&1; then
      echo "El emulador $pid ya no corre. Quito su anuncio para que adb pueda ver el siguiente arranque."
      rm -rf "$running_dir/$pid" "$ini"
    fi
  done
}

start_local_avd() {
  local avd="$1"
  local common_flags
  common_flags="-memory 4096 -partition-size 8192 -no-snapshot-load -no-snapshot-save -no-boot-anim -no-audio"

  clear_stale_emulator
  echo "Iniciando AVD: $avd"
  # API 36 on Apple Silicon needs a window and the host GPU. Headless
  # swiftshader exits before adb sees a device. The emulator is started in
  # its own session so closing this script does not take adb's device with it.
  # Extra RAM and a larger data partition keep Play services from filling /data.
  if [ "$(uname -s)" = "Darwin" ]; then
    gpu_flags=(-gpu host)
  else
    gpu_flags=(-no-window -gpu swiftshader_indirect)
  fi
  EMULATOR_LOG="$EMULATOR_LOG" \
    EMULATOR_ARGS="$avd $common_flags ${gpu_flags[*]}" \
    python3 -c 'import os, shlex, subprocess
log = open(os.environ["EMULATOR_LOG"], "w")
args = ["emulator", *shlex.split(os.environ["EMULATOR_ARGS"])]
proc = subprocess.Popen(args, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
open("/tmp/solventa-emu.pid", "w").write(str(proc.pid))'
  emulator_pid="$(tr -d '[:space:]' < /tmp/solventa-emu.pid)"
}

adb start-server >/dev/null 2>&1 || true

if [ "${GITHUB_ACTIONS:-}" = "true" ]; then
  echo "Esperando el emulador de GitHub Actions..."
  if ! wait_for_boot 240; then
    echo "GitHub Actions no dejó un emulador en estado device."
    adb devices -l || true
    report_emulator_boot_error
    exit 1
  fi
elif ! is_device_ready; then
  avd="$(emulator -list-avds | head -n 1 || true)"
  if [ -z "$avd" ]; then
    echo "No hay un dispositivo conectado ni AVDs disponibles para correr connectedDebugAndroidTest."
    exit 1
  fi

  start_local_avd "$avd"
  if ! wait_for_boot 360; then
    report_emulator_boot_error
    exit 1
  fi
elif ! wait_for_boot 360; then
  report_emulator_boot_error
  exit 1
fi

adb devices -l
./gradlew :app:connectedDebugAndroidTest --console=plain
