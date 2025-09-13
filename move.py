import numpy as np

from pyglet.window import key

from gym_duckietown.envs import DuckietownEnv


def process_image(obs):
	pass # ничего не делать с картинкой

env = DuckietownEnv(
	**{"seed": 128546,
	"map_name": "loop_empty", # где-то в репозитории можно эти карты настраивать
	"max_steps": 100,
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

while not done:
	action = process_image(obs)
	action = [0.0,0.0]
	obs, rew, done, info = env.step(np.array(action))
	env.render()
