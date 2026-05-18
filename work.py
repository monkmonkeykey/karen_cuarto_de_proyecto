#!/usr/bin/env python3

import time
import os
import threading
import json
from datetime import datetime, date
from rpi_ws281x import PixelStrip, Color
from evdev import InputDevice, categorize, ecodes, list_devices

# -----------------------------
# CONFIGURACIÓN GENERAL
# -----------------------------

WIDTH = 32
HEIGHT = 8
LED_COUNT = WIDTH * HEIGHT  # 256 LEDs por matriz

# IMPORTANTE:
# GPIO13 debe usar channel 1.
# GPIO18 debe usar channel 0.

# Matriz dinero / verde
MONEY_LED_PIN = 18          # GPIO18 / pin físico 33
MONEY_LED_CHANNEL = 1

# Matriz reloj / roja
CLOCK_LED_PIN = 13          # GPIO13 / pin físico 12
CLOCK_LED_CHANNEL = 0

LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 10
LED_INVERT = False

# -----------------------------
# TECLADO INALÁMBRICO
# -----------------------------

EXPECTED_KEYBOARD_NAME = "Logi K250 Keyboard"
KEYBOARD_PATH_FILE = "/tmp/karen_keyboard_path"
DEFAULT_KEYBOARD_PATH = "/dev/input/event5"
KEYBOARD_RESCAN_SECONDS = 1.0

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
# INICIALIZAR MATRICES INDEPENDIENTES
# -----------------------------

# Se usan argumentos nombrados para evitar errores de orden.
money_strip = PixelStrip(
    num=LED_COUNT,
    pin=MONEY_LED_PIN,
    freq_hz=LED_FREQ_HZ,
    dma=LED_DMA,
    invert=LED_INVERT,
    brightness=LED_BRIGHTNESS,
    channel=MONEY_LED_CHANNEL
)

clock_strip = PixelStrip(
    num=LED_COUNT,
    pin=CLOCK_LED_PIN,
    freq_hz=LED_FREQ_HZ,
    dma=LED_DMA,
    invert=LED_INVERT,
    brightness=LED_BRIGHTNESS,
    channel=CLOCK_LED_CHANNEL
)

money_strip.begin()
clock_strip.begin()

# -----------------------------
# MAPEO XY A ÍNDICE LOCAL
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

def clear_strip(strip):
    for i in range(LED_COUNT):
        strip.setPixelColor(i, COLOR_OFF)


def clear_all():
    clear_strip(money_strip)
    clear_strip(clock_strip)


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


def get_text_width(text, spacing=0):
    total = 0
    chars = [char for char in text if char in FONT]

    for i, char in enumerate(chars):
        total += len(FONT[char][0])

        if i < len(chars) - 1:
            total += spacing

    return total


def draw_text(strip, text, x, y, color, spacing=0):
    cursor_x = x

    for i, char in enumerate(text):
        char_width = draw_char(strip, char, cursor_x, y, color)
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

    clear_strip(clock_strip)

    # Una sola fila: HH:MM:SS
    y = 1
    x = 1

    # HH
    x += draw_char(clock_strip, hh[0], x, y, COLOR_CLOCK)
    x += draw_char(clock_strip, hh[1], x, y, COLOR_CLOCK)
    x += 1

    # :
    if colon_on:
        x += draw_char(clock_strip, ":", x, y, COLOR_COLON)
    else:
        x += 1
    x += 1

    # MM
    x += draw_char(clock_strip, mm[0], x, y, COLOR_CLOCK)
    x += draw_char(clock_strip, mm[1], x, y, COLOR_CLOCK)
    x += 1

    # :
    if colon_on:
        x += draw_char(clock_strip, ":", x, y, COLOR_COLON)
    else:
        x += 1
    x += 1

    # SS
    x += draw_char(clock_strip, ss[0], x, y, COLOR_CLOCK)
    x += draw_char(clock_strip, ss[1], x, y, COLOR_CLOCK)

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


def get_animated_money_value(current_time, animation_start_time, start_value, end_value):
    """
    Interpola el valor del dinero durante la animación tipo odómetro.
    """
    ANIMATION_DURATION = 0.8

    elapsed = current_time - animation_start_time

    if elapsed >= ANIMATION_DURATION:
        return end_value

    progress = elapsed / ANIMATION_DURATION
    easing = 1 - ((1 - progress) ** 3)

    current_value = int(start_value + (end_value - start_value) * easing)

    return current_value


def get_money_color_animated(current_time, last_update_time):
    """
    Retorna un color animado para el dinero con efecto de destello.
    """
    elapsed = current_time - last_update_time
    ANIMATION_DURATION = 0.8

    if elapsed > ANIMATION_DURATION:
        return COLOR_MONEY

    progress = elapsed / ANIMATION_DURATION
    easing = 1 - (progress ** 2)

    brightness_boost = int(105 * easing)

    return Color(0, 150 + brightness_boost, 0)


def draw_money(money_thousandths, current_time=None):
    if current_time is None:
        current_time = time.monotonic()

    clear_strip(money_strip)

    display_value = get_animated_money_value(
        current_time,
        animation_state["start_time"],
        animation_state["start"],
        money_thousandths
    )

    text, spacing = format_money_variable(display_value)
    money_color = get_money_color_animated(current_time, last_money_update_time)

    y = 1
    x = 0

    draw_text(money_strip, text, x, y, money_color, spacing=spacing)

