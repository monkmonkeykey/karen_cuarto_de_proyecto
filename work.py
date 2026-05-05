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

MATRIX_LEDS = WIDTH * HEIGHT
MATRIX_COUNT = 2
LED_COUNT = MATRIX_LEDS * MATRIX_COUNT

LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 5
LED_INVERT = False
LED_CHANNEL = 0

# Conexión en cadena:
# Matriz 0: dinero verde
# Matriz 1: reloj rojo
MONEY_MATRIX = 0
CLOCK_MATRIX = 1

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

COLOR_CLOCK = Color(150, 0, 0)
COLOR_COLON = Color(255, 0, 0)
COLOR_MONEY = Color(0, 150, 0)
COLOR_OFF = Color(0, 0, 0)

# -----------------------------
# INICIALIZAR TIRA ÚNICA
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
# MAPEO XY A ÍNDICE LOCAL
# -----------------------------

def xy_to_local_index(x, y):
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


def matrix_xy_to_index(matrix_id, x, y):
    local_index = xy_to_local_index(x, y)

    if local_index is None:
        return None

    return matrix_id * MATRIX_LEDS + local_index

# -----------------------------
# FUENTE 4x7
# -----------------------------

FONT = {
    "0": [
        "1111",
        "1001",
        "1001",
        "1001",
        "1001",
        "1001",
        "1111"
    ],
    "1": [
        "0010",
        "0110",
        "0010",
        "0010",
        "0010",
        "0010",
        "1111"
    ],
    "2": [
        "1111",
        "0001",
        "0001",
        "1111",
        "1000",
        "1000",
        "1111"
    ],
    "3": [
        "1111",
        "0001",
        "0001",
        "1111",
        "0001",
        "0001",
        "1111"
    ],
    "4": [
        "1001",
        "1001",
        "1001",
        "1111",
        "0001",
        "0001",
        "0001"
    ],
    "5": [
        "1111",
        "1000",
        "1000",
        "1111",
        "0001",
        "0001",
        "1111"
    ],
    "6": [
        "1111",
        "1000",
        "1000",
        "1111",
        "1001",
        "1001",
        "1111"
    ],
    "7": [
        "1111",
        "0001",
        "0001",
        "0010",
        "0010",
        "0100",
        "0100"
    ],
    "8": [
        "1111",
        "1001",
        "1001",
        "1111",
        "1001",
        "1001",
        "1111"
    ],
    "9": [
        "1111",
        "1001",
        "1001",
        "1111",
        "0001",
        "0001",
        "1111"
    ],
    ":": [
        "0",
        "1",
        "0",
        "0",
        "0",
        "1",
        "0"
    ],
    ".": [
        "0",
        "0",
        "0",
        "0",
        "0",
        "1",
        "1"
    ],
    "$": [
        "1111",
        "1010",
        "1010",
        "1110",
        "0101",
        "0101",
        "1111"
    ]
}

# -----------------------------
# FUNCIONES DE DIBUJO
# -----------------------------

def clear_all():
    for i in range(LED_COUNT):
        strip.setPixelColor(i, COLOR_OFF)


def clear_matrix(matrix_id):
    start = matrix_id * MATRIX_LEDS
    end = start + MATRIX_LEDS

    for i in range(start, end):
        strip.setPixelColor(i, COLOR_OFF)


def set_pixel(matrix_id, x, y, color):
    index = matrix_xy_to_index(matrix_id, x, y)

    if index is not None:
        strip.setPixelColor(index, color)


def draw_char(matrix_id, char, x_offset, y_offset, color):
    bitmap = FONT.get(char)

    if bitmap is None:
        return 0

    for y, row in enumerate(bitmap):
        for x, value in enumerate(row):
            if value == "1":
                set_pixel(matrix_id, x_offset + x, y_offset + y, color)

    return len(bitmap[0])


def get_text_width(text, spacing=0):
    total = 0

    visible_chars = [char for char in text if char in FONT]

    for i, char in enumerate(visible_chars):
        bitmap = FONT.get(char)
        total += len(bitmap[0])

        if i < len(visible_chars) - 1:
            total += spacing

    return total


def draw_text(matrix_id, text, x, y, color, spacing=0):
    cursor_x = x

    for i, char in enumerate(text):
        char_width = draw_char(matrix_id, char, cursor_x, y, color)
        cursor_x += char_width

        if i < len(text) - 1:
            cursor_x += spacing

# -----------------------------
# DIBUJO DEL RELOJ
#
# Fuente 4x7.
# Formato visual:
# HH : MM : SS
#
# Distribución:
# HH = 8 px
# espacio = 1 px
# : = 1 px
# espacio = 1 px
# MM = 8 px
# espacio = 1 px
# : = 1 px
# espacio = 1 px
# SS = 8 px
# Total = 29 px
# Margen izquierdo = 1 px
# -----------------------------

