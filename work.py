#!/usr/bin/env python3

import time
import os
import threading
import json
from datetime import datetime, date
from rpi_ws281x import PixelStrip, Color
from evdev import InputDevice, categorize, ecodes

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
# GPIO18 -> DIN matriz 0
# DOUT matriz 0 -> DIN matriz 1
#
# Matriz 0: dinero verde
# Matriz 1: reloj rojo
MONEY_MATRIX = 0
CLOCK_MATRIX = 1

# -----------------------------
# TECLADO FIJO
# -----------------------------

KEYBOARD_PATH = "/dev/input/event5"
EXPECTED_KEYBOARD_NAME = "Logi K250 Keyboard"

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
    chars = [char for char in text if char in FONT]

    for i, char in enumerate(chars):
        total += len(FONT[char][0])

        if i < len(chars) - 1:
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
# -----------------------------

def draw_time():
    now = datetime.now()

    hh = now.strftime("%H")
    mm = now.strftime("%M")
    ss = now.strftime("%S")

    colon_on = int(time.time()) % 2 == 0

    clear_matrix(CLOCK_MATRIX)

    y = 0
    x = 0

    # Mostrar de forma más grande: HH:MM en primera fila, SS en segunda
    # HH
    draw_text(CLOCK_MATRIX, hh, x, y, COLOR_CLOCK, spacing=0)
    x += 9

    # :
    if colon_on:
        draw_char(CLOCK_MATRIX, ":", x, y, COLOR_COLON)
    x += 3

    # MM
    draw_text(CLOCK_MATRIX, mm, x, y, COLOR_CLOCK, spacing=0)

# -----------------------------
# DIBUJO DEL DINERO
# -----------------------------

def format_money_variable(money_thousandths):
    value = money_thousandths / 1000.0

    # Intenta mostrar 3 decimales, luego 2, luego 1.
    for decimals in [3, 2, 1]:
        text = f"${value:.{decimals}f}"

        if get_text_width(text, spacing=1) <= WIDTH:
            return text, 1

        if get_text_width(text, spacing=0) <= WIDTH:
            return text, 0

    # Si aun con 1 decimal no cabe, recorta desde la izquierda
    # conservando siempre el símbolo $.
    text = f"${value:.1f}"

    while get_text_width(text, spacing=0) > WIDTH and len(text) > 1:
        if text.startswith("$"):
            text = "$" + text[2:]
        else:
            text = text[1:]

    return text, 0


def draw_money(money_thousandths):
    clear_matrix(MONEY_MATRIX)

    text, spacing = format_money_variable(money_thousandths)

    y = 1
    x = 0

    draw_text(MONEY_MATRIX, text, x, y, COLOR_MONEY, spacing=spacing)

# -----------------------------
# CONTROL DE TECLADO / DINERO CON EVDEV
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

# Teclas físicamente presionadas
pressed_keys = set()

# Último momento en que hubo evento de teclado
last_keyboard_activity = None

# Ventana para considerar continuidad entre una tecla y otra.
KEYBOARD_ACTIVITY_WINDOW = 0.25

# Cada cuánto reintenta abrir el teclado si falla (más frecuente)
KEYBOARD_RESCAN_SECONDS = 0.5

# Para evitar conflictos entre el hilo del teclado y el loop principal
keyboard_lock = threading.Lock()


def open_fixed_keyboard():
    if not os.path.exists(KEYBOARD_PATH):
        print(f"No existe {KEYBOARD_PATH}")
        return None

    try:
        device = InputDevice(KEYBOARD_PATH)

        if EXPECTED_KEYBOARD_NAME not in device.name:
            print(f"El dispositivo en {KEYBOARD_PATH} no es el esperado: {device.name}")
            return None

        capabilities = device.capabilities()

        if ecodes.EV_KEY not in capabilities:
            print(f"El dispositivo {KEYBOARD_PATH} no reporta eventos EV_KEY.")
            return None

        key_codes = capabilities[ecodes.EV_KEY]

        if (
            ecodes.KEY_A not in key_codes
            and ecodes.KEY_SPACE not in key_codes
            and ecodes.KEY_ENTER not in key_codes
        ):
            print(f"El dispositivo {KEYBOARD_PATH} no parece ser un teclado completo.")
            return None

        print(f"Teclado seleccionado: {device.path}: {device.name}")
        return device

    except Exception as e:
        print(f"Error abriendo teclado fijo: {e}")
        return None


