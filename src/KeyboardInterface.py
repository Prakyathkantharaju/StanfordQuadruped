import UDPComms
import numpy as np
import time
from src.State import BehaviorState, State
from src.Command import Command
from src.Utilities import deadband, clipped_first_order_filter





"""
    Mapping information
+---------------------------------------+------------------------------------------------------------+--------------+------------------+
|                  Type                 |                           Command                          |  PS4 command | Keyboard command |
+---------------------------------------+------------------------------------------------------------+--------------+------------------+
|    gait toggle (turn on trot gait)    |                         Trot_event                         |      R1      |         B        |
+---------------------------------------+------------------------------------------------------------+--------------+------------------+
| Hop toggle (turn on the hopping gait) |                          hop_event                         |       X      |         X        |
+---------------------------------------+------------------------------------------------------------+--------------+------------------+
|        activate toggle (start)        |                       activate_event                       |      L1      |         V        |
+---------------------------------------+------------------------------------------------------------+--------------+------------------+
|        forward velocity (xvel)        |                   horizontal_velocity[0]                   |      ly      |      W or up     |
+---------------------------------------+------------------------------------------------------------+--------------+------------------+
|                Yaw (y)                |                 yaw_rate = y * -max_y_rate                 |      rx      |         R        |
+---------------------------------------+------------------------------------------------------------+--------------+------------------+
|               Pitch (p)               |            pitch = current_pitch * m_dt * p_rate           |      ry      |         T        |
+---------------------------------------+------------------------------------------------------------+--------------+------------------+
|         lateral velcoty (yvel)        |                   horizontal_velocity[1]                   |      lx      |     E or side    |
+---------------------------------------+------------------------------------------------------------+--------------+------------------+
|          message_rate (m_dt)          |                             --                             | message_rate |         ?        |
+---------------------------------------+------------------------------------------------------------+--------------+------------------+
|            height_movement            | height = current_height - m_dt * z_speed * height_movement |     dpady    |         Y        |
+---------------------------------------+------------------------------------------------------------+--------------+------------------+
|             Roll_movement             |   roll = current_rool + m_dt * roll_speed * Roll_movement  |     dpadx    |         U        |
+---------------------------------------+------------------------------------------------------------+--------------+------------------+
"""





class KeyboardInterface:
    def __init__(
        self, config, udp_port=8835, udp_publisher_port = 8845,
    ):
        self.config = config
        self.previous_gait_toggle = 0
        self.previous_state = BehaviorState.REST
        self.previous_hop_toggle = 0
        self.previous_activate_toggle = 0

        self.message_rate = 50
        self.udp_handle = UDPComms.Subscriber(udp_port, timeout=0.3)
        self.udp_publisher = UDPComms.Publisher(udp_publisher_port)


    def get_command(self, state, do_print=False):
        try:
            msg = self.udp_handle.get()
            command = Command()

            ####### Handle discrete commands ########
            # Check if requesting a state transition to trotting, or from trotting to resting
            gait_toggle = msg["B"]
            command.trot_event = (gait_toggle == 1 and self.previous_gait_toggle == 0)

            # Check if requesting a state transition to hopping, from trotting or resting
            hop_toggle = msg["X"]
            command.hop_event = (hop_toggle == 1 and self.previous_hop_toggle == 0)

            activate_toggle = msg["V"]
            command.activate_event = (activate_toggle == 1 and self.previous_activate_toggle == 0)

            # Update previous values for toggles and state
            self.previous_gait_toggle = gait_toggle
            self.previous_hop_toggle = hop_toggle
            self.previous_activate_toggle = activate_toggle

            ####### Handle continuous commands ########
            x_vel = msg["W"] * self.config.max_x_velocity
            y_vel = msg["E"] * -self.config.max_y_velocity
            command.horizontal_velocity = np.array([x_vel, y_vel])
            command.yaw_rate = msg["R"] * -self.config.max_yaw_rate

            message_rate = msg["message_rate"]
            message_dt = 1.0 / message_rate

            pitch = msg["T"] * self.config.max_pitch
            deadbanded_pitch = deadband(
                pitch, self.config.pitch_deadband
            )
            pitch_rate = clipped_first_order_filter(
                state.pitch,
                deadbanded_pitch,
                self.config.max_pitch_rate,
                self.config.pitch_time_constant,
            )
            command.pitch = state.pitch + message_dt * pitch_rate

            height_movement = msg["R"]
            command.height = state.height - message_dt * self.config.z_speed * height_movement

            roll_movement = - msg["U"]
            command.roll = state.roll + message_dt * self.config.roll_speed * roll_movement

            return command

        except UDPComms.timeout:
            if do_print:
                print("UDP Timed out")
            return Command()


    def set_color(self, color):
        joystick_msg = {"ps4_color": color}
        #self.udp_publisher.send(joystick_msg)
        print(f"joy stick command {joystick_msg}")

