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


obs = env.reset()
step = 0
dt = None
for name in ["delta_time", "dt", "delta_t"]:
    if hasattr(env.unwrapped, name):
        dt = getattr(env.unwrapped, name)
if dt is None and hasattr(env.unwrapped, "simulator"):
    for name in ["delta_time", "dt", "delta_t"]:
        if hasattr(env.unwrapped.simulator, name):
            dt = getattr(env.unwrapped.simulator, name)

print("dt =", dt)