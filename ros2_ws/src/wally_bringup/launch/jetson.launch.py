import os

from ament_index_python.packages import PackageNotFoundError, get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression


def _package_exists(package_name):
    try:
        get_package_share_directory(package_name)
        return True
    except PackageNotFoundError:
        return False


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')
    camera_model = LaunchConfiguration('camera_model')
    enable_camera = LaunchConfiguration('enable_camera')
    enable_perception = LaunchConfiguration('enable_perception')
    enable_nvblox = LaunchConfiguration('enable_nvblox')
    use_lidar_nvblox = LaunchConfiguration('use_lidar_nvblox')
    enable_teleop = LaunchConfiguration('enable_teleop')
    cmd_vel_topic = LaunchConfiguration('cmd_vel_topic')
    camera_driver_available = 'true' if _package_exists('depthai_ros_driver') else 'false'
    nvblox_available = 'true' if _package_exists('nvblox_ros') else 'false'

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time', default_value='false')
    declare_camera_model = DeclareLaunchArgument(
        'camera_model', default_value='OAK-D-LR')
    declare_enable_camera = DeclareLaunchArgument(
        'enable_camera', default_value='true')
    declare_enable_perception = DeclareLaunchArgument(
        'enable_perception', default_value='true')
    declare_enable_nvblox = DeclareLaunchArgument(
        'enable_nvblox', default_value='true')
    declare_use_lidar_nvblox = DeclareLaunchArgument(
        'use_lidar_nvblox', default_value='false')
    declare_enable_teleop = DeclareLaunchArgument(
        'enable_teleop', default_value='false')
    declare_cmd_vel_topic = DeclareLaunchArgument(
        'cmd_vel_topic', default_value='cmd_vel')

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
        launch_arguments={'camera_model': camera_model}.items(),
        condition=IfCondition(
            PythonExpression([
                "'",
                enable_camera,
                "' == 'true' and '",
                camera_driver_available,
                "' == 'true'",
            ])
        ),
    )

    # 4. FAST-LIO (delayed 3s to let LiDAR initialize)
    fast_lio = TimerAction(
        period=3.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(
                        get_package_share_directory('wally_fastlio'),
                        'launch', 'mapping.launch.py')),
                launch_arguments={
                    'use_sim_time': use_sim_time,
                    'rviz': 'false',
                }.items(),
            ),
        ],
    )

    # 5. Segmentation pipeline (optional)
    perception = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('wally_perception'),
                'launch', 'segmentation.launch.py')),
        condition=IfCondition(
            PythonExpression([
                "'",
                enable_perception,
                "' == 'true' and '",
                enable_camera,
                "' == 'true' and '",
                camera_driver_available,
                "' == 'true'",
            ])
        ),
    )

    # 6. Nvblox mapping (optional, depth mode by default)
    nvblox_depth = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('wally_nvblox'),
                'launch', 'nvblox.launch.py')),
        launch_arguments={'global_frame': 'map'}.items(),
        condition=IfCondition(
            PythonExpression([
                "'",
                enable_nvblox,
                "' == 'true' and '",
                nvblox_available,
                "' == 'true' and '",
                use_lidar_nvblox,
                "' != 'true' and '",
                enable_camera,
                "' == 'true' and '",
                camera_driver_available,
                "' == 'true'",
            ])
        ),
    )

    nvblox_lidar = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('wally_nvblox'),
                'launch', 'nvblox_lidar.launch.py')),
        launch_arguments={
            'global_frame': 'odom',
            'use_sim_time': use_sim_time,
        }.items(),
        condition=IfCondition(
            PythonExpression([
                "'",
                enable_nvblox,
                "' == 'true' and '",
                nvblox_available,
                "' == 'true' and ('",
                use_lidar_nvblox,
                "' == 'true' or '",
                enable_camera,
                "' != 'true' or '",
                camera_driver_available,
                "' != 'true')",
            ])
        ),
    )

    camera_fallback_notice = LogInfo(
        msg='depthai_ros_driver not found; camera/perception disabled and nvblox_lidar mode selected.',
        condition=IfCondition(
            PythonExpression([
                "'",
                enable_camera,
                "' == 'true' and '",
                camera_driver_available,
                "' != 'true'",
            ])
        ),
    )

    nvblox_missing_notice = LogInfo(
        msg='nvblox_ros not found; nvblox bringup is disabled.',
        condition=IfCondition(
            PythonExpression([
                "'",
                enable_nvblox,
                "' == 'true' and '",
                nvblox_available,
                "' != 'true'",
            ])
        ),
    )

    # 7. Keyboard teleop (optional)
    teleop = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('wally_bringup'),
                'launch', 'teleop.launch.py')),
        launch_arguments={'cmd_vel_topic': cmd_vel_topic}.items(),
        condition=IfCondition(enable_teleop),
    )

    return LaunchDescription([
        declare_use_sim_time,
        declare_camera_model,
        declare_enable_camera,
        declare_enable_perception,
        declare_enable_nvblox,
        declare_use_lidar_nvblox,
        declare_enable_teleop,
        declare_cmd_vel_topic,
        camera_fallback_notice,
        nvblox_missing_notice,
        robot_description,
        lidar,
        camera,
        fast_lio,
        perception,
        nvblox_depth,
        nvblox_lidar,
        teleop,
    ])
