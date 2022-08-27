from ROAR.agent_module.agent import Agent
from pathlib import Path
from ROAR.control_module.pid_fast_controller import PIDFastController
from ROAR.planning_module.local_planner.simple_waypoint_following_local_planner_fast import \
    SimpleWaypointFollowingLocalPlanner
from ROAR.planning_module.behavior_planner.behavior_planner import BehaviorPlanner
from ROAR.planning_module.mission_planner.waypoint_following_mission_planner import WaypointFollowingMissionPlanner
from ROAR.utilities_module.data_structures_models import SensorsData
from ROAR.utilities_module.vehicle_models import VehicleControl, Vehicle
import logging
import numpy as np
import pickle

ep_num = 102
saved_q_table = f"qtables5/ep{ep_num}.pickle" # load existing q-table here

SPEED_INTERVAL_COUNT = 20 # set how many intervals you want between boundaries
SPEED_LOW_BOUNDARY = 60
SPEED_HIGH_BOUNDARY = 260
SPEED_INTERVAL_SIZE = (SPEED_HIGH_BOUNDARY - SPEED_LOW_BOUNDARY) / SPEED_INTERVAL_COUNT

ERROR_INTERVAL_COUNT = 20 # set how many intervals you want between boundaries
ERROR_LOW_BOUNDARY = 0
ERROR_HIGH_BOUNDARY = 1.0
ERROR_INTERVAL_SIZE = (ERROR_HIGH_BOUNDARY - ERROR_LOW_BOUNDARY) / ERROR_INTERVAL_COUNT

NUM_ACTIONS = 2 # 0 full throttle, 1 full brake

class QAgent(Agent):
    def __init__(self, target_speed=40, **kwargs):
        super().__init__(**kwargs)
        self.target_speed = target_speed
        self.logger = logging.getLogger("PID Agent")
        self.route_file_path = Path(self.agent_settings.waypoint_file_path)
        self.pid_controller = PIDFastController(agent=self, steering_boundary=(-1, 1), throttle_boundary=(0, 1))
        self.mission_planner = WaypointFollowingMissionPlanner(agent=self)
        # initiated right after mission plan

        with open(saved_q_table, "rb") as f:
            self.q_table = pickle.load(f)

        self.behavior_planner = BehaviorPlanner(agent=self)
        self.local_planner = SimpleWaypointFollowingLocalPlanner(
            agent=self,
            controller=self.pid_controller,
            mission_planner=self.mission_planner,
            behavior_planner=self.behavior_planner,
            closeness_threshold=1)
        self.logger.debug(
            f"Waypoint Following Agent Initiated. Reading f"
            f"rom {self.route_file_path.as_posix()}")

    def run_step(self, vehicle: Vehicle,
                 sensors_data: SensorsData) -> VehicleControl:
        super(QAgent, self).run_step(vehicle=vehicle,
                                       sensors_data=sensors_data)
        self.transform_history.append(self.vehicle.transform)
        # print(self.vehicle.transform, self.vehicle.velocity)
        if self.is_done:
            control = VehicleControl()
            self.logger.debug("Path Following Agent is Done. Idling.")
        else:
            action = self.get_action() # fetch action from trained q table
            control = self.local_planner.run_in_series(action)
        return control

    def get_obs(self):
        current_speed = Vehicle.get_speed(self.vehicle)
        error = self.pid_controller.obs_error
        obs = (current_speed, error)
        return obs

    def get_obs_state(self, obs):
        raw_speed, raw_error = obs[0], obs[1]
        speed_index, error_index = self.get_speed_index(raw_speed), self.get_error_index(raw_error)
        return (speed_index, error_index)
    
    # convert raw speed (0-300+) to speed index (0-19)
    def get_speed_index(self, raw_speed):
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
    def get_error_index(self, raw_error):
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

    def get_action(self):
        return np.argmax(self.q_table[(self.get_obs_state(self.get_obs()))])