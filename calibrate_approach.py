"""
Калибровка захвата сверху.
Запустите: python calibrate_approach.py

Шаг 1 — положите объект БЛИЗКО к руке (нижняя часть кадра)
         Настройте плечо и локоть так чтобы клешня нависала над ним сверху.
         Нажмите Enter.

Шаг 2 — положите объект ДАЛЕКО от руки (верхняя часть кадра)
         Так же настройте позицию. Enter.

Результат сохраняется в config.py.

Управление:
  A / D  — плечо (shoulder) -1° / +1°
  S / W  — плечо -10° / +10°
  J / L  — локоть (elbow) -1° / +1°
  I / K  — локоть -10° / +10°
  Enter  — подтвердить позицию
  Q      — выйти без сохранения
"""

import serial
import time
import sys
import re
import msvcrt

from config import (SERIAL_PORT, BAUDRATE, SERVO_LIMITS, HOME_POSITION,
                    GRIP_OPEN, CLASS_NAMES)

try:
    arduino = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)
    time.sleep(2)
    print("✅ Arduino подключена\n")
except Exception as e:
    print(f"❌ Ошибка подключения: {e}")
    sys.exit(1)

BASE = HOME_POSITION['base']
SHMIN, SHMAX = SERVO_LIMITS['shoulder']
ELMIN, ELMAX = SERVO_LIMITS['elbow']

def send(shoulder, elbow):
    shoulder = max(SHMIN, min(SHMAX, int(shoulder)))
    elbow    = max(ELMIN, min(ELMAX, int(elbow)))
    cmd = f"go s1={BASE} s2={shoulder} s3={elbow} s4={GRIP_OPEN}\n"
    arduino.write(cmd.encode())
    return shoulder, elbow

def status(label, sh, el):
    sys.stdout.write(f"\r  {label}  |  shoulder={sh:3d}°  elbow={el:3d}°   ")
    sys.stdout.flush()

def calibrate_point(label, default_sh, default_el):
    sh, el = send(default_sh, default_el)
    print(f"\n▶ {label}")
    print("  A/D = shoulder ±1°    S/W = shoulder ±10°")
    print("  J/L = elbow ±1°       I/K = elbow ±10°")
    print("  Enter = подтвердить\n")
    status(label, sh, el)

    while True:
        ch = msvcrt.getch()
        try:
            ch = ch.decode().lower()
        except Exception:
            continue

        if   ch == 'd': sh, el = send(sh + 1,  el)
        elif ch == 'a': sh, el = send(sh - 1,  el)
        elif ch == 'w': sh, el = send(sh + 10, el)
        elif ch == 's': sh, el = send(sh - 10, el)
        elif ch == 'l': sh, el = send(sh, el + 1)
        elif ch == 'j': sh, el = send(sh, el - 1)
        elif ch == 'k': sh, el = send(sh, el + 10)
        elif ch == 'i': sh, el = send(sh, el - 10)
        elif ch in ('\r', '\n', '\x0d'):
            print(f"\n  ✅ {label}: shoulder={sh}° elbow={el}°")
            return sh, el
        elif ch == 'q':
            print("\n⚠️  Выход без сохранения")
            arduino.close()
            sys.exit(0)

        status(label, sh, el)

# Текущие значения из config как отправная точка
try:
    from config import APPROACH_NEAR_SH, APPROACH_NEAR_EL, APPROACH_FAR_SH, APPROACH_FAR_EL
    near_sh_def, near_el_def = APPROACH_NEAR_SH, APPROACH_NEAR_EL
    far_sh_def,  far_el_def  = APPROACH_FAR_SH,  APPROACH_FAR_EL
except ImportError:
    near_sh_def, near_el_def = 120, 70
    far_sh_def,  far_el_def  = 100, 90

print("=" * 55)
print("  Калибровка захвата сверху")
print("=" * 55)
print("\nШаг 1: положите объект БЛИЗКО к основанию руки.\n")
near_sh, near_el = calibrate_point("БЛИЗКО (нижняя часть кадра)", near_sh_def, near_el_def)

print("\nШаг 2: положите объект ДАЛЕКО от основания руки.\n")
far_sh, far_el = calibrate_point("ДАЛЕКО (верхняя часть кадра)", far_sh_def, far_el_def)

# Сохраняем в config.py
with open("config.py", "r", encoding="utf-8") as f:
    text = f.read()

new_block = f"""
# Калибровка захвата сверху
# NEAR — объект близко (низ кадра), FAR — объект далеко (верх кадра)
APPROACH_NEAR_Y  = 400   # пиксель Y для "близко" (подстройте под вашу камеру)
APPROACH_FAR_Y   = 80    # пиксель Y для "далеко"
APPROACH_NEAR_SH = {near_sh}
APPROACH_NEAR_EL = {near_el}
APPROACH_FAR_SH  = {far_sh}
APPROACH_FAR_EL  = {far_el}
"""

# Удаляем старый блок если есть, добавляем новый
text = re.sub(r'\n# Калибровка захвата сверху.*?APPROACH_FAR_EL\s*=\s*\d+\n',
              '', text, flags=re.DOTALL)
text = text.rstrip() + "\n" + new_block

with open("config.py", "w", encoding="utf-8") as f:
    f.write(text)

print(f"\n💾 Сохранено в config.py")
print(f"   NEAR: shoulder={near_sh}° elbow={near_el}°")
print(f"   FAR:  shoulder={far_sh}° elbow={far_el}°")

send(HOME_POSITION['shoulder'], HOME_POSITION['elbow'])
arduino.close()
