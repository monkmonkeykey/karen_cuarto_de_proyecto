#!/usr/bin/env python3

import time
import sys
import os
from evdev import InputDevice, ecodes

KEYBOARD_PATH = "/dev/input/event5"
EXPECTED_NAME = "Microsoft Wedge Mobile Keyboard"

TIMEOUT_SECONDS = 120
CHECK_INTERVAL = 2


def keyboard_is_ready():
    if not os.path.exists(KEYBOARD_PATH):
        return False

    try:
        device = InputDevice(KEYBOARD_PATH)

        if EXPECTED_NAME not in device.name:
            print(f"Dispositivo encontrado, pero no es el esperado: {device.name}")
            return False

        capabilities = device.capabilities()

        if ecodes.EV_KEY not in capabilities:
            print("El dispositivo existe, pero no reporta teclas.")
            return False

        key_codes = capabilities[ecodes.EV_KEY]

        if ecodes.KEY_A not in key_codes and ecodes.KEY_SPACE not in key_codes:
            print("El dispositivo existe, pero no parece ser teclado completo.")
            return False

        print(f"Teclado listo: {KEYBOARD_PATH}: {device.name}")
        return True

    except Exception as e:
        print(f"Error revisando teclado: {e}")
        return False


start_time = time.monotonic()

while True:
    if keyboard_is_ready():
        sys.exit(0)

    elapsed = time.monotonic() - start_time

    if elapsed >= TIMEOUT_SECONDS:
        print(f"ERROR: No se detectó el teclado esperado en {KEYBOARD_PATH}")
        sys.exit(1)

    print(f"Esperando teclado en {KEYBOARD_PATH}...")
    time.sleep(CHECK_INTERVAL)