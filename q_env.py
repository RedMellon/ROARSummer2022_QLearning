from ROAR_Sim.carla_client.carla_runner import CarlaRunner
import pygame
import subprocess, sys
from ROAR.utilities_module.vehicle_models import Vehicle

from ROAR.agent_module.forward_only_agent import ForwardOnlyAgent
from ROAR.agent_module.pid_agent import PIDAgent
from ROAR.agent_module.pid_fast_agent import PIDFastAgent


class ROARQEnv:
    def __init__(self, params):
        self.carla_config = params["carla_config"]
        self.agent_config = params["agent_config"]
        self.npc_agent_class = params["npc_agent_class"]
        self.carla_runner = CarlaRunner(carla_settings=self.carla_config,
                                        agent_settings=self.agent_config,
                                        npc_agent_class=self.npc_agent_class)
        self.clock = None
        self.should_render = True  # choose to render here

    
    def reset(self):
        # keep trying to connect to server if it crashes
        while True:
            try:
                self.carla_runner.on_finish()
                self.carla_runner = CarlaRunner(carla_settings=self.carla_config,
                                                agent_settings=self.agent_config,
                                                npc_agent_class=self.npc_agent_class)
                vehicle = self.carla_runner.set_carla_world()
                self.agent = PIDFastAgent(vehicle=vehicle, agent_settings=self.agent_config) # change agent here
                
                self.agent.start_module_threads()
                self.clock = pygame.time.Clock()
                # self.start_simulation_time = self.world.carla_world.get_snapshot().elapsed_seconds
                # self.start_vehicle_position = self.agent.vehicle.transform.location.to_array()

                # get obs
                current_speed = Vehicle.get_speed(self.agent.vehicle)
                error = self.agent.pid_controller.obs_error
                obs = (current_speed, error)
                break
            except:
                print("Killing carla server...")
                p = subprocess.Popen(["powershell.exe", 
                            "C:\\Users\\gamev\\Desktop\\ROAR_Folders\\Summer2022\\ROAR_qlearning\\server_killer.ps1"], 
                            stdout=sys.stdout)
                p.communicate()
                print("Retrying to connect to server...")
        return obs
        
        # self.carla_runner.on_finish()
        # self.carla_runner = CarlaRunner(carla_settings=self.carla_config,
        #                                 agent_settings=self.agent_config,
        #                                 npc_agent_class=self.npc_agent_class)
        # vehicle = self.carla_runner.set_carla_world()
        # self.agent = PIDFastAgent(vehicle=vehicle, agent_settings=self.agent_config) # change agent here
        
        # self.agent.start_module_threads()
        # self.clock = pygame.time.Clock()
        # # self.start_simulation_time = self.world.carla_world.get_snapshot().elapsed_seconds
        # # self.start_vehicle_position = self.agent.vehicle.transform.location.to_array()

        # # get obs
        # current_speed = Vehicle.get_speed(self.agent.vehicle)
        # error = self.agent.pid_controller.obs_error
        # obs = (current_speed, error)
        # return obs


    def step(self, action):
        pygame.event.pump() # call this in while loop to prevent pygame from freezing
        self.clock.tick_busy_loop(60)
        self.carla_runner.world.tick(self.clock)
        
        if self.should_render:
            self.render()        

        # apply agent control

        if Vehicle.get_speed(self.agent.vehicle) < 10:
            action = 0 # override

        self.carla_runner.convert_data() # update vehicle and sensor data (from source to agent)
        agent_control = self.agent.run_step(vehicle=self.carla_runner.vehicle_state,
                                                sensors_data=self.carla_runner.sensor_data, action=action)
        carla_control = self.carla_runner.carla_bridge.convert_control_from_agent_to_source(agent_control)
        self.carla_runner.world.player.apply_control(carla_control)

        obs, reward, done = (0,0), 0, False
        
        # get obs
        current_speed = Vehicle.get_speed(self.agent.vehicle)
        error = self.agent.pid_controller.obs_error
        obs = (current_speed, error)
        
        # get reward
        had_collision = len(self.carla_runner.world.collision_sensor.get_collision_history()) > 0
        if had_collision:
            reward = -20 # big punishment for crashing
            # print("collision!!!")
            done = True # restart the episode
        elif current_speed == 0:
            # print("stopped")
            reward = -10
            # done = True
        elif action == 0:
            reward = 1 # reward for going full throttle
            # print("throttle")
        elif action == 1:
            reward = -1 # punishment for braking
            # print("brake")
        
        # end episode when completed 1 lap
        if len(self.agent.local_planner.way_points_queue) < 200:
            done = True
        
        return obs, reward, done
    
    def render(self):
        self.carla_runner.world.render(display=self.carla_runner.display)
        pygame.display.flip()