def draw_time():
    now = datetime.now()
    hh = now.strftime("%H")
    mm = now.strftime("%M")
    ss = now.strftime("%S")

    colon_on = int(time.time()) % 2 == 0

    clear_matrix(CLOCK_MATRIX)

    y = 1
    x = 1

    # HH
    draw_text(CLOCK_MATRIX, hh, x, y, COLOR_CLOCK, spacing=0)
    x += 8

    # espacio, :, espacio
    x += 1
    if colon_on:
        draw_char(CLOCK_MATRIX, ":", x, y, COLOR_COLON)
    x += 1
    x += 1

    # MM
    draw_text(CLOCK_MATRIX, mm, x, y, COLOR_CLOCK, spacing=0)
    x += 8

    # espacio, :, espacio
    x += 1
    if colon_on:
        draw_char(CLOCK_MATRIX, ":", x, y, COLOR_COLON)
    x += 1
    x += 1

    # SS
    draw_text(CLOCK_MATRIX, ss, x, y, COLOR_CLOCK, spacing=0)

# -----------------------------
# DIBUJO DEL DINERO
#
# Incremento:
# 0.080 por segundo completo de actividad.
#
# Formatos:
# $ 0.080
# $ 1.280
# $12.800
# $99.920
# $100.00
# $999.92
# $1000.0
#
# Se intenta mostrar con separación después del $
# mientras el ancho lo permita.
# -----------------------------

def format_money_variable(money_thousandths):
    value = money_thousandths / 1000.0

    # Intenta primero con 3, luego 2, luego 1 decimal.
    for decimals in [3, 2, 1]:
        text = f"${value:.{decimals}f}"

        # Preferimos espacio después de $ si cabe.
        text_with_space = "$" + text[1:]

        if get_text_width(text_with_space, spacing=0) <= WIDTH:
            return text_with_space

    # Si aun así no cabe, usa 1 decimal y recorta desde la izquierda,
    # conservando siempre el símbolo $.
    text = f"${value:.1f}"

    while get_text_width(text, spacing=0) > WIDTH and len(text) > 1:
        if text.startswith("$"):
            text = "$" + text[2:]
        else:
            text = text[1:]

    return text


def draw_money(money_thousandths):
    clear_matrix(MONEY_MATRIX)

    text = format_money_variable(money_thousandths)

    y = 1
    x = 0

    # Si cabe con 1 px de separación entre todos los caracteres, úsalo.
    # Esto mejora mucho la lectura en valores cortos.
    if get_text_width(text, spacing=1) <= WIDTH:
        spacing = 1
    else:
        spacing = 0

    draw_text(MONEY_MATRIX, text, x, y, COLOR_MONEY, spacing=spacing)

# -----------------------------
# CONTROL DE TECLADO / DINERO
# -----------------------------

# Dinero guardado en milésimas:
# 80 = 0.080
# 160 = 0.160
# 1000 = 1.000
money_thousandths = 0

# Cada segundo completo de actividad suma 0.080
THOUSANDTHS_PER_SECOND = 80

# Acumula tiempo activo de teclado.
# Solo cuando llega a 1 segundo suma 0.080.
typing_time_accumulator = 0.0

pressed_keys = set()

last_keyboard_activity = None

# Ventana para considerar continuidad entre una tecla y otra.
# Si escribes rápido, pequeñas pausas todavía cuentan.
KEYBOARD_ACTIVITY_WINDOW = 0.25


def on_key_event(event):
    global last_keyboard_activity

    now = time.monotonic()

    if event.event_type == keyboard.KEY_DOWN:
        pressed_keys.add(event.scan_code)
        last_keyboard_activity = now

    elif event.event_type == keyboard.KEY_UP:
        pressed_keys.discard(event.scan_code)
        last_keyboard_activity = now


keyboard.hook(on_key_event)


def keyboard_is_active():
    now = time.monotonic()

    if len(pressed_keys) > 0:
        return True

    if last_keyboard_activity is not None:
        if now - last_keyboard_activity <= KEYBOARD_ACTIVITY_WINDOW:
            return True

    return False

# -----------------------------
# LOOP PRINCIPAL
# -----------------------------

last_time = time.monotonic()

try:
    while True:
        current_time = time.monotonic()
        delta_time = current_time - last_time
        last_time = current_time

        if keyboard_is_active():
            typing_time_accumulator += delta_time

            while typing_time_accumulator >= 1.0:
                money_thousandths += THOUSANDTHS_PER_SECOND
                typing_time_accumulator -= 1.0
        else:
            typing_time_accumulator = 0.0

        draw_money(money_thousandths)
        draw_time()

        strip.show()

        time.sleep(0.01)

except KeyboardInterrupt:
    clear_all()
    strip.show()