import numpy as np
from scipy.linalg import solve_continuous_are    
import cv2
import numpy as np

def moving(obs):
    """
    Функция для определения центра дороги и отклонения робота.
    obs: изображение с камеры робота.
    Возвращает:
        - center_offset: отклонение от центра дороги.
        - angle_to_center: угол поворота к центру дороги.
    """
    # Преобразуем изображение в оттенки серого
    gray = cv2.cvtColor(obs, cv2.COLOR_BGR2GRAY)

    # Применяем фильтр для выделения линий разметки (желтая и белая разметка)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)

    # Определяем область интереса (ROI) - нижняя часть изображения
    height, width = edges.shape
    roi = edges[int(height / 2):, :]

    # Находим линии с помощью преобразования Хафа
    lines = cv2.HoughLinesP(roi, 1, np.pi / 180, threshold=50, minLineLength=50, maxLineGap=150)

    # Переменные для нахождения центра дороги
    left_lines = []
    right_lines = []

    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            slope = (y2 - y1) / (x2 - x1 + 1e-6)  # Угловой коэффициент
            if slope < -0.5:  # Левая линия
                left_lines.append(line[0])
            elif slope > 0.5:  # Правая линия
                right_lines.append(line[0])

    # Вычисляем среднюю позицию левой и правой линий
    left_center = np.mean([line[:2] for line in left_lines], axis=0) if left_lines else None
    right_center = np.mean([line[:2] for line in right_lines], axis=0) if right_lines else None

    # Вычисляем центр дороги
    if left_center is not None and right_center is not None:
        road_center = (left_center[0] + right_center[0]) / 2
    elif left_center is not None:
        road_center = left_center[0] + width / 4  # Предположим, правая линия дальше
    elif right_center is not None:
        road_center = right_center[0] - width / 4  # Предположим, левая линия дальше
    else:
        road_center = width / 2  # Центр изображения по умолчанию

    # Вычисляем отклонение от центра
    robot_position = width / 2
    center_offset = (road_center - robot_position) / width

    # Вычисляем угол наклона к центру дороги
    angle_to_center = np.arctan2(road_center - robot_position, height / 2)

    return center_offset, angle_to_center


def lqr(A, B, Q, R):
    """
    Решает задачу LQR.
    Возвращает оптимальную матрицу K для состояния.
    """
    P = np.linalg.solve_continuous_are(A, B, Q, R)
    K = np.linalg.inv(R) @ B.T @ P
    return K

# Параметры робота
dt = 0.1  # шаг времени
v_max = 1.0  # максимальная скорость
omega_max = 1.0  # максимальная угловая скорость

# Динамическая модель робота (простая модель с дифференциальным управлением)
A = np.array([[0, 1],
              [0, 0]])
B = np.array([[0],
              [1]])
Q = np.diag([10, 1])  # Вес состояния
R = np.array([[1]])  # Вес управления

K = lqr(A, B, Q, R)  # Оптимальная матрица K

# Начальное состояние
state = np.array([[0],  # Отклонение от центра
                  [0]])  # Угол к центру дороги

while not done:
    # Обработка изображения и расчет текущего состояния
    center_offset, angle_to_center = moving(obs)
    state[0, 0] = center_offset
    state[1, 0] = angle_to_center

    # Вычисление управления с помощью LQR
    u = -K @ state

    # Применение управления с учетом ограничений
    omega = np.clip(u[0, 0], -omega_max, omega_max)
    action = [v_max, omega]

    # Шаг симуляции
    obs, rew, done, info = env.step(np.array(action))
    env.render()
