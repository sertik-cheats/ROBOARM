import time
from config import (ACTION_DELAY, GRIP_OPEN, GRIP_CLOSE, CENTER_TOLERANCE,
                    GRAB_AREA, CAMERA_WIDTH, CAMERA_HEIGHT, DETECTION_TIMEOUT,
                    DROP_ZONES, DROP_SHOULDER, DROP_ELBOW,
                    SPEED_TRACK_STEPS, SPEED_TRACK_DELAY,
                    SPEED_MOVE_STEPS, SPEED_MOVE_DELAY,
                    SPEED_CARRY_STEPS, SPEED_CARRY_DELAY,
                    APPROACH_NEAR_Y, APPROACH_FAR_Y,
                    APPROACH_NEAR_SH, APPROACH_NEAR_EL,
                    APPROACH_FAR_SH, APPROACH_FAR_EL)
from arm_controller import RoboticArmController

ANGLE_DEADZONE       = 3
HOLD_RELEASE_TIMEOUT = 3.0
COAST_TIMEOUT        = 1.5
TRANSITION_GUARD     = 0.5

class GrabController:
    def __init__(self, arm: RoboticArmController):
        self.arm   = arm
        self.state = "TRACK"
        self.last_action_time     = time.time()
        self.action_delay         = ACTION_DELAY
        self.first_detection_time = None
        self.hold_lost_time       = None
        self.grabbed_class        = None

        self.safe_angles = {'shoulder': 90, 'elbow': 90}

        self._last_known_obj     = None
        self._last_seen_time     = None
        self._state_entered_time = time.time()

    def can_act(self):
        return time.time() - self.last_action_time > self.action_delay

    def _set_state(self, new_state):
        if self.state != new_state:
            print(f"  → {new_state}")
            self.state = new_state
            self._state_entered_time = time.time()

    def _in_new_state(self):
        return time.time() - self._state_entered_time < TRANSITION_GUARD

    def reset(self):
        print("🔄 СБРОС → TRACK")
        self.state                = "TRACK"
        self.last_action_time     = time.time()
        self.first_detection_time = None
        self.hold_lost_time       = None
        self.grabbed_class        = None
        self._last_known_obj      = None
        self._last_seen_time      = None
        self._state_entered_time  = time.time()
        self.arm.go_home()

    def _get_base_from_obj(self, obj):
        if obj is not None:
            cx, _ = obj['center']
            return self.arm.calculate_base_angle_from_pixel(cx)
        return self.arm.current_angles['base']

    def _get_approach_angles(self, obj):
        """
        Вычисляет углы плеча и локтя для захвата сверху
        на основе Y-координаты объекта в кадре.
        Ближе к низу кадра (большой Y) = объект близко = NEAR-углы.
        Ближе к верху кадра (малый Y)  = объект далеко = FAR-углы.
        """
        if obj is None:
            return APPROACH_NEAR_SH, APPROACH_NEAR_EL

        _, cy = obj['center']

        # Клампируем Y в диапазон калибровки
        cy = max(APPROACH_FAR_Y, min(APPROACH_NEAR_Y, cy))

        # t=0 → далеко (верх кадра), t=1 → близко (низ кадра)
        t = (cy - APPROACH_FAR_Y) / max(APPROACH_NEAR_Y - APPROACH_FAR_Y, 1)

        shoulder = APPROACH_FAR_SH + (APPROACH_NEAR_SH - APPROACH_FAR_SH) * t
        elbow    = APPROACH_FAR_EL + (APPROACH_NEAR_EL - APPROACH_FAR_EL) * t

        return int(shoulder), int(elbow)

    def _drop_base_angle(self):
        if self.grabbed_class and self.grabbed_class in DROP_ZONES:
            return DROP_ZONES[self.grabbed_class]
        return self.arm.current_angles['base']

    def _resolve_obj(self, obj):
        if obj is not None:
            self._last_known_obj = obj
            self._last_seen_time = time.time()
            return obj
        if self._last_known_obj is not None:
            if time.time() - self._last_seen_time < COAST_TIMEOUT:
                return self._last_known_obj
        return None

    def update(self, raw_obj):
        obj = self._resolve_obj(raw_obj) if self.state == "TRACK" else raw_obj

        # ── TRACK ────────────────────────────────────────────────────────────
        if self.state == "TRACK":
            if obj is not None:
                base = self._get_base_from_obj(obj)
                if abs(base - self.arm.current_angles['base']) > ANGLE_DEADZONE:
                    self.arm.move_smooth(
                        base,
                        self.safe_angles['shoulder'],
                        self.safe_angles['elbow'],
                        GRIP_OPEN,
                        steps=SPEED_TRACK_STEPS, delay=SPEED_TRACK_DELAY
                    )
                if self.first_detection_time is None:
                    self.first_detection_time = time.time()
                elif time.time() - self.first_detection_time >= DETECTION_TIMEOUT:
                    self._set_state("APPROACH")
                    self.last_action_time = time.time()
                    self.first_detection_time = None
            else:
                self.first_detection_time = None
                self._last_known_obj = None
                self._last_seen_time = None

        # ── APPROACH: опускаемся над объектом сверху ─────────────────────────
        elif self.state == "APPROACH" and self.can_act():
            base = self._get_base_from_obj(obj)
            sh, el = self._get_approach_angles(obj)
            print(f"📐 Подход сверху: base={base}° shoulder={sh}° elbow={el}°")
            self.arm.move_smooth(base, sh, el, GRIP_OPEN,
                                 steps=SPEED_MOVE_STEPS, delay=SPEED_MOVE_DELAY)
            self._set_state("GRAB")
            self.last_action_time = time.time()

        # ── GRAB ─────────────────────────────────────────────────────────────
        elif self.state == "GRAB" and self.can_act():
            base = self._get_base_from_obj(obj)
            sh, el = self._get_approach_angles(obj)
            if obj is not None:
                self.grabbed_class = obj['class_name']
                print(f"🤏 Захват: {self.grabbed_class} → зона {DROP_ZONES.get(self.grabbed_class, '?')}°")
            self.arm.move_smooth(base, sh, el, GRIP_CLOSE,
                                 steps=SPEED_MOVE_STEPS, delay=SPEED_MOVE_DELAY)
            self._set_state("LIFT")
            self.last_action_time = time.time()

        # ── LIFT ─────────────────────────────────────────────────────────────
        elif self.state == "LIFT" and self.can_act():
            base = self._get_base_from_obj(obj)
            self.arm.move_smooth(base, self.safe_angles['shoulder'],
                                 self.safe_angles['elbow'], GRIP_CLOSE,
                                 steps=SPEED_MOVE_STEPS, delay=SPEED_MOVE_DELAY)
            self._set_state("CARRY")
            self.last_action_time = time.time()

        # ── CARRY ────────────────────────────────────────────────────────────
        elif self.state == "CARRY" and self.can_act():
            drop_base = self._drop_base_angle()
            print(f"🚚 Везу {self.grabbed_class} → {drop_base}°")
            self.arm.move_smooth(drop_base, self.safe_angles['shoulder'],
                                 self.safe_angles['elbow'], GRIP_CLOSE,
                                 steps=SPEED_CARRY_STEPS, delay=SPEED_CARRY_DELAY)
            self._set_state("DROP")
            self.last_action_time = time.time()

        # ── DROP ─────────────────────────────────────────────────────────────
        elif self.state == "DROP" and self.can_act():
            drop_base = self._drop_base_angle()
            self.arm.move_smooth(drop_base, DROP_SHOULDER, DROP_ELBOW, GRIP_CLOSE,
                                 steps=SPEED_MOVE_STEPS, delay=SPEED_MOVE_DELAY)
            self._set_state("RELEASE")
            self.last_action_time = time.time()

        # ── RELEASE ──────────────────────────────────────────────────────────
        elif self.state == "RELEASE" and self.can_act():
            drop_base = self._drop_base_angle()
            self.arm.move_smooth(drop_base, DROP_SHOULDER, DROP_ELBOW, GRIP_OPEN,
                                 steps=SPEED_MOVE_STEPS, delay=SPEED_MOVE_DELAY)
            print(f"✅ Сброшено в зону {self.grabbed_class}")
            self.grabbed_class = None
            self._set_state("RETURN")
            self.last_action_time = time.time()

        # ── RETURN ───────────────────────────────────────────────────────────
        elif self.state == "RETURN" and self.can_act():
            self.arm.go_home()
            self._set_state("TRACK")
            self.last_action_time = time.time()

        # ── HOLD ─────────────────────────────────────────────────────────────
        elif self.state == "HOLD":
            if obj is None:
                if self.hold_lost_time is None:
                    self.hold_lost_time = time.time()
                elif time.time() - self.hold_lost_time > HOLD_RELEASE_TIMEOUT:
                    print("🔄 HOLD → TRACK")
                    self._set_state("TRACK")
                    self.hold_lost_time = None
            else:
                self.hold_lost_time = None

        # ── Сброс при потере в промежуточных состояниях ───────────────────────
        if (raw_obj is None
                and self.state in ("APPROACH", "GRAB", "LIFT")
                and not self._in_new_state()
                and (self._last_seen_time is None
                     or time.time() - self._last_seen_time >= COAST_TIMEOUT)):
            print(f"⚠️ Объект потерян в {self.state} → TRACK")
            self._set_state("TRACK")
            self.grabbed_class = None
            self.first_detection_time = None
            self._last_known_obj = None
            self._last_seen_time = None
