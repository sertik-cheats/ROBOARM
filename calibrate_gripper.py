"""
Калибровка клешни.
Запустите отдельно: python calibrate_gripper.py

  A / D  — угол -1° / +1°
  W / S  — угол -10° / +10°
  O      — запомнить как GRIP_OPEN
  C      — запомнить как GRIP_CLOSE
  Enter  — сохранить в config.py и выйти
  Q      — выйти без сохранения
"""

import serial
import time
import sys
import re
import msvcrt

from config import SERIAL_PORT, BAUDRATE, SERVO_LIMITS, HOME_POSITION, GRIP_OPEN, GRIP_CLOSE

try:
    arduino = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)
    time.sleep(2)
    print("✅ Arduino подключена\n")
except Exception as e:
    print(f"❌ Ошибка подключения: {e}")
    sys.exit(1)

saved_open  = GRIP_OPEN
saved_close = GRIP_CLOSE
current     = HOME_POSITION['gripper']

B  = HOME_POSITION['base']
SH = HOME_POSITION['shoulder']
EL = HOME_POSITION['elbow']
GMIN = SERVO_LIMITS['gripper'][0]
GMAX = SERVO_LIMITS['gripper'][1]

def send(angle):
    angle = max(GMIN, min(GMAX, int(angle)))
    cmd = f"go s1={B} s2={SH} s3={EL} s4={angle}\n"
    arduino.write(cmd.encode())
    return angle

def status():
    bar_len = 40
    ratio  = (current - GMIN) / max(GMAX - GMIN, 1)
    filled = int(bar_len * ratio)
    bar    = "█" * filled + "░" * (bar_len - filled)
    sys.stdout.write(f"\r  [{bar}] {current:3d}°  |  OPEN={saved_open}  CLOSE={saved_close}   ")
    sys.stdout.flush()

send(current)
print("Положите объект (~45мм) в клешню.\n")
print("  A/D = ±1°    W/S = ±10°    O = сохранить OPEN    C = сохранить CLOSE    Enter = записать    Q = выйти\n")
status()

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
    elif ch == 'o':
        saved_open = current
        print(f"\n  ✅ GRIP_OPEN  = {saved_open}")
    elif ch == 'c':
        saved_close = current
        print(f"\n  ✅ GRIP_CLOSE = {saved_close}")
    elif ch in ('\r', '\n', '\x0d'):
        with open("config.py", "r", encoding="utf-8") as f:
            text = f.read()
        text = re.sub(r'GRIP_OPEN\s*=\s*\d+',  f'GRIP_OPEN  = {saved_open}',  text)
        text = re.sub(r'GRIP_CLOSE\s*=\s*\d+', f'GRIP_CLOSE = {saved_close}', text)
        with open("config.py", "w", encoding="utf-8") as f:
            f.write(text)
        print(f"\n\n💾 Сохранено в config.py:  GRIP_OPEN={saved_open}  GRIP_CLOSE={saved_close}")
        break
    elif ch == 'q':
        print("\n⚠️  Выход без сохранения")
        break

    status()

arduino.close()
