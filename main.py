import cv2
from arm_controller import RoboticArmController
from grab_controller import GrabController
from vision import Vision
from config import *

# Все состояния для отображения на экране
STATE_COLORS = {
    "TRACK":   (0, 255, 0),
    "APPROACH":(0, 255, 255),
    "GRAB":    (0, 165, 255),
    "LIFT":    (255, 165, 0),
    "CARRY":   (255, 0, 255),
    "DROP":    (0, 0, 255),
    "RELEASE": (255, 0, 128),
    "RETURN":  (128, 128, 255),
    "HOLD":    (255, 255, 0),
}

def draw_drop_zones(frame):
    """Показывает настроенные зоны сброса в углу экрана."""
    y = 30
    cv2.putText(frame, "DROP ZONES:", (CAMERA_WIDTH - 200, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    for cls, angle in DROP_ZONES.items():
        y += 20
        cv2.putText(frame, f"  {cls}: {angle}deg", (CAMERA_WIDTH - 200, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)

def main():
    arm = RoboticArmController()
    if not arm.connect():
        return

    vision = Vision()
    vision.select_blind_zone()

    grabber = GrabController(arm)

    print("🚀 Система запущена.")
    print("  q       — выход")
    print("  0       — сброс в TRACK + HOME")
    print("  t/a/g/l/h — ручная смена состояния")
    print("  (калибровка зон: python calibrate_zones.py)")

    while True:
        frame = vision.get_frame()
        if frame is None:
            break

        detections = vision.detect_objects(frame)

        closest = None
        if detections:
            center_frame = (CAMERA_WIDTH // 2, CAMERA_HEIGHT // 2)
            closest = min(detections, key=lambda obj:
                (obj['center'][0] - center_frame[0])**2 +
                (obj['center'][1] - center_frame[1])**2)

        grabber.update(closest)

        # Рисуем UI
        vision.draw_info(frame, detections, closest, grabber.state, arm.current_angles)
        draw_drop_zones(frame)

        # Цветная плашка состояния
        color = STATE_COLORS.get(grabber.state, (255, 255, 255))
        cv2.rectangle(frame, (0, CAMERA_HEIGHT - 30), (CAMERA_WIDTH, CAMERA_HEIGHT), color, -1)
        label = grabber.state
        if grabber.grabbed_class:
            label += f" [{grabber.grabbed_class}]"
        cv2.putText(frame, label, (10, CAMERA_HEIGHT - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

        cv2.imshow("Robotic Arm Control", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('0'):
            grabber.state = "TRACK"
            grabber.grabbed_class = None
            arm.go_home()
        elif key == ord('t'): grabber.state = "TRACK"
        elif key == ord('a'): grabber.state = "APPROACH"
        elif key == ord('g'): grabber.state = "GRAB"
        elif key == ord('l'): grabber.state = "LIFT"
        elif key == ord('h'): grabber.state = "HOLD"

    vision.release()
    arm.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
