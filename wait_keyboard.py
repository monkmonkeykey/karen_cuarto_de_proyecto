#!/usr/bin/env python3

import time
import sys
from evdev import InputDevice, ecodes, list_devices

TIMEOUT_SECONDS = 60
CHECK_INTERVAL = 2


def find_keyboard_devices():
    keyboards = []

    for path in list_devices():
        try:
            device = InputDevice(path)
            capabilities = device.capabilities()

            if ecodes.EV_KEY not in capabilities:
                continue

            key_codes = capabilities[ecodes.EV_KEY]

            # Filtro para detectar teclados reales.
            if (
                ecodes.KEY_A in key_codes
                or ecodes.KEY_SPACE in key_codes
                or ecodes.KEY_ENTER in key_codes
            ):
                keyboards.append(device)

        except Exception:
            pass

    return keyboards


start_time = time.monotonic()

while True:
    devices = find_keyboard_devices()

    if len(devices) > 0:
        print("Teclado detectado antes de iniciar:")
        for device in devices:
            print(f"- {device.path}: {device.name}")
        sys.exit(0)

    elapsed = time.monotonic() - start_time

    if elapsed >= TIMEOUT_SECONDS:
        print("ERROR: No se detectó teclado dentro del tiempo límite.")
        sys.exit(1)

    print("Esperando teclado...")
    time.sleep(CHECK_INTERVAL)