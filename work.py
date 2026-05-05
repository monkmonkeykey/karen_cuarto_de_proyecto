#!/usr/bin/env python3

import time
from datetime import datetime
from rpi_ws281x import PixelStrip, Color

# -----------------------------
# CONFIGURACIÃN GENERAL
# -----------------------------

WIDTH = 32
HEIGHT = 8
LED_COUNT = WIDTH * HEIGHT

LED_PIN = 18          # GPIO18 / D18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 5   # 0 - 255
LED_INVERT = False
LED_CHANNEL = 0

# -----------------------------
# CONFIGURACIÃN DE MAPEO
# -----------------------------
# Para una matriz WS2812B 32x8 comÃºn en serpentina horizontal.
# Si se ve mal, cambia estos valores.

SERPENTINE = True
WIRING_MODE = "vertical"   # "horizontal" o "vertical"

MIRROR_X = True
MIRROR_Y = True

# -----------------------------
# COLORES
# -----------------------------

COLOR_NUM = Color(150, 0, 0)       # rojo
COLOR_COLON = Color(255, 0, 0)  # rojo bajo
COLOR_OFF = Color(0, 0, 0)

# -----------------------------
# INICIALIZAR MATRIZ
# -----------------------------

strip = PixelStrip(
    LED_COUNT,
    LED_PIN,
    LED_FREQ_HZ,
    LED_DMA,
    LED_INVERT,
    LED_BRIGHTNESS,
    LED_CHANNEL
)

strip.begin()

# -----------------------------
# MAPEO XY A ÃNDICE LED
# -----------------------------

def xy_to_index(x, y):
    if x < 0 or x >= WIDTH or y < 0 or y >= HEIGHT:
        return None

    if MIRROR_X:
        x = WIDTH - 1 - x

    if MIRROR_Y:
        y = HEIGHT - 1 - y

    if WIRING_MODE == "horizontal":
        if SERPENTINE:
            if y % 2 == 0:
                return y * WIDTH + x
            else:
                return y * WIDTH + (WIDTH - 1 - x)
        else:
            return y * WIDTH + x

    elif WIRING_MODE == "vertical":
        if SERPENTINE:
            if x % 2 == 0:
                return x * HEIGHT + y
            else:
                return x * HEIGHT + (HEIGHT - 1 - y)
        else:
            return x * HEIGHT + y

    return y * WIDTH + x

# -----------------------------
# FUENTE 5x8
# -----------------------------

FONT = {
    "0": [
        "01110",
        "10001",
        "10011",
        "10101",
        "11001",
        "10001",
        "10001",
        "01110"
    ],
    "1": [
        "00100",
        "01100",
        "10100",
        "00100",
        "00100",
        "00100",
        "00100",
        "11111"
    ],
    "2": [
        "01110",
        "10001",
        "00001",
        "00010",
        "00100",
        "01000",
        "10000",
        "11111"
    ],
    "3": [
        "11110",
        "00001",
        "00001",
        "01110",
        "00001",
        "00001",
        "10001",
        "01110"
    ],
    "4": [
        "00010",
        "00110",
        "01010",
        "10010",
        "11111",
        "00010",
        "00010",
        "00010"
    ],
    "5": [
        "11111",
        "10000",
        "10000",
        "11110",
        "00001",
        "00001",
        "10001",
        "01110"
    ],
    "6": [
        "00110",
        "01000",
        "10000",
        "11110",
        "10001",
        "10001",
        "10001",
        "01110"
    ],
    "7": [
        "11111",
        "00001",
        "00010",
        "00100",
        "00100",
        "01000",
        "01000",
        "01000"
    ],
    "8": [
        "01110",
        "10001",
        "10001",
        "01110",
        "10001",
        "10001",
        "10001",
        "01110"
    ],
    "9": [
        "01110",
        "10001",
        "10001",
        "10001",
        "01111",
        "00001",
        "00010",
        "11100"
    ],
    ":": [
        "0",
        "1",
        "1",
        "0",
        "0",
        "1",
        "1",
        "0"
    ]
}

# -----------------------------
# FUNCIONES DE DIBUJO
# -----------------------------

def clear():
    for i in range(LED_COUNT):
        strip.setPixelColor(i, COLOR_OFF)


def set_pixel(x, y, color):
    index = xy_to_index(x, y)

    if index is not None:
        strip.setPixelColor(index, color)


def draw_char(char, x_offset, y_offset, color):
    bitmap = FONT.get(char)

    if bitmap is None:
        return 0

    for y, row in enumerate(bitmap):
        for x, value in enumerate(row):
            if value == "1":
                set_pixel(x_offset + x, y_offset + y, color)

    return len(bitmap[0])


def draw_time(text):
    x = 0
    y = 0

    colon_on = int(time.time()) % 2 == 0

    for char in text:
        if char == ":":
            if colon_on:
                draw_char(char, x, y, COLOR_COLON)

            x += 1

        else:
            draw_char(char, x, y, COLOR_NUM)
            x += 5

# -----------------------------
# LOOP PRINCIPAL
# -----------------------------

try:
    while True:
        now = datetime.now()
        hora = now.strftime("%H:%M:%S")

        clear()
        draw_time(hora)
        strip.show()

        #time.sleep(0.1)

except KeyboardInterrupt:
    clear()
    strip.show()

