import numpy as np
from pyglet.window import key
from gym_duckietown.envs import DuckietownEnv
import cv2
import enum
import math
from scipy.linalg import solve_continuous_are
from controllers.pid_controller import PIDController

        
@enum.unique
class ColorLine(enum.Enum):
    yellow = 2
    white = 1

def draw_rainbow_cont(contours, height, width):
    #image = cv2.imread("//home//userubuntu//gym-duckietown//rubbish//logo2.png")
    image = np.zeros((height, width, 3), np.uint8)
    for i in range(len(contours)):
        sel_countours=[contours[i]]
        r = (10*i)%255
        g = (5*i)%255
        b = i+100
        cv2.drawContours(image, sel_countours, -1, (r,g,b), 1)
    return image

def lines(edges, height, width):
    houghLines = cv2.HoughLinesP( 1, np.pi / 180, 50, None, 50, 10)
    image = np.zeros((height, width, 3), np.uint8)
    if houghLines is not None:
        #print(houghLines)
        #for points in houghLines:
        for i in range(len(houghLines)):
      # Extracted points nested in the list
            x1,y1,x2,y2=houghLines[i][0]
            r = (10*i)%255
            g = (5*i)%255
            b = i+100
            cv2.line(image,(x1,y1),(x2,y2),(r,g,b),2)
    return image
    
def aprox(cnts, height, width):
    #img = cv2.imread("//home//userubuntu//gym-duckietown//rubbish//logo3.png")
    img = np.zeros((height, width, 3), np.uint8)
    key = 1
    #print('cnts')
    #print(cnts)
    approx_cnt = []
    for cnt in cnts:
        if (cv2.arcLength(cnt, True) > 40):
            approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)
            approx_cnt.append(approx)
            #print(len(approx))
            if len(approx) < 3:
                #print("Blue = pentagon")
                cv2.drawContours(img, [approx], 0, (255, 255, 255), -1)
            if len(approx) == 3:
                #print("Blue = pentagon")
                cv2.drawContours(img, [approx], 0, 255, -1)
            elif len(approx) == 4:
                if (key == 1):
                    print(approx)
                    key = 0
                #print("Green = triangle")
                cv2.drawContours(img, [approx], 0, (0, 255, 0), -1)
            elif len(approx) == 5:
                #print("Red = square")
                cv2.drawContours(img, [approx], 0, (0, 0, 255), -1)
            elif len(approx) == 6:
                #print("Cyan = Hexa")
                cv2.drawContours(img, [approx], 0, (255, 255, 0), -1)
            elif len(approx) == 7:
                #print("White = Octa")
                cv2.drawContours(img, [approx], 0, (255, 255, 255), -1)
            elif len(approx) < 13:
                #print("White = Octa")
                cv2.drawContours(img, [approx], 0, (0, 0, 0), -1)
            elif len(approx) > 12:
                #print("Yellow = circle")
                cv2.drawContours(img, [approx], 0, (0, 255, 255), -1)
    print('approx_cnt')
    print(approx_cnt)
    return img, approx_cnt

def aproxLine(cnts, height, width):
    img = np.zeros((height, width, 3), np.uint8)
    key = 1
    for cnt in cnts:
        if (cv2.arcLength(cnt, True) > 20):
            approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)
            #cv2.polylines(img, [approx], isClosed=False, color=(0, 255, 0), thickness=2)
    return img
    
def centerCnts(cnts, height, width):
    img = np.zeros((height, width, 3), np.uint8)
    min_x, min_y = width+10,height+10
    max_x, max_y = -1,-1
    for cnt in cnts:
        if (cv2.arcLength(cnt, True) > 20):
            approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)
            if len(approx) < 7:
                cv2.drawContours(img, [approx], 0, (255, 255, 255), -1)
                M = cv2.moments(approx)
                if M['m00'] != 0:
                    cx = int(M['m10']/M['m00'])
                    cy = int(M['m01']/M['m00'])
                    cv2.circle(img, (cx, cy), 4, (0, 0, 255), -1)
                    if (cy < min_y):
                        min_y = cy
                        min_x = cx
                    if (cy > max_y):
                        max_y = cy
                        max_x = cx
    cv2.circle(img, (max_x, max_y), 4, (0, 255, 0), -1)
    cv2.circle(img, (min_x, min_y), 4, (0, 255, 0), -1)
    cv2.circle(img, (351, 106), 4, (255, 255, 0), -1)
    line = [min_x, min_y, max_x, max_y]
    return img, line

def line_intersection(line1, line2):
    x1, y1 = line1[0],line1[1]
    x2, y2 = line1[2],line1[3]
    x3, y3 = line2[0],line2[1]
    x4, y4 = line2[2],line2[3]

    # Коэффициенты для первой прямой
    A1 = y2 - y1
    B1 = x1 - x2
    C1 = x2 * y1 - x1 * y2

    # Коэффициенты для второй прямой
    A2 = y4 - y3
    B2 = x3 - x4
    C2 = x4 * y3 - x3 * y4

    # Определитель
    D = A1 * B2 - A2 * B1

    if D == 0:
        # Прямые параллельны
        return None
    else:
        # Найти точку пересечения
        x = (B1 * C2 - B2 * C1) / D
        y = (A2 * C1 - A1 * C2) / D
        return x, y

