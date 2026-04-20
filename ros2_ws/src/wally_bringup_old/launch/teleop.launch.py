from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    cmd_vel_topic = LaunchConfiguration('cmd_vel_topic')

    return LaunchDescription([
        DeclareLaunchArgument(
            'cmd_vel_topic', default_value='cmd_vel',
            description='Topic to publish velocity commands on'),

        Node(
            package='teleop_twist_keyboard',
            executable='teleop_twist_keyboard',
            name='teleop_twist_keyboard',
            output='screen',
            prefix='xterm -e',
            remappings=[('cmd_vel', cmd_vel_topic)],
            parameters=[{
                'speed': 0.4,
                'turn': 1.0,
                'repeat_rate': 10.0,
                'key_timeout': 0.3,
            }],
        ),
    ])
