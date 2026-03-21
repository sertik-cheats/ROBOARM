"""
Калибровка зон сброса.
Запустите отдельно: python calibrate_zones.py

Для каждого класса мусора:
  A / D  — повернуть базу -1° / +1°
  S / W  — повернуть базу -10° / +10°
  Enter  — подтвердить зону и перейти к следующей
  Q      — выйти без сохранения

Результат автоматически записывается в config.py
"""

import serial
import time
import sys
import re
import msvcrt

from config import SERIAL_PORT, BAUDRATE, SERVO_LIMITS, HOME_POSITION, DROP_ZONES, CLASS_NAMES

try:
    arduino = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)
    time.sleep(2)
    print("✅ Arduino подключена\n")
except Exception as e:
    print(f"❌ Ошибка подключения: {e}")
    sys.exit(1)

SH   = HOME_POSITION['shoulder']
EL   = HOME_POSITION['elbow']
GR   = HOME_POSITION['gripper']
BMIN = SERVO_LIMITS['base'][0]
BMAX = SERVO_LIMITS['base'][1]

def send(base):
    base = max(BMIN, min(BMAX, int(base)))
    cmd = f"go s1={base} s2={SH} s3={EL} s4={GR}\n"
    arduino.write(cmd.encode())
    return base

def status(cls_name, angle):
    bar_len = 40
    ratio  = (angle - BMIN) / max(BMAX - BMIN, 1)
    filled = int(bar_len * ratio)
    bar    = "█" * filled + "░" * (bar_len - filled)
    sys.stdout.write(f"\r  [{bar}] {angle:3d}°  ({cls_name})   ")
    sys.stdout.flush()

# Классы которые нужно откалибровать — только уникальные зоны
# (Waste не показываем отдельно — по умолчанию совпадает с Paper)
classes_to_calibrate = [c for c in CLASS_NAMES if c != 'Waste']

new_zones = dict(DROP_ZONES)  # копия текущих значений

print("Наведите руку на центр каждой корзины и нажмите Enter.\n")
print("  A/D = ±1°    W/S = ±10°    Enter = подтвердить    Q = выйти\n")

for cls in classes_to_calibrate:
    current = new_zones.get(cls, HOME_POSITION['base'])
    current = send(current)
    print(f"\n▶ Класс: {cls}  (текущий угол: {current}°)")
    status(cls, current)

    confirmed = False
    while True:
        ch = msvcrt.getch()
        try:
            ch = ch.decode().lower()
        except Exception:
            continue

        if   ch == 'd': current = send(current + 1)
        elif ch == 'a': current = send(current - 1)
        elif ch == 'w': current = send(current + 10)
        elif ch == 's': current = send(current - 10)
        elif ch in ('\r', '\n', '\x0d'):
            new_zones[cls] = current
            print(f"\n  ✅ {cls} → {current}°")
            confirmed = True
            break
        elif ch == 'q':
            print("\n⚠️  Выход без сохранения")
            arduino.close()
            sys.exit(0)

        status(cls, current)

# Waste = Paper по умолчанию если не переопределено
if 'Waste' not in new_zones:
    new_zones['Waste'] = new_zones.get('Paper', HOME_POSITION['base'])

# Сохраняем в config.py
with open("config.py", "r", encoding="utf-8") as f:
    text = f.read()

zones_str = "DROP_ZONES = {\n"
for k, v in new_zones.items():
    zones_str += f"    '{k}': {v},\n"
zones_str += "}"

text = re.sub(r"DROP_ZONES\s*=\s*\{[^}]*\}", zones_str, text, flags=re.DOTALL)

with open("config.py", "w", encoding="utf-8") as f:
    f.write(text)

print(f"\n\n💾 Зоны сохранены в config.py:")
for k, v in new_zones.items():
    print(f"   {k}: {v}°")

# Возвращаем в HOME
send(HOME_POSITION['base'])
arduino.close()
