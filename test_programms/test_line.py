import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from sklearn.decomposition import PCA
from scipy.odr import *

# Исходные данные
x = np.array([2, 3, 5, 6])
y = np.array([4, 1, 6, 2])
points = np.column_stack((x, y))
    
# 1. Классическая линейная регрессия (МНК)
ols_res = stats.linregress(x, y)
ols_line = ols_res.intercept + ols_res.slope * x
    
# 2. Метод главных компонент (PCA)
pca = PCA(n_components=1)
centered_points = points - np.mean(points, axis=0)
pca.fit(centered_points)
pca_slope = pca.components_[0][1] / pca.components_[0][0]
pca_intercept = np.mean(y) - pca_slope * np.mean(x)
pca_line = pca_intercept + pca_slope * x
    
# 3. Total Least Squares (ортогональная регрессия)
def linear_func(p, x):
    return p[0] * x + p[1]
    
linear_model = Model(linear_func)
data = RealData(x, y)
odr = ODR(data, linear_model, beta0=[1., 1.])
odr_res = odr.run()
tls_slope, tls_intercept = odr_res.beta
tls_line = tls_intercept + tls_slope * x


plt.figure(figsize=(10, 6))
plt.plot(x, y, 'ko', label='Исходные точки', markersize=8)

plt.plot(x, ols_line, 'r-', label=f'МНК: y = {ols_res.slope:.2f}x + {ols_res.intercept:.2f}')
plt.plot(x, pca_line, 'b--', label=f'PCA: y = {pca_slope:.2f}x + {pca_intercept:.2f}')
plt.plot(x, tls_line, 'g-.', label=f'TLS: y = {tls_slope:.2f}x + {tls_intercept:.2f}')

plt.xlabel('x')
plt.ylabel('y')
plt.title('Сравнение методов регрессии')
plt.legend()
plt.grid(True)
plt.savefig('regression_comparison.png', dpi=300)
plt.close()

print("График сохранен в regression_comparison.png")