def fiting_line(color, contours, height, width, img):
    points = []
    if (len(contours) > 0):
        for cnt in contours:
            sorted_cnt = sorted(cnt, key= lambda cnt: cnt[0][1])
            #print("sort")
            #print(sorted_cnt)
            max_y1 = sorted_cnt[-1]
            max_y2 = sorted_cnt[-2]
            points.append((max_y1+max_y2)/2)
            min_y1 = sorted_cnt[0]
            min_y2 = sorted_cnt[1]
            points.append((min_y1+min_y2)/2)
        sorted_points = sorted(points, key= lambda pnts: pnts[0][1])
        max_p = sorted_points[-1]
        min_p = sorted_points[0]
    else:
        if (ColorLine.yellow == color):
            min_p = [[0, int(0.59 * height)]]  # верхняя граница
            max_p = [[0, int(0.78 * height)]]  # нижняя граница
        if (ColorLine.white == color):
            min_p = [[width, int(0.59 * height)]]  # верхняя граница
            max_p = [[width, int(0.78 * height)]]  # нижняя граница
    cv2.line(img, (int(min_p[0][0]), int(min_p[0][1])), (int(max_p[0][0]), int(max_p[0][1])), (0, 255, 0), 2)
    line = np.array([min_p[0], max_p[0]])
    print("line", line)
    return img, line

def region_selection(image, color):
	# create an array of the same size as of the input image 
	mask = np.zeros_like(image) 
	# if you pass an image with more then one channel
	if len(image.shape) > 2:
		channel_count = image.shape[2]
		ignore_mask_color = (255,) * channel_count
	# our image only has one channel so it will go under "else"
	else:
		# color of the mask polygon (white)
		ignore_mask_color = 255
	# creating a polygon to focus only on the road in the picture
	# we have created this polygon in accordance to how the camera was placed
	rows, cols = image.shape[:2]
	if (ColorLine.yellow == color):
		left_border = 0
		right_border = 1 #0.75
	elif (ColorLine.white == color):
		left_border = 0.5
		right_border = 1
	bottom_left = [cols * left_border, rows * 0.78]
	bottom_right = [cols * right_border, rows * 0.78]
	top_left = [cols * left_border, rows * 0.59]
	top_right= [cols * right_border, rows * 0.59]
	vertices = np.array([[bottom_left, top_left, top_right, bottom_right]], dtype=np.int32)
	cv2.fillPoly(mask, vertices, ignore_mask_color)
	masked_image = cv2.bitwise_and(image, mask)
	return masked_image
    
