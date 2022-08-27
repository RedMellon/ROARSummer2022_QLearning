from pathlib import Path
import logging
import numpy as np
import pickle
import os

from ROAR.configurations.configuration import Configuration as AgentConfig
from ROAR_Sim.configurations.configuration import Configuration as CarlaConfig
from ROAR.agent_module.pure_pursuit_agent import PurePursuitAgent
from q_env import ROARQEnv


NUM_RUNNING_EPISODES = 30
dir_path = os.listdir("qtables5")
num_files = len(dir_path)
saved_q_table = ""
saved_q_table = f"qtables5/ep{num_files}.pickle"

# NUM_EPISODES = 100 # to run one episode, make this same as starting episode
# STARTING_EPISODE = 60
# saved_q_table = ""
# saved_q_table = f"qtables5/ep{STARTING_EPISODE-1}.pickle" # load existing q-table here

SPEED_INTERVAL_COUNT = 20 # set how many intervals you want between boundaries
SPEED_LOW_BOUNDARY = 60
SPEED_HIGH_BOUNDARY = 260
SPEED_INTERVAL_SIZE = (SPEED_HIGH_BOUNDARY - SPEED_LOW_BOUNDARY) / SPEED_INTERVAL_COUNT

ERROR_INTERVAL_COUNT = 20 # set how many intervals you want between boundaries
ERROR_LOW_BOUNDARY = 0
ERROR_HIGH_BOUNDARY = 1.0
ERROR_INTERVAL_SIZE = (ERROR_HIGH_BOUNDARY - ERROR_LOW_BOUNDARY) / ERROR_INTERVAL_COUNT

NUM_ACTIONS = 2 # 0 full throttle, 1 full brake

LEARNING_RATE = 0.2
DISCOUNT = 0.95


def main():
    
    # get configurations
    log = logging.getLogger(__name__)
    agent_config = AgentConfig.parse_file(Path("./ROAR/configurations/carla/carla_agent_configuration.json"))
    carla_config = CarlaConfig.parse_file(Path("./ROAR_Sim/configurations/configuration.json"))
    params = {
        "agent_config": agent_config,
        "carla_config": carla_config,
        "npc_agent_class": PurePursuitAgent
    }

    # create environment
    env = ROARQEnv(params)

    # load an existing q table (q_table[speed][error][action])
    if saved_q_table != "":
        with open(saved_q_table, "rb") as f:
            q_table = pickle.load(f)
    # create a new q table
    else:
        q_table = np.random.uniform(low=0, high=0, size=([SPEED_INTERVAL_COUNT,ERROR_INTERVAL_COUNT] + [NUM_ACTIONS])) # 20x20x2 table
        # for i in range(20):
        #     for ii in range(20):
        #         q_table[i][ii][0] = 0.1 # give prio to action 0 in the beginning

    # run specified number of training episodes
    # for ep_num in range(STARTING_EPISODE, NUM_EPISODES+1):
    ep_num = num_files + 1
    for count in range(NUM_RUNNING_EPISODES):

        # keep trying to connect to server
        # while True:
        #     try:
        #         obs = env.reset()
        #         break
        #     except:
        #         print("Retrying to connect to server...")
        obs = env.reset()

        done = False
        log.debug("RUNNING: episode " + str(ep_num))
        while not done:
            # format obs data
            obs_state = get_obs_state(obs)
            
            # get action by looking up max q value in q table
            action = np.argmax(q_table[(obs_state)])
            # print(q_table[(obs_state)])
            
            # step into env w/ chosen action
            obs, reward, done = env.step(action)

            # get q_data
            new_obs_state = get_obs_state(obs)
            max_future_q = np.max(q_table[new_obs_state])
            current_q = q_table[obs_state + (action,)]
            
            # almighty q-equation!
            new_q = (1 - LEARNING_RATE) * current_q + LEARNING_RATE * (reward + DISCOUNT * max_future_q)

            # update q value w/ new q
            q_table[obs_state + (action,)] = new_q
            # print(new_q)
            # print("Action: " + str(action), "Current q: " + str(current_q), "Updated q: " + str(new_q))
    
        # save q-table after each episode
        path = Path(f"qtables5\ep{ep_num}.pickle")
        if path.is_file():
            env.carla_runner.on_finish()
            raise Exception("Q-table with same name already exists, please don't overwrite it! Stopping program.")
        with open(f"qtables5\ep{ep_num}.pickle", "wb") as f:
            pickle.dump(q_table, f)
            ep_num += 1

    # close carla environment
    env.carla_runner.on_finish()
    print("done training!")

def get_obs_state(obs):
    raw_speed, raw_error = obs[0], obs[1]
    speed_index, error_index = get_speed_index(raw_speed), get_error_index(raw_error)
    return (speed_index, error_index)


# convert raw speed (0-300+) to speed index (0-19)
def get_speed_index(raw_speed):
        # bound between 60 and 259 (treat anything below 60 as part of 60-70 interval)
        x = min(max(raw_speed, SPEED_LOW_BOUNDARY), SPEED_HIGH_BOUNDARY - 1) # max is 259
        # modify range to fit boundary
        x = x - SPEED_LOW_BOUNDARY # low_boundary: 60 for speed
        # allocate to specific interval
        x = x / SPEED_INTERVAL_SIZE # interval size: 10 for speed
        # round
        x = int(x)
        # return
        index = x
        return index


# convert raw error (0-1.0+) to error index (0-19)
def get_error_index(raw_error):
        # bound between 0 and 1.0
        x = min(max(raw_error, ERROR_LOW_BOUNDARY), ERROR_HIGH_BOUNDARY - 0.01) # max is 0.99
        # modify range to fit boundary
        x = x - ERROR_LOW_BOUNDARY
        # allocate to specific interval
        x = x / ERROR_INTERVAL_SIZE
        # round
        x = int(x)
        # return
        index = x
        return index


if __name__ == "__main__":
    logging.basicConfig(format='%(levelname)s - %(asctime)s - %(name)s '
                               '- %(message)s',
                        datefmt="%H:%M:%S",
                        level=logging.DEBUG)
    logging.getLogger(" streaming client").setLevel(logging.WARNING)
    import warnings

    warnings.filterwarnings("ignore", module="carla")

    warnings.filterwarnings("ignore", module="carla")
    main()