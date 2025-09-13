class LQController:
    def __init__(self, A, B, Q, R):
        # Определение матриц для LQC
        A = np.array([[0, 1], [0, 0]])  # Простая модель углового отклонения
        B = np.array([[0], [1]])  # Влияние углового управления
        Q = np.array([[0.5, 0], [0, 2]])  # Весовые коэффициенты для состояния
        R = np.array([[10.0]])  # Вес управления

        # Решение уравнения Риккати
        P = solve_continuous_are(A, B, Q, R)

        # Вычисление матрицы обратной связи K
        self.K = np.linalg.inv(R) @ B.T @ P

    def compute(self, current_angle, desired_angle=0.0, angle_speed=0.0):
        state = np.array([[current_angle], [angle_speed]])  # [угол; угловая скорость (пусть 0)]
        control = -self.K @ state
        print("control ", control, " current_angle ", current_angle)
        return float(control[0, 0])