def moving_test(obs,step):
    height = 480
    width = 640
    img = np.ascontiguousarray(obs)
    img_orig = np.ascontiguousarray(obs)
    mask_yellow = cv2.inRange(img, (140, 140, 0), (255, 255, 150)) #подобрать значения
    mask_white = cv2.inRange(img, (160, 160, 160), (255, 255, 255))
    mask_white = region_selection(mask_white, ColorLine.white)
    mask_yellow = region_selection(mask_yellow, ColorLine.yellow)
    # combine the masks using bitwise OR
    mask = cv2.bitwise_or(mask_yellow, mask_white)
    # apply the mask to the original image
    #result = cv2.bitwise_and(img, img, mask=mask)
    amount_yellow = cv2.countNonZero(mask)
    white_contours, ier = cv2.findContours(mask_white, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    yellow_contours, ier = cv2.findContours(mask_yellow, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    mask_contours, ier = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    #print(len(contours))    
    #image = draw_rainbow_cont(contours,480,640)
    rainbow_image, rainbow_aprox = aprox(mask_contours,height, width)
    yellow_image, yellow_aprox = aprox(yellow_contours,height, width)
    white_image, white_aprox = aprox(white_contours,height, width)
    
    #img = np.zeros((height, width, 3), np.uint8)
    img, yellow_line = fiting_line(ColorLine.yellow, yellow_aprox,height, width, img_orig)
    #cv2.imwrite("//home//userubuntu//gym-duckietown//rubbish//y_fline.png", y_fline) 
    img, white_line = fiting_line(ColorLine.white, white_aprox,height, width, img)
    angle = 0.0
    #cv2.imwrite("//home//userubuntu//gym-duckietown//rubbish//2lines"+str(step)+".png", img)
    #cv2.imwrite("//home//userubuntu//gym-duckietown//rubbish//img_orig"+str(step)+".png", img_orig)

    try:
        p1 = ((yellow_line[0] + white_line[0]) / 2)
        p2 = ((yellow_line[1] + white_line[1]) / 2)
        print(f"Результаты: p1={p1}, p2={p2}")
        angle = 0.0
        angle_radians = 0.0
        if (p1[0] != p2[0] and p1[1] != p2[1]):
            value = (p2[0] - p1[0])/(p2[1] - p1[1])
            #print(p2[1] - p1[1])
            #print(p2[0] - p1[0])
            #print(value)
            angle_radians = math.atan(value)
    # Преобразовываем Radians в градусы для удобства
        angle = math.degrees(angle_radians)
        cv2.line(img,(int(p1[0]),int(p1[1])),(int(p2[0]),int(p2[1])),(0,255,0),2)
        #cv2.line(img,,(0,255,0),2)
        #cv2.imwrite("//home//userubuntu//gym-duckietown//rubbish//w_fline.png", w_fline)
        
        # Настройки текста
        text = str(angle)
        position = (50, 100)  # Координаты (X, Y)
        font = cv2.FONT_HERSHEY_SIMPLEX  # Шрифт
        font_scale = 2  # Размер шрифта
        color = (0, 255, 0)  # Цвет (B, G, R)
        thickness = 2  # Толщина линий
        line_type = cv2.LINE_AA  # Антиалиасинг (сглаживание)

        # Добавляем текст на изображение
        cv2.putText(img, text, position, font, font_scale, color, thickness, line_type)

        cv2.imwrite("//home//userubuntu//gym-duckietown//rubbish//today//lines"+str(step)+".png", img)
        
        rainbow_count = draw_rainbow_cont(mask_contours,480,640)
        cw_img, cw_line = centerCnts(white_contours,height, width)
        cy_img, cy_line = centerCnts(yellow_contours,height, width)
        m_img, m_line = centerCnts(mask_contours,height, width)
    except TypeError as e:
    # Обработка ошибки
        print(f"Произошла ошибка: {e}")
        print(f"yellow_line: {yellow_line}")
        print(f"white_line: {white_line}")
        quit()
    
    #cx, cy = line_intersection(cw_line, cy_line)
    # Сохраняем результат
    #cv2.imwrite("//home//userubuntu//gym-duckietown//rubbish//cw_img.png", cw_img)
    #cv2.imwrite("//home//userubuntu//gym-duckietown//rubbish//cy_img.png", cy_img)
    #cv2.imwrite("//home//userubuntu//gym-duckietown//rubbish//m_img.png", m_img)
    #cv2.imwrite("//home//userubuntu//gym-duckietown//rubbish//rainbow_image.png", rainbow_image)
    #cv2.imwrite("//home//userubuntu//gym-duckietown//rubbish//white_image.png", white_image)
    #cv2.imwrite("//home//userubuntu//gym-duckietown//rubbish//yellow_image.png", yellow_image)
    #cv2.imwrite("//home//userubuntu//gym-duckietown//rubbish//rainbow_count.png", rainbow_count)
    #print(amount_yellow)
    return angle
    


env = DuckietownEnv(
	**{"seed": 128546,
	"map_name": "zigzag_dists", # где-то в репозитории можно эти карты настраивать
	"max_steps": 1,
	"camera_width": 640,
	"camera_height": 480,
	"accept_start_angle_deg": 40, #what
	"full_transparency": True,
	"distortion": True,
	"domain_rand": False
	}
)

done = False
obs = env.reset()
step = 0
 
# Параметры PID
pid_lateral = PIDController(kp=0.5, ki=0.01, kd=0.1)
#pid_angular = PIDController(kp=0.3, ki=0.0, kd=0.0)
pid_angular = PIDController(kp=0.24, ki=0.012, kd=0.009)
# pid_angular = PIDController(kp=0.23, ki=0.01, kd=0.015) - клонит влево
# pid_angular = PIDController(kp=0.25, ki=0.015, kd=0.006) - съехал на повороте направо

# Время обновления
dt = 0.01  # в секундах


    
while not done:
    # Положение робота
    #current_position = 0.2
    #desired_position = 0.0
    desired_angle = 0.0     # желаемый угол (в градусах)
    
    current_angle = moving_test(obs, step) # угол отклонения от направления движения (в градусах)
    step+=1

    with open('pid_test.txt', 'a+') as f:
       f.write(f"{step}  current_angle {current_angle}\n")
    #lateral_error = desired_position - current_position
    angular_error = desired_angle - current_angle

    #lateral_control = pid_lateral.compute(lateral_error, dt)
    angular_control = pid_angular.compute(angular_error, dt)

    # Управляющие скорости
    linear_speed = 1.0 #= max(0.1, 1.0 - abs(lateral_control))  # скорость снижается при большом отклонении
    angular_speed = 0 #-angular_control  # коррекция угловой скорости

    #with open('depend_speed_error.txt', 'a+') as f:
    #   f.write(f"{step} angular_speed {angular_speed} current_angle {current_angle} angular_error {angular_error}\n")
       
    action = [linear_speed, angular_speed]
    #action = [linear_speed, step*0.5]
    obs, rew, done, info = env.step(np.array(action))
    env.render()
    