# -----------------------------
# CONTROL DE TECLADO / DINERO CON EVDEV
# -----------------------------

money_thousandths = 0
last_money_update_time = time.monotonic()

animation_state = {
    "start": 0,
    "start_time": time.monotonic()
}

# Cada segundo completo de actividad suma 0.080
THOUSANDTHS_PER_SECOND = 80

typing_time_accumulator = 0.0

pressed_keys = set()
last_keyboard_activity = None

KEYBOARD_ACTIVITY_WINDOW = 0.25

keyboard_lock = threading.Lock()


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


def keyboard_name_matches(device):
    return EXPECTED_KEYBOARD_NAME in device.name


def open_keyboard_from_path(path):
    try:
        if not os.path.exists(path):
            return None

        device = InputDevice(path)

        if not keyboard_name_matches(device):
            print(f"Dispositivo en {path} no coincide: {device.name}")
            return None

        if not device_is_keyboard(device):
            print(f"Dispositivo en {path} no parece teclado completo: {device.name}")
            return None

        return device

    except Exception as e:
        print(f"No se pudo abrir {path}: {e}")
        return None


def find_keyboard_by_name():
    for path in list_devices():
        try:
            device = InputDevice(path)

            if not keyboard_name_matches(device):
                continue

            if not device_is_keyboard(device):
                continue

            return device

        except Exception:
            pass

    return None


def save_keyboard_path(path):
    try:
        with open(KEYBOARD_PATH_FILE, "w") as f:
            f.write(path)
    except Exception as e:
        print(f"No se pudo guardar ruta del teclado: {e}")


def read_saved_keyboard_path():
    try:
        if not os.path.exists(KEYBOARD_PATH_FILE):
            return None

        with open(KEYBOARD_PATH_FILE, "r") as f:
            path = f.read().strip()

        if path:
            return path

    except Exception:
        pass

    return None


def open_keyboard():
    saved_path = read_saved_keyboard_path()

    if saved_path:
        device = open_keyboard_from_path(saved_path)
        if device is not None:
            print(f"Teclado seleccionado desde archivo: {device.path}: {device.name}")
            return device

    device = open_keyboard_from_path(DEFAULT_KEYBOARD_PATH)

    if device is not None:
        print(f"Teclado seleccionado desde ruta inicial: {device.path}: {device.name}")
        save_keyboard_path(device.path)
        return device

    device = find_keyboard_by_name()

    if device is not None:
        print(f"Teclado encontrado por nombre: {device.path}: {device.name}")
        save_keyboard_path(device.path)
        return device

    print(f"No se encontró teclado con nombre: {EXPECTED_KEYBOARD_NAME}")
    return None


def keyboard_listener():
    global last_keyboard_activity

    retry_count = 0

    while True:
        device = open_keyboard()

        if device is None:
            retry_count += 1

            if retry_count % 5 == 0:
                print(f"Reintentando conexión con teclado... intento {retry_count}")

            time.sleep(KEYBOARD_RESCAN_SECONDS)
            continue

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
    """Carga dinero del día actual y total acumulado."""
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
    """Guarda dinero del día y total acumulado."""
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
    """Verifica si cambió el día y reinicia contador si es necesario."""
    today = date.today()

    if last_day != today:
        print(f"Nuevo día: {today}. Total acumulado: ${dinero_total / 1000.0:.3f}")
        dinero_total += dinero_hoy
        dinero_hoy = 0
        return today, dinero_hoy, dinero_total

    return last_day, dinero_hoy, dinero_total

# -----------------------------
# LOOP PRINCIPAL
# -----------------------------

money_thousandths, total_money_thousandths = load_data()

last_day = date.today()
last_time = time.monotonic()
last_save_time = time.monotonic()

SAVE_INTERVAL = 5

try:
    while True:
        current_time = time.monotonic()
        delta_time = current_time - last_time
        last_time = current_time

        last_day, money_thousandths, total_money_thousandths = check_new_day(
            last_day,
            money_thousandths,
            total_money_thousandths
        )

        if keyboard_is_active():
            typing_time_accumulator += delta_time

            while typing_time_accumulator >= 1.0:
                animation_state["start"] = money_thousandths
                animation_state["start_time"] = current_time

                money_thousandths += THOUSANDTHS_PER_SECOND

                last_money_update_time = current_time
                typing_time_accumulator -= 1.0
        else:
            typing_time_accumulator = 0.0

        if current_time - last_save_time >= SAVE_INTERVAL:
            save_data(money_thousandths, total_money_thousandths)
            last_save_time = current_time

        draw_money(money_thousandths, current_time)
        draw_time()

        money_strip.show()
        clock_strip.show()

        time.sleep(0.01)

except KeyboardInterrupt:
    save_data(money_thousandths, total_money_thousandths)
    clear_all()
    money_strip.show()
    clock_strip.show()

    print(f"\nDinero hoy: ${money_thousandths / 1000.0:.3f}")
    print(f"Total acumulado: ${total_money_thousandths / 1000.0:.3f}")
    