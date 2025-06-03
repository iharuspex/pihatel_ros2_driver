import rclpy

from libpihatel_ros2_driver.Controller import Controller
from libpihatel_ros2_driver.SerialPort import SerialManager
from libpihatel_ros2_driver.SettingsComnav import SettingsComnav
from libpihatel_ros2_driver import Parser
from libpihatel_ros2_driver import Buzzer

import time

def main():
    rclpy.init()

    controller = Controller()
    serial_port = SerialManager()
    settings_commnav = SettingsComnav()
    ascii_parser = Parser.ParserDataASCII()
    binary_parser = Parser.ParserDataBinary()
    buzzer = Buzzer.Buzzer()

    controller.set_class_reference(serial_port, ascii_parser, settings_commnav, buzzer)

    # TODO move this to the launch configuration
    params = {
        'port_name': '/dev/ttyS0',
        'coords_input': [0.0, 0.0, 0.0],
        'coords_status': "auto",
        'pps_output': True,

        'entry_interval_rtcm': 1,
        'hardware_checkbox1': False,
        'hardware_checkbox2': False,
        'hardware_checkbox3': False,

        'work_buzzer': True
    }

    controller.start_controller(params)
    frame_id = controller.get_frame_id()

    while rclpy.ok():
        controller.publish(frame_id)
        time.sleep(2)


if __name__ == '__main__':
    main()
