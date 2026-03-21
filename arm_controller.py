import serial
import time
from config import GRIP_OPEN, GRIP_CLOSE, CENTER_TOLERANCE, GRAB_AREA, CAMERA_WIDTH, CAMERA_HEIGHT
from config import SERIAL_PORT, BAUDRATE, SERVO_LIMITS, HOME_POSITION

class RoboticArmController:
    def __init__(self):
        self.arduino = None
        self.current_angles = HOME_POSITION.copy()

    def connect(self):
        try:
            self.arduino = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)
            time.sleep(2)
            print("✅ Подключение к Arduino установлено")
            time.sleep(0.3)
            if self.arduino.in_waiting:
                raw = self.arduino.read(self.arduino.in_waiting)
                print(f"📥 Arduino при старте: {raw.decode(errors='replace').strip()}")
            self.send_command(**HOME_POSITION)
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return False

    def send_command(self, base, shoulder, elbow, gripper):
        if not self.arduino or not self.arduino.is_open:
            print("⚠️ Arduino не подключён")
            return False

        base     = max(SERVO_LIMITS['base'][0],     min(SERVO_LIMITS['base'][1],     base))
        shoulder = max(SERVO_LIMITS['shoulder'][0], min(SERVO_LIMITS['shoulder'][1], shoulder))
        elbow    = max(SERVO_LIMITS['elbow'][0],    min(SERVO_LIMITS['elbow'][1],    elbow))
        gripper  = max(SERVO_LIMITS['gripper'][0],  min(SERVO_LIMITS['gripper'][1],  gripper))

        command = f"go s1={int(base)} s2={int(shoulder)} s3={int(elbow)} s4={int(gripper)}\n"
        try:
            self.arduino.write(command.encode())
            print(f"📤 {command.strip()}")
            self.current_angles = {
                'base': base, 'shoulder': shoulder,
                'elbow': elbow, 'gripper': gripper
            }
            return True
        except Exception as e:
            print(f"❌ Ошибка отправки: {e}")
            return False

    def move_smooth(self, target_base, target_shoulder, target_elbow, target_gripper, steps=10, delay=0.03):
        start = self.current_angles.copy()
        for i in range(1, steps + 1):
            t = i / steps
            b = start['base']     + (target_base     - start['base'])     * t
            s = start['shoulder'] + (target_shoulder - start['shoulder']) * t
            e = start['elbow']    + (target_elbow    - start['elbow'])    * t
            g = start['gripper']  + (target_gripper  - start['gripper'])  * t
            self.send_command(b, s, e, g)
            time.sleep(delay)

    def calculate_base_angle_from_pixel(self, pixel_x):
        t = 1-(pixel_x / CAMERA_WIDTH)
        angle = SERVO_LIMITS['base'][0] + t * (SERVO_LIMITS['base'][1] - SERVO_LIMITS['base'][0])
        return int(angle)

    def go_home(self):
        print("🏠 Возврат в HOME...")
        self.move_smooth(
            HOME_POSITION['base'], HOME_POSITION['shoulder'],
            HOME_POSITION['elbow'], HOME_POSITION['gripper'],
            steps=15, delay=0.03
        )

    def close(self):
        if self.arduino and self.arduino.is_open:
            self.arduino.close()
            print("🔌 Соединение закрыто")
