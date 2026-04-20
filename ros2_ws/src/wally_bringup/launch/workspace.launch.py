import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')
    camera_model = LaunchConfiguration('camera_model')
    enable_perception = LaunchConfiguration('enable_perception')
    enable_nvblox = LaunchConfiguration('enable_nvblox')
    use_lidar_nvblox = LaunchConfiguration('use_lidar_nvblox')
    enable_teleop = LaunchConfiguration('enable_teleop')
    cmd_vel_topic = LaunchConfiguration('cmd_vel_topic')

    bringup_pkg = get_package_share_directory('wally_bringup')
    perception_pkg = get_package_share_directory('wally_perception')
    nvblox_pkg = get_package_share_directory('wally_nvblox')

    core_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bringup_pkg, 'launch', 'jetson.launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'camera_model': camera_model,
        }.items(),
    )

    segmentation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(perception_pkg, 'launch', 'segmentation.launch.py')
        ),
        condition=IfCondition(enable_perception),
    )

    nvblox_depth = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nvblox_pkg, 'launch', 'nvblox.launch.py')
        ),
        launch_arguments={'global_frame': 'map'}.items(),
        condition=IfCondition(
            PythonExpression([
                "'",
                enable_nvblox,
                "' == 'true' and '",
                use_lidar_nvblox,
                "' != 'true'",
            ])
        ),
    )

    nvblox_lidar = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nvblox_pkg, 'launch', 'nvblox_lidar.launch.py')
        ),
        launch_arguments={
            'global_frame': 'odom',
            'use_sim_time': use_sim_time,
        }.items(),
        condition=IfCondition(
            PythonExpression([
                "'",
                enable_nvblox,
                "' == 'true' and '",
                use_lidar_nvblox,
                "' == 'true'",
            ])
        ),
    )

    teleop = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bringup_pkg, 'launch', 'teleop.launch.py')
        ),
        launch_arguments={'cmd_vel_topic': cmd_vel_topic}.items(),
        condition=IfCondition(enable_teleop),
    )

    camera_model_hint = DeclareLaunchArgument(
        'camera_model',
        default_value='OAK-D-LR',
        description='Forwarded to camera bringup through wally_bringup/camera.launch.py',
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        camera_model_hint,
        DeclareLaunchArgument('enable_perception', default_value='true'),
        DeclareLaunchArgument('enable_nvblox', default_value='true'),
        DeclareLaunchArgument('use_lidar_nvblox', default_value='false'),
        DeclareLaunchArgument('enable_teleop', default_value='false'),
        DeclareLaunchArgument('cmd_vel_topic', default_value='cmd_vel'),
        core_bringup,
        segmentation,
        nvblox_depth,
        nvblox_lidar,
        teleop,
    ])
