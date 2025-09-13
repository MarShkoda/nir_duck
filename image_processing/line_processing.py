import cv2
import enum
import math
import numpy as np
from scipy import stats
from sklearn.decomposition import PCA

@enum.unique
class ColorLine(enum.Enum):
    yellow = 2
    white = 1
    
class ImageLineProcessing:
    step = 0
    def __init__(self, image, width, height, color):
        self.image = cv2.GaussianBlur(image, (9,9), 0)
        self.width = width
        self.height = height
        self.color = color
        if self.color == ColorLine.yellow:
            ImageLineProcessing.step+=1
            lower_blue = np.array([175, 165, 20], dtype=np.uint8)
            upper_blue = np.array([250, 250, 150], dtype=np.uint8)
            self.color_mask = cv2.inRange(self.image, lower_blue, upper_blue)
        else:
            lower_white = np.array([160, 160, 160], dtype=np.uint8)
            upper_white = np.array([255, 255, 255], dtype=np.uint8)
            self.color_mask = cv2.inRange(self.image, lower_white, upper_white)
        # cv2.imwrite("//home//userubuntu//gym-duckietown//rubbish//0color"+str(self.color)+".png", self.color_mask)
        #cv2.imwrite("//home//userubuntu//gym-duckietown//rubbish//debug_bgr.png", image)  # исходник
        #filename = f"//home//userubuntu//gym-duckietown//test//{ImageLineProcessing.step}.png"
        #cv2.imwrite(filename, self.image)  # HSV обратно
        #cv2.imwrite("//home//userubuntu//gym-duckietown//rubbish//debug_mask.png", self.color_mask)  # маска по цвету        
 
    def region_selection(self):
        mask = np.zeros_like(self.color_mask) 
        
        if len(self.color_mask.shape) > 2:
            channel_count = self.color_mask.shape[2]
            ignore_mask_color = (255,) * channel_count
        else:
            ignore_mask_color = 255
        rows, cols = self.color_mask.shape[:2]
        #left_border = 0# if (ColorLine.yellow == self.color) else 0.4
        left_border = 0 if (ColorLine.yellow == self.color) else 0.4
        #right_border = 1#0.6 if (ColorLine.yellow == self.color) else 1
        right_border = 0.6 if (ColorLine.yellow == self.color) else 1

        bottom_left = [cols * left_border, rows * 0.78]
        bottom_right = [cols * right_border, rows * 0.78]
        top_left = [cols * left_border, rows * 0.55]
        top_right= [cols * right_border, rows * 0.55]
        vertices = np.array([[bottom_left, top_left, top_right, bottom_right]], dtype=np.int32)
        cv2.fillPoly(mask, vertices, ignore_mask_color)
        masked_image = cv2.bitwise_and(self.color_mask, mask)
        #cv2.imwrite("//home//userubuntu//gym-duckietown//rubbish//1mask.png", masked_image)
        return masked_image
        
    def approx_countours(self, cnts):
        approx_cnt = []
        img = np.zeros((self.height, self.width, 3), np.uint8)
        for cnt in cnts:
            if (cv2.arcLength(cnt, True)):
                approx = cnt #cv2.approxPolyDP(cnt, 0.05 * cv2.arcLength(cnt, True), True)
                approx_cnt.append(approx)
                if len(approx) < 3:
                    cv2.drawContours(img, [approx], 0, (255, 255, 255), -1)
                if len(approx) == 3:
                    cv2.drawContours(img, [approx], 0, 255, -1)
                elif len(approx) == 4:
                    cv2.drawContours(img, [approx], 0, (0, 255, 0), -1)
                elif len(approx) == 5:
                    cv2.drawContours(img, [approx], 0, (0, 0, 255), -1)
                else:
                    cv2.drawContours(img, [approx], 0, (255, 255, 0), -1)
        cv2.imwrite("//home//userubuntu//gym-duckietown//rubbish//2approx"+str(self.color)+".png", img)
        return approx_cnt
        
    def mnk(self, contours):
        all_points = []

        for cnt in contours:
            cnt = cnt.reshape(-1, 2)
            all_points.append(cnt)

        if len(all_points) == 0:
            #print("Нет валидных контуров для обработки.")
            return np.nan, -1, -1

        all_points = np.vstack(all_points)  # shape: (N, 2)

        rect = cv2.minAreaRect(all_points)
        box = cv2.boxPoints(rect)
        box = np.int0(box)
        
        
        # сртировка по Y
        sorted_box = sorted(box, key=lambda p: p[1])
        bottom_side = sorted_box[:2]
        top_side = sorted_box[-2:]

        bottom_mid = ((bottom_side[0][0] + bottom_side[1][0]) / 2,
                      (bottom_side[0][1] + bottom_side[1][1]) / 2)
        top_mid = ((top_side[0][0] + top_side[1][0]) / 2,
                   (top_side[0][1] + top_side[1][1]) / 2)

        [vx, vy, x, y] = cv2.fitLine(all_points, cv2.DIST_L2, 0, 0.01, 0.01)
        lefty = int((-x*vy/vx)+ y)
        righty = int(((self.width-x)*vy/vx)+y)
        image = np.zeros((self.height, self.width, 3), np.uint8)
        if self.color == ColorLine.yellow:
            line_color = (0, 255, 0)
        else:
            line_color = (0, 255, 255)

        #cv2.line(image, (self.width, righty), (0, lefty), (0, 255, 0), 2)
        cv2.line(image,
                 (int(bottom_mid[0]), int(bottom_mid[1])),
                 (int(top_mid[0]), int(top_mid[1])),
                 line_color, 2)
        M = cv2.moments(all_points)
        cx = 0#int(M['m10']/M['m00'])
        cy = 0#int(M['m01']/M['m00'])
        cv2.circle(image, (cx, cy), 5, (255,0,255), 5)
        cv2.drawContours(image,[box],0,(0,0,255),2)


        #cv2.imwrite("//home//userubuntu//gym-duckietown//rubbish//line"+str(self.color)+".png", image)

        if (top_mid[0] - bottom_mid[0]) == 0:
            return np.nan, -1, -1
        slope = (top_mid[1] - bottom_mid[1]) / (top_mid[0] - bottom_mid[0])
        return slope, cx, cy
        #return 0.0
        
    def line_fit_edges(self, blur):
        edges = cv2.Canny(blur, 30, 100)  # ниже пороги
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi/180,
            threshold=20,       # было 50
            minLineLength=10,   # было 30
            maxLineGap=20       # было 10
        )
        angles = []
        image = np.zeros((self.height, self.width, 3), np.uint8)
        #print('------')
        eps = 1e-6
        output = self.image.copy()
        output[edges > 0] = [0, 0, 255]   # все пиксели границ красные
        edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                angle = np.arctan2(y2 - y1, x2 - x1)
                #print('angle ', angle)
                #if -math.pi < angle < -math.pi+2/math.pi or math.pi-2/math.pi < angle < math.pi: # горизонтальные
                #    continue
                #if abs(angle) < eps:
                #    continue
                cv2.line(output, (x1, y1), (x2, y2), (0, 255, 255), 2)
                angles.append(angle)
        #print('------')
        #cv2.imwrite("//home//userubuntu//gym-duckietown//rubbish//edges"+str(self.color)+".png", edges)
        #cv2.imwrite("//home//userubuntu//gym-duckietown//rubbish//line"+str(self.color)+".png", image)
        #cv2.imwrite("line"+str(self.color)+".png", self.image)
        cv2.imwrite("line"+str(self.color)+".png", output)
        if angles:
            avg_angle = np.mean(angles)
            #print('mean ', avg_angle)
        else:
            avg_angle = np.nan
        return avg_angle

    
    
    
    
    
    def pca_line_fit(self, contours):
        all_points = []

        for cnt in contours:
            cnt = cnt.reshape(-1, 2)
            all_points.append(cnt)

        if len(all_points) == 0:
            print("Нет валидных контуров для обработки.")
            return np.nan

        all_points = np.vstack(all_points)  # shape: (N, 2)
        
        mean = np.mean(all_points, axis=0)
        centered_points = all_points - mean

        pca = PCA(n_components=1)
        pca.fit(centered_points)
        
        direction = pca.components_[0]
        slope = direction[1] / direction[0]
        
        x0, y0 = mean
        intercept = y0 - slope * x0
        
        x1 = 0
        y1 = int(intercept + slope * x1)
        
        x2 = self.width - 1
        y2 = int(intercept + slope * x2)
        
        image = np.zeros((self.height, self.width, 3), np.uint8)
        if self.color == ColorLine.yellow:
            line_color = (0, 255, 0)
        else:
            line_color = (0, 255, 255)
        
        cv2.line(image, (x1, y1), (x2, y2), line_color, 2)
        #cv2.imwrite("//home//userubuntu//gym-duckietown//rubbish//line"+str(self.color)+".png", image)
        #cv2.imwrite("line.png", image)
        
        return slope
    
    def process(self):
        masked = self.region_selection()
        _, thresh = cv2.threshold(masked, 120, 255, cv2.THRESH_BINARY)
        #cv2.imwrite("//home//userubuntu//gym-duckietown//rubbish//2thresh.png", thresh)
        #contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        #approx_cnts = self.approx_countours(contours)
        #angle_line = self.mnk(approx_cnts)
        angle_line = self.line_fit_edges(thresh)
        return angle_line
