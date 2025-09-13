import itertools
import matplotlib.pyplot as plt
import numpy as np

def point_in_quadrilateral(p, quad):
    """Проверяет, находится ли точка p внутри выпуклого четырехугольника quad."""
    def sign(a, b, c):
        return (a[0] - c[0]) * (b[1] - c[1]) - (b[0] - c[0]) * (a[1] - c[1])
    
    d1 = sign(p, quad[0], quad[1])
    d2 = sign(p, quad[1], quad[2])
    d3 = sign(p, quad[2], quad[3])
    d4 = sign(p, quad[3], quad[0])
    
    has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0) or (d4 < 0)
    has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0) or (d4 > 0)
    
    return not (has_neg and has_pos)

def find_max_containing_quadrilateral(points):
    """
    Находит четырехугольник с вершинами из points, содержащий максимальное количество 
    других точек из points. Возвращает (вершины, количество внутри, точки внутри).
    """
    if len(points) < 4:
        return (points, 0, [])
    
    max_count = -1
    best_quad = None
    best_inside = []
    
    for quad in itertools.combinations(points, 4):
        quad_list = list(quad)
        inside_points = [p for p in points if p not in quad_list and point_in_quadrilateral(p, quad_list)]
        count = len(inside_points)
        
        if count > max_count:
            max_count = count
            best_quad = quad_list
            best_inside = inside_points
    
    return (best_quad, max_count, best_inside)

def find_horizontal_sides_midpoints(quad):
    """Находит середины верхней и нижней горизонтальных сторон"""
    # Сортируем точки по Y координате
    sorted_quad = sorted(quad, key=lambda p: p[1])
    
    # Нижняя сторона - две точки с наименьшими Y
    bottom_side = sorted_quad[:2]
    # Верхняя сторона - две точки с наибольшими Y
    top_side = sorted_quad[-2:]
    
    # Сортируем по X координате для нахождения левой и правой точек
    bottom_side_sorted = sorted(bottom_side, key=lambda p: p[0])
    top_side_sorted = sorted(top_side, key=lambda p: p[0])
    
    # Находим середины сторон
    bottom_mid = ((bottom_side_sorted[0][0] + bottom_side_sorted[1][0])/2, 
                  (bottom_side_sorted[0][1] + bottom_side_sorted[1][1])/2)
    top_mid = ((top_side_sorted[0][0] + top_side_sorted[1][0])/2, 
               (top_side_sorted[0][1] + top_side_sorted[1][1])/2)
    
    return bottom_mid, top_mid

def plot_points_and_quadrilateral(points, quad, inside_points):
    """Визуализирует точки, четырехугольник и вертикальную линию"""
    plt.figure(figsize=(10, 8))
    
    # Все точки
    x_all, y_all = zip(*points)
    plt.scatter(x_all, y_all, c='blue', label='Все точки')
    
    if inside_points:
        x_in, y_in = zip(*inside_points)
        plt.scatter(x_in, y_in, c='green', label='Точки внутри')
    
    x_quad, y_quad = zip(*quad)
    plt.scatter(x_quad, y_quad, c='red', s=100, label='Вершины')
    
    quad_polygon = quad + [quad[0]]
    quad_x, quad_y = zip(*quad_polygon)
    plt.plot(quad_x, quad_y, 'r-', linewidth=2)
    plt.fill(quad_x, quad_y, 'r', alpha=0.1)
    
    bottom_mid, top_mid = find_horizontal_sides_midpoints(quad)
    
    plt.plot([bottom_mid[0], top_mid[0]], [bottom_mid[1], top_mid[1]], 
             'm--', linewidth=2, label='Вертикальная линия')
    
    plt.scatter([bottom_mid[0], top_mid[0]], [bottom_mid[1], top_mid[1]], 
                c='cyan', s=80, marker='x', label='Середины сторон')
    
    plt.title(f'Четырёхугольник содержит {len(inside_points)} точек')
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.legend()
    plt.grid(True)
    plt.savefig('rect.png', dpi=300)
    plt.close()
x = np.array([2, 3, 5, 6])
y = np.array([4, 1, 6, 2])
points = list(zip(x, y))

best_quad, count, inside_points = find_max_containing_quadrilateral(points)

print("Вершины четырехугольника:", best_quad)
print("Количество точек внутри:", count)
print("Точки внутри:", inside_points)

plot_points_and_quadrilateral(points, best_quad, inside_points)