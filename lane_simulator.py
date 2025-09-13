import cv2
import math
import numpy as np
from gym_duckietown.envs import DuckietownEnv
from controllers.pid_controller import PIDController

# ========== Алгоритм обнаружения линии (упрощён LaneKeeping V2) ==========
class LaneDetector:
    def __init__(self):
        # Параметры Калмана
        self.kalman = cv2.KalmanFilter(2, 1)
        self.kalman.transitionMatrix = np.array([[1, 1], [0, 1]], np.float32)
        self.kalman.measurementMatrix = np.array([[1, 0]], np.float32)
        self.kalman.processNoiseCov = np.eye(2, dtype=np.float32) * 0.03
        self.kalman.measurementNoiseCov = np.array([[0.5]], np.float32)

    def detect_angle(self, frame):
        h, w = frame.shape[:2]
        roi = frame[int(h*0.5):, :]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5,5), 0)
        edges = cv2.Canny(blur, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 50, minLineLength=50, maxLineGap=100)

        if lines is None:
            return 0.0, frame

        # Собираем точки
        points = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            points.append([x1, y1])
            points.append([x2, y2])
        points = np.array(points)

        # Линия регрессии
        [vx, vy, x0, y0] = cv2.fitLine(points, cv2.DIST_L2, 0, 0.01, 0.01)
        angle = math.degrees(math.atan2(vy, vx))

        # Сглаживаем
        measurement = np.array([[np.float32(angle)]])
        self.kalman.correct(measurement)
        smoothed_angle = float(self.kalman.statePost[0])

        # Визуализация
        overlay = frame.copy()
        x1 = int(x0 - vx * 1000)
        y1 = int(h - 100 + y0 - vy * 1000)
        x2 = int(x0 + vx * 1000)
        y2 = int(h - 100 + y0 + vy * 1000)
        cv2.line(overlay, (x1, y1), (x2, y2), (0,255,0), 3)

        return smoothed_angle, overlay

# ========== Инициализация симулятора ==========
env = DuckietownEnv(
    seed=42,
    map_name="zigzag_dists",
    max_steps=1000,
    camera_width=640,
    camera_height=480,
    accept_start_angle_deg=1,
    full_transparency=True,
    distortion=True,
    domain_rand=False
)

obs = env.reset()
done = False
step = 0
dt = 0.05

lane_detector = LaneDetector()
pid = PIDController(kp=0.35, ki=0.02, kd=0.01)

# ========== Основной цикл ==========
while not done:
    frame = np.ascontiguousarray(obs)

    angle_deg, vis = lane_detector.detect_angle(frame)
    current_angle_rad = math.radians(angle_deg)
    desired_angle = 0.0  # прямо

    error = desired_angle - current_angle_rad
    control = pid.compute(error, dt)

    action = [0.6, -control * 20]
    obs, reward, done, info = env.step(np.array(action))
    env.render()

    cv2.imshow("Lane Visualization", vis)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
