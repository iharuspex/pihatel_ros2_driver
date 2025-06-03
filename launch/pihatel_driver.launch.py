from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='pihatel_ros2_driver',
            executable='pihatel_serial_driver',
            # name='pihatel_ros2_driver',
            output='screen',
            parameters=[{ }]
        ),
    ])