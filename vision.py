import cv2
import math
import numpy as np
from ultralytics import YOLO
from config import YOLO_MODEL_PATH, CLASS_NAMES, CAMERA_WIDTH, CAMERA_HEIGHT, CENTER_TOLERANCE, BBOX_AREA_MIN, BBOX_AREA_MAX

class Vision:
    def __init__(self):
        self.model = YOLO(YOLO_MODEL_PATH)
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, CAMERA_WIDTH)
        self.cap.set(4, CAMERA_HEIGHT)
        self.blind_zone = None

    def get_frame(self):
        ret, frame = self.cap.read()
        return frame if ret else None

    def detect_objects(self, frame):
        results = self.model(frame, verbose=False)
        detections = []
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = math.ceil(box.conf[0] * 100) / 100
                cls = int(box.cls[0])
                if conf < 0.5:
                    continue
                area = (x2 - x1) * (y2 - y1)
                if area < BBOX_AREA_MIN or area > BBOX_AREA_MAX:
                    continue
                center = ((x1 + x2) // 2, (y1 + y2) // 2)
                # Проверка слепой зоны
                if self.blind_zone and self._in_blind_zone(center):
                    continue
                detections.append({
                    'center': center,
                    'bbox': (x1, y1, x2, y2),
                    'confidence': conf,
                    'class': cls,
                    'class_name': CLASS_NAMES[cls]
                })
        return detections

    def _in_blind_zone(self, center):
        x, y = center
        x1, y1, x2, y2 = self.blind_zone
        return x1 <= x <= x2 and y1 <= y <= y2

    def select_blind_zone(self):
        """Интерактивный выбор слепой зоны"""
        frame = self.get_frame()
        if frame is None:
            return
        roi = cv2.selectROI("Выбор слепой зоны", frame, False, True)
        cv2.destroyWindow("Выбор слепой зоны")
        if roi[2] == 0 or roi[3] == 0:
            self.blind_zone = None
            print("⚠️ Слепая зона не выбрана")
        else:
            x, y, w, h = roi
            self.blind_zone = (x, y, x + w, y + h)
            print(f"✅ Слепая зона: {self.blind_zone}")

    def draw_info(self, frame, detections, closest_obj, grabber_state, arm_angles):
        # Отрисовка bounding box'ов
        for obj in detections:
            x1, y1, x2, y2 = obj['bbox']
            color = (0, 255, 0) if obj == closest_obj else (255, 0, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            label = f"{obj['class_name']}: {obj['confidence']:.2f}"
            cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            # площадь bbox — поможет подобрать BBOX_AREA_MAX
            area = (x2 - x1) * (y2 - y1)
            cv2.putText(frame, f"area:{area}", (x1, y2+15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

        # Центральная линия и допуск
        h, w = frame.shape[:2]
        cv2.line(frame, (w//2, 0), (w//2, h), (255, 255, 0), 2)
        cv2.line(frame, (w//2 - CENTER_TOLERANCE, 0), (w//2 - CENTER_TOLERANCE, h), (0, 255, 255), 1)
        cv2.line(frame, (w//2 + CENTER_TOLERANCE, 0), (w//2 + CENTER_TOLERANCE, h), (0, 255, 255), 1)

        # Слепая зона
        if self.blind_zone:
            x1, y1, x2, y2 = self.blind_zone
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(frame, "BLIND ZONE", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)

        # Текстовая информация
        texts = [
            f"Objects: {len(detections)}",
            f"State: {grabber_state}",
            f"Base: {arm_angles['base']}°",
            f"Shoulder: {arm_angles['shoulder']}°",
            f"Elbow: {arm_angles['elbow']}°",
            f"Gripper: {arm_angles['gripper']}°"
        ]
        for i, txt in enumerate(texts):
            cv2.putText(frame, txt, (10, 30 + i*25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

    def release(self):
        self.cap.release()