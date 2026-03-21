# Параметры подключения
SERIAL_PORT = "COM9"
BAUDRATE = 115200

# Пределы углов сервоприводов (min, max)
SERVO_LIMITS = {
    'base':     (0, 180),
    'shoulder': (30, 150),
    'elbow':    (30, 150),
    'gripper':  (0, 180)
}

# Начальные углы (безопасная позиция)
HOME_POSITION = {
    'base':     90,
    'shoulder': 90,
    'elbow':    90,
    'gripper':  90
}

GRIP_OPEN  = 120
GRIP_CLOSE = 180

CENTER_TOLERANCE  = 30
GRAB_AREA         = 8000
ACTION_DELAY      = 0.8
DETECTION_TIMEOUT = 2.0
SAFE_SHOULDER     = 90
SAFE_ELBOW        = 90
GRAB_SHOULDER     = 110
GRAB_ELBOW        = 80

# Параметры камеры
CAMERA_WIDTH  = 640
CAMERA_HEIGHT = 480

BLIND_ZONE = None

YOLO_MODEL_PATH = "yolo-Weights/yolov8m-seg.pt"
CLASS_NAMES = ["Glass", "Metal", "Paper", "Plastic", "Waste"]

# =============================================================================
# ЗОНЫ СБРОСА
# Каждая зона — угол поворота базы (0–180°), куда рука едет после захвата.
# Настройте с помощью: python calibrate_zones.py
# =============================================================================
DROP_ZONES = {
    'Glass': 180,
    'Metal': 72,
    'Paper': 35,
    'Plastic': 103,
    'Waste': 135,
}

# Угол плеча и локтя при сбросе объекта в зону
DROP_SHOULDER = 110   # такой же как GRAB — опускаем над корзиной
DROP_ELBOW    = 80
SPEED_TRACK_STEPS  = 3     # слежение — оставьте быстрым
SPEED_TRACK_DELAY  = 0.01

SPEED_MOVE_STEPS   = 20    # захват, подъём, опускание
SPEED_MOVE_DELAY   = 0.05  # ← увеличивайте это для замедления

SPEED_CARRY_STEPS  = 30    # перенос к корзине
SPEED_CARRY_DELAY  = 0.07  # ← и это
