#!/usr/bin/env python3

import time
import sys
from evdev import InputDevice, ecodes, list_devices

EXPECTED_KEYBOARD_NAME = "Logi K250 Keyboard"
KEYBOARD_PATH_FILE = "/tmp/karen_keyboard_path"

TIMEOUT_SECONDS = 300
CHECK_INTERVAL = 2


def device_is_keyboard(device):
    try:
        capabilities = device.capabilities()

        if ecodes.EV_KEY not in capabilities:
            return False

        key_codes = capabilities[ecodes.EV_KEY]

        return (
            ecodes.KEY_A in key_codes
            or ecodes.KEY_SPACE in key_codes
            or ecodes.KEY_ENTER in key_codes
        )

    except Exception:
        return False


def find_keyboard():
    for path in list_devices():
        try:
            device = InputDevice(path)

            if EXPECTED_KEYBOARD_NAME not in device.name:
                continue

            if not device_is_keyboard(device):
                continue

            return device

        except Exception:
            pass

    return None


start_time = time.monotonic()

while True:
    keyboard = find_keyboard()

    if keyboard is not None:
        print(f"Teclado listo: {keyboard.path}: {keyboard.name}")

        with open(KEYBOARD_PATH_FILE, "w") as f:
            f.write(keyboard.path)

        sys.exit(0)

    elapsed = time.monotonic() - start_time

    if elapsed >= TIMEOUT_SECONDS:
        print(f"ERROR: No se detectó el teclado esperado: {EXPECTED_KEYBOARD_NAME}")
        sys.exit(1)

    print(f"Esperando teclado inalámbrico: {EXPECTED_KEYBOARD_NAME}...")
    time.sleep(CHECK_INTERVAL)