def keyboard_listener():
    global last_keyboard_activity

    retry_count = 0
    while True:
        device = open_fixed_keyboard()

        if device is None:
            retry_count += 1
            if retry_count % 5 == 0:  # Cada 5 reintentos (2.5 segundos)
                print(f"Reintentando conexión con teclado... (intento {retry_count})")
            time.sleep(KEYBOARD_RESCAN_SECONDS)
            continue

        # Conexión exitosa
        retry_count = 0
        print("✓ Teclado conectado exitosamente")

        try:
            for event in device.read_loop():
                if event.type != ecodes.EV_KEY:
                    continue

                key_event = categorize(event)
                now = time.monotonic()

                with keyboard_lock:
                    if key_event.keystate == key_event.key_down:
                        pressed_keys.add(key_event.scancode)
                        last_keyboard_activity = now

                    elif key_event.keystate == key_event.key_up:
                        pressed_keys.discard(key_event.scancode)
                        last_keyboard_activity = now

        except Exception as e:
            print(f"Error leyendo teclado: {e}")

        with keyboard_lock:
            pressed_keys.clear()

        time.sleep(KEYBOARD_RESCAN_SECONDS)


def keyboard_is_active():
    now = time.monotonic()

    with keyboard_lock:
        if len(pressed_keys) > 0:
            return True

        if last_keyboard_activity is not None:
            if now - last_keyboard_activity <= KEYBOARD_ACTIVITY_WINDOW:
                return True

    return False


keyboard_thread = threading.Thread(target=keyboard_listener, daemon=True)
keyboard_thread.start()

# -----------------------------
# GESTIÓN DE PERSISTENCIA
# -----------------------------

DATA_FILE = "dinero_datos.json"

def load_data():
    """Carga dinero del día actual y total acumulado"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                return data.get("dinero_hoy", 0), data.get("dinero_total", 0)
        except Exception as e:
            print(f"Error cargando datos: {e}")
            return 0, 0
    return 0, 0

def save_data(dinero_hoy, dinero_total):
    """Guarda dinero del día y total acumulado"""
    try:
        data = {
            "fecha": str(date.today()),
            "dinero_hoy": dinero_hoy,
            "dinero_total": dinero_total
        }
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error guardando datos: {e}")

def check_new_day(last_day, dinero_hoy, dinero_total):
    """Verifica si cambió el día y reinicia contador si es necesario"""
    today = date.today()
    if last_day != today:
        print(f"Nuevo día: {today}. Total acumulado: ${dinero_total / 1000.0:.3f}")
        dinero_total += dinero_hoy  # Suma el dinero del día anterior al total
        dinero_hoy = 0  # Reinicia el contador del día
        return today, dinero_hoy, dinero_total
    return last_day, dinero_hoy, dinero_total

# -----------------------------
# LOOP PRINCIPAL
# -----------------------------

# Carga dinero previo
money_thousandths, total_money_thousandths = load_data()
last_day = date.today()
last_time = time.monotonic()
last_save_time = time.monotonic()
SAVE_INTERVAL = 5  # Guardar cada 5 segundos

try:
    while True:
        current_time = time.monotonic()
        delta_time = current_time - last_time
        last_time = current_time

        # Verifica si cambió el día
        last_day, money_thousandths, total_money_thousandths = check_new_day(
            last_day, money_thousandths, total_money_thousandths
        )

        if keyboard_is_active():
            typing_time_accumulator += delta_time

            while typing_time_accumulator >= 1.0:
                money_thousandths += THOUSANDTHS_PER_SECOND
                typing_time_accumulator -= 1.0
        else:
            typing_time_accumulator = 0.0

        # Guarda datos cada cierto tiempo
        if current_time - last_save_time >= SAVE_INTERVAL:
            save_data(money_thousandths, total_money_thousandths)
            last_save_time = current_time

        draw_money(money_thousandths)
        draw_time()

        strip.show()

        time.sleep(0.01)

except KeyboardInterrupt:
    # Guarda datos finales antes de salir
    save_data(money_thousandths, total_money_thousandths)
    clear_all()
    strip.show()
    print(f"\nDinero hoy: ${money_thousandths / 1000.0:.3f}")
    print(f"Total acumulado: ${total_money_thousandths / 1000.0:.3f}")