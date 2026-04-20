import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time', default_value='false')

    # 1. Robot description + TF bridges
    robot_description = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('wally_bringup'),
                'launch', 'robot_description.launch.py')),
        launch_arguments={'use_sim_time': use_sim_time}.items(),
    )

    # 2. Livox MID-360 LiDAR driver
    lidar = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('wally_bringup'),
                'launch', 'lidar.launch.py')),
    )

    # 3. OAK-D depth camera driver
    camera = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('wally_bringup'),
                'launch', 'camera.launch.py')),
    )

    # 4. FAST-LIO (delayed 3s to let LiDAR initialize)
    fast_lio = TimerAction(
        period=3.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(
                        get_package_share_directory('fast_lio'),
                        'launch', 'mapping.launch.py')),
                launch_arguments={
                    'use_sim_time': use_sim_time,
                    'rviz': 'false',
                }.items(),
            ),
        ],
    )

    return LaunchDescription([
        declare_use_sim_time,
        robot_description,
        lidar,
        camera,
        fast_lio,
    ])
