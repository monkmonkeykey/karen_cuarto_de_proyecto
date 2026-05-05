#!/usr/bin/env python3

import time
from datetime import datetime
from rpi_ws281x import PixelStrip, Color
import keyboard

# -----------------------------
# CONFIGURACIÓN GENERAL
# -----------------------------

WIDTH = 32
HEIGHT = 8
LED_COUNT = WIDTH * HEIGHT

# Matriz 1: reloj rojo
LED_PIN_CLOCK = 18
LED_CHANNEL_CLOCK = 0

# Matriz 2: dinero verde
LED_PIN_MONEY = 13
LED_CHANNEL_MONEY = 1

LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 5
LED_INVERT = False

# -----------------------------
# CONFIGURACIÓN DE MAPEO
# -----------------------------

SERPENTINE = True
WIRING_MODE = "vertical"   # "horizontal" o "vertical"

MIRROR_X = True
MIRROR_Y = True

# -----------------------------
# COLORES
# -----------------------------

COLOR_NUM = Color(150, 0, 0)       # rojo reloj
COLOR_COLON = Color(255, 0, 0)     # rojo dos puntos
COLOR_MONEY = Color(0, 150, 0)     # verde dinero
COLOR_OFF = Color(0, 0, 0)

# -----------------------------
# INICIALIZAR MATRICES
# -----------------------------

clock_strip = PixelStrip(
    LED_COUNT,
    LED_PIN_CLOCK,
    LED_FREQ_HZ,
    LED_DMA,
    LED_INVERT,
    LED_BRIGHTNESS,
    LED_CHANNEL_CLOCK
)

money_strip = PixelStrip(
    LED_COUNT,
    LED_PIN_MONEY,
    LED_FREQ_HZ,
    LED_DMA,
    LED_INVERT,
    LED_BRIGHTNESS,
    LED_CHANNEL_MONEY
)

clock_strip.begin()
money_strip.begin()

# -----------------------------
# MAPEO XY A ÍNDICE LED
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
        "0",
        "1",
        "0",
        "0",
        "1",
        "0",
        "0"
    ],
    ".": [
        "0",
        "0",
        "0",
        "0",
        "0",
        "0",
        "1",
        "0"
    ]
}

# -----------------------------
# FUNCIONES DE DIBUJO
# -----------------------------

def clear(strip):
    for i in range(LED_COUNT):
        strip.setPixelColor(i, COLOR_OFF)


def set_pixel(strip, x, y, color):
    index = xy_to_index(x, y)

    if index is not None:
        strip.setPixelColor(index, color)


def draw_char(strip, char, x_offset, y_offset, color):
    bitmap = FONT.get(char)

    if bitmap is None:
        return 0

    for y, row in enumerate(bitmap):
        for x, value in enumerate(row):
            if value == "1":
                set_pixel(strip, x_offset + x, y_offset + y, color)

    return len(bitmap[0])


def get_text_width(text):
    total = 0

    for char in text:
        bitmap = FONT.get(char)
        if bitmap is not None:
            total += len(bitmap[0])

    return total


def draw_text(strip, text, color):
    x = 0
    y = 0

    for char in text:
        char_width = draw_char(strip, char, x, y, color)
        x += char_width


def draw_time(text):
    x = 0
    y = 0

    colon_on = int(time.time()) % 2 == 0

    for char in text:
        if char == ":":
            if colon_on:
                draw_char(clock_strip, char, x, y, COLOR_COLON)

            x += 1

        else:
            draw_char(clock_strip, char, x, y, COLOR_NUM)
            x += 5


def draw_money(value):
    text = f"{value:.1f}"

    # Si el número ya no cabe en 32 px, se recortan los caracteres iniciales.
    # Ejemplo: 123456.7 podría terminar mostrándose como 3456.7
    while get_text_width(text) > WIDTH:
        text = text[1:]

    clear(money_strip)
    draw_text(money_strip, text, COLOR_MONEY)
    money_strip.show()

# -----------------------------
# CONTROL DE TECLADO / DINERO
# -----------------------------

money_value = 0.0
rate_per_second = 0.8

pressed_keys = set()

def on_key_down(event):
    pressed_keys.add(event.name)


def on_key_up(event):
    pressed_keys.discard(event.name)


keyboard.on_press(on_key_down)
keyboard.on_release(on_key_up)

# -----------------------------
# LOOP PRINCIPAL
# -----------------------------

last_time = time.time()

try:
    while True:
        current_time = time.time()
        delta_time = current_time - last_time
        last_time = current_time

        # Si hay cualquier tecla presionada, aumenta 0.8 por segundo.
        # Si hay varias teclas presionadas, NO aumenta más rápido.
        if len(pressed_keys) > 0:
            money_value += rate_per_second * delta_time

        now = datetime.now()
        hora = now.strftime("%H:%M:%S")

        clear(clock_strip)
        draw_time(hora)
        clock_strip.show()

        draw_money(money_value)

        time.sleep(0.02)

except KeyboardInterrupt:
    clear(clock_strip)
    clear(money_strip)
    clock_strip.show()
    money_strip.show()