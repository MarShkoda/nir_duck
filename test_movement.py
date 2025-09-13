import cv2
import enum
import math
import numpy as np
from scipy.linalg import solve_continuous_are
from scipy import stats

from pyglet.window import key
from gym_duckietown.envs import DuckietownEnv
from controllers.pid_controller import PIDController
from image_processing.line_processing import ImageLineProcessing
from image_processing.line_processing import ColorLine


    
env2 = DuckietownEnv(
    **{"seed": 128546,
    "map_name": "straight_road", 
    "max_steps": 1000,
    "camera_width": 640,
    "camera_height": 480,
    "accept_start_angle_deg": 30, #what
    "full_transparency": True,
    "distortion": True,
    "domain_rand": False
    }
)

env = DuckietownEnv(
    **{"seed": 128546,
    "map_name": "loop_empty", 
    "max_steps": 10000,
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
paused = False

pid_angular = PIDController(kp=9.5, ki=0.0, kd=0.0)  # подбери под dt=0.03
dt = 0.03

last_valid_angle = 0.0

def moving_test(obs, step, last_valid_angle):
    img = np.ascontiguousarray(obs)
    height, width = 480, 640
    yellow_image = ImageLineProcessing(img, width, height, ColorLine.yellow)
    white_image = ImageLineProcessing(img, width, height, ColorLine.white)
    y_slope, _, _ = yellow_image.process()
    w_slope, _, _ = white_image.process()

    angles = []
    if not np.isnan(y_slope):
        angles.append(math.atan(y_slope))
    if not np.isnan(w_slope):
        angles.append(math.atan(w_slope))

    if angles:
        current_angle = np.mean(angles)
        last_valid_angle = current_angle
    else:
        current_angle = last_valid_angle  # fallback
    return current_angle, last_valid_angle

with open('new_res.txt', 'a+') as f:
    while not done:
        desired_angle = 0.0
        current_angle, last_valid_angle = moving_test(obs, step, last_valid_angle)
        step += 1

        angular_error = current_angle - desired_angle
        angular_control = pid_angular.compute(angular_error, dt)

        linear_speed = 0.7
        angular_speed = angular_control  # без умножения на 20
        f.write(f"{step}  current_angle {current_angle} {angular_control}\n")

        action = [linear_speed, angular_speed]
        obs, rew, done, info = env.step(np.array(action))
        env.render()
