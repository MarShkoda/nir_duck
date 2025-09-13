import cv2
import enum
import math
import numpy as np
from scipy import stats

@enum.unique
class ColorLine(enum.Enum):
    yellow = 2
    white = 1
    
class ImageLineProcessing:
    def __init__(self, image, width, height, color):
        self.image = cv2.GaussianBlur(image, (9,9), 0)
        #self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV)
        self.width = width
        self.height = height
        self.color = color
        if self.color == ColorLine.yellow:
            lower_blue = np.array([190, 190, 20], dtype=np.uint8)
            upper_blue = np.array([250, 250, 150], dtype=np.uint8)
            self.color_mask = cv2.inRange(self.image, lower_blue, upper_blue)
        else:
            lower_white = np.array([180, 180, 180], dtype=np.uint8)
            upper_white = np.array([255, 255, 255], dtype=np.uint8)
            self.color_mask = cv2.inRange(self.image, lower_white, upper_white)
        cv2.imwrite("color_mask.png", self.color_mask)

 
    def region_selection(self):
        mask = np.zeros_like(self.color_mask) 
        
        if len(self.color_mask.shape) > 2:
            channel_count = self.color_mask.shape[2]
            ignore_mask_color = (255,) * channel_count
        else:
            ignore_mask_color = 255
        rows, cols = self.color_mask.shape[:2]
        left_border = 0 if (ColorLine.yellow == self.color) else 0.4
        right_border = 0.5 if (ColorLine.yellow == self.color) else 1

        bottom_left = [cols * left_border, rows * 0.78]
        bottom_right = [cols * right_border, rows * 0.78]
        top_left = [cols * left_border, rows * 0.55]
        top_right= [cols * right_border, rows * 0.55]
        vertices = np.array([[bottom_left, top_left, top_right, bottom_right]], dtype=np.int32)
        cv2.fillPoly(mask, vertices, ignore_mask_color)
        masked_image = cv2.bitwise_and(self.color_mask, mask)
        #_, masked_gray = cv2.threshold(masked, 120, 255, cv2.THRESH_BINARY)
        cv2.imwrite("//home//userubuntu//gym-duckietown//rubbish//1mask.png", masked_image)
        return masked_image
        
    def approx_countours(self, cnts):
        approx_cnt = []
        img = np.zeros((self.height, self.width, 3), np.uint8)
        for cnt in cnts:
            if (cv2.arcLength(cnt, True)):
                approx = cv2.approxPolyDP(cnt, 0.05 * cv2.arcLength(cnt, True), True)
                approx_cnt.append(approx)
                if len(approx) < 3:
                    cv2.drawContours(img, [approx], 0, (255, 255, 255), -1)
                if len(approx) == 3:
                    cv2.drawContours(img, [approx], 0, 255, -1)
                elif len(approx) == 4:
                    cv2.drawContours(img, [approx], 0, (0, 255, 0), -1)
                elif len(approx) == 5:
                    cv2.drawContours(img, [approx], 0, (0, 0, 255), -1)
                elif len(approx) == 6:
                    cv2.drawContours(img, [approx], 0, (255, 255, 0), -1)
        #cv2.imwrite("//home//userubuntu//gym-duckietown//rubbish//2approx"+str(self.color)+".png", img)
        #print('approx', approx)
        return approx_cnt
        
    def mnk(self, contours):
        all_points = []

        for cnt in contours:
            cnt = cnt.reshape(-1, 2)
            all_points.append(cnt)

        if len(all_points) == 0:
            print("Нет валидных контуров для обработки.")
            return np.nan

        all_points = np.vstack(all_points)  # shape: (N, 2)
        x = all_points[:, 0]
        y = all_points[:, 1]
        res = stats.linregress(x, y)
        print("self.color", self.color, " res ", res.slope)
        return res.slope
        
    def process(self):
        masked = self.region_selection()
        _, thresh = cv2.threshold(masked, 120, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        approx_cnts = self.approx_countours(contours)
        angle_line = self.mnk(approx_cnts)
        #print('angle_line ', angle_line)
        return angle_line


img = cv2.imread('test.png')
height = 480
width = 640
yellow_image = ImageLineProcessing(img, width, height, ColorLine.yellow)
        