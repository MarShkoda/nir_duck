import cv2
import numpy as np
import math

def lane_offset_angle(image_path):
    img = cv2.imread(image_path)
    h, w = img.shape[:2]
    
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Более широкие диапазоны
    blue_mask = cv2.inRange(hsv, (70, 40, 40), (100, 255, 255))   # голубая линия
    white_mask = cv2.inRange(hsv, (0, 0, 180), (180, 80, 255))    # белые линии

    # выделим нижнюю часть (важнее для смещения)
    roi = slice(int(h*0.6), h)

    blue_pts = np.column_stack(np.where(blue_mask[roi,:] > 0))
    white_pts = np.column_stack(np.where(white_mask[roi,:] > 0))

    if len(blue_pts) == 0 or len(white_pts) == 0:
        print("Линии не найдены")
        return None

    # сдвигаем координаты ROI обратно в систему всего изображения
    blue_pts[:,0] += int(h*0.6)
    white_pts[:,0] += int(h*0.6)

    # аппроксимация полиномом 1-й степени (прямая)
    bx, by = blue_pts[:,1], blue_pts[:,0]
    wx, wy = white_pts[:,1], white_pts[:,0]

    blue_fit = np.polyfit(by, bx, 1)  # x = m*y + b
    white_fit = np.polyfit(wy, wx, 1)

    # координаты внизу изображения
    y_eval = h-1
    x_blue = blue_fit[0]*y_eval + blue_fit[1]
    x_white = white_fit[0]*y_eval + white_fit[1]

    # центр правой полосы
    lane_center = (x_blue + x_white) / 2
    cam_center = w/2

    offset_px = cam_center - lane_center

    # угол линии (по голубой)
    slope = blue_fit[0]
    angle = math.degrees(math.atan(slope))

    print(f"Смещение от центра полосы: {offset_px:.1f} px (положит. = левее)")
    print(f"Угол отклонения линии: {angle:.2f}°")

    # Визуализация
    out = img.copy()
    cv2.line(out, (int(x_blue), h-1), (int(x_white), h-1), (0,255,0), 2)
    cv2.circle(out, (int(lane_center), h-1), 8, (0,0,255), -1)
    cv2.circle(out, (int(cam_center), h-1), 8, (255,0,0), -1)

    cv2.imshow("Result", out)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    return offset_px, angle

lane_offset_angle("test.png")
