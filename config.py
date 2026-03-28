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

GRIP_OPEN  = 100
GRIP_CLOSE = 5

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
    'Glass':   45,   # угол базы для стекла
    'Metal':   90,   # угол базы для металла
    'Paper':   135,  # угол базы для бумаги
    'Plastic': 45,   # угол базы для пластика
    'Waste':   135,  # угол базы для прочего мусора
}

# Угол плеча и локтя при сбросе объекта в зону
DROP_SHOULDER = 110   # такой же как GRAB — опускаем над корзиной
DROP_ELBOW    = 80

# =============================================================================
# СКОРОСТЬ ДВИЖЕНИЯ
# steps  — количество промежуточных точек (больше = плавнее)
# delay  — пауза между шагами в секундах (больше = медленнее)
#
# Пресеты:
#   Быстро:   steps=5,  delay=0.02
#   Нормально: steps=10, delay=0.03
#   Медленно:  steps=20, delay=0.05
#   Очень медленно: steps=30, delay=0.07
# =============================================================================
SPEED_TRACK_STEPS  = 3     # слежение за объектом (лучше оставить быстрым)
SPEED_TRACK_DELAY  = 0.01

SPEED_MOVE_STEPS   = 20    # все основные движения (APPROACH, GRAB, LIFT...)
SPEED_MOVE_DELAY   = 0.05

SPEED_CARRY_STEPS  = 30    # перенос к корзине (можно ещё медленнее)
SPEED_CARRY_DELAY  = 0.07

# Фильтр размера объектов
# Объекты меньше MIN — шум, больше MAX — скорее всего сама рука
BBOX_AREA_MIN = 500     # минимальная площадь bbox в пикселях
BBOX_AREA_MAX = 60000   # максимальная площадь bbox (рука обычно > 80000)

# Калибровка захвата сверху
# NEAR — объект близко (низ кадра), FAR — объект далеко (верх кадра)
APPROACH_NEAR_Y  = 400   # пиксель Y для "близко" (подстройте под вашу камеру)
APPROACH_FAR_Y   = 80    # пиксель Y для "далеко"
APPROACH_NEAR_SH = 80
APPROACH_NEAR_EL = 30
APPROACH_FAR_SH  = 150
APPROACH_FAR_EL  = 60
