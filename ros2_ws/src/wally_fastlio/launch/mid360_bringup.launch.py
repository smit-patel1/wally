import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution

from launch_ros.actions import Node


def generate_launch_description():
    fast_lio_pkg = get_package_share_directory('wally_fastlio')
    livox_pkg = get_package_share_directory('livox_ros_driver2')

    default_config_path = os.path.join(fast_lio_pkg, 'config')
    default_rviz_cfg = os.path.join(fast_lio_pkg, 'rviz', 'fastlio_odom.rviz')
    livox_launch = os.path.join(livox_pkg, 'launch_ROS2', 'msg_MID360_launch.py')

    use_sim_time = LaunchConfiguration('use_sim_time')
    config_path = LaunchConfiguration('config_path')
    config_file = LaunchConfiguration('config_file')
    rviz_use = LaunchConfiguration('rviz')
    rviz_cfg = LaunchConfiguration('rviz_cfg')
    publish_map_to_odom = LaunchConfiguration('publish_map_to_odom')

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation clock if true',
    )
    declare_config_path = DeclareLaunchArgument(
        'config_path',
        default_value=default_config_path,
        description='FAST_LIO config directory',
    )
    declare_config_file = DeclareLaunchArgument(
        'config_file',
        default_value='mid360.yaml',
        description='FAST_LIO config filename',
    )
    declare_rviz = DeclareLaunchArgument(
        'rviz',
        default_value='true',
        description='Launch RViz2 if true',
    )
    declare_rviz_cfg = DeclareLaunchArgument(
        'rviz_cfg',
        default_value=default_rviz_cfg,
        description='RViz2 config file',
    )
    declare_publish_map_to_odom = DeclareLaunchArgument(
        'publish_map_to_odom',
        default_value='false',
        description='Publish static identity transform map -> odom',
    )

    livox_driver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(livox_launch),
    )

    fast_lio_node = Node(
        package='wally_fastlio',
        executable='fastlio_mapping',
        parameters=[
            PathJoinSubstitution([config_path, config_file]),
            {'use_sim_time': use_sim_time},
        ],
        output='screen',
    )

    delayed_fast_lio_node = TimerAction(
        period=2.0,
        actions=[fast_lio_node],
    )

    map_to_odom_static_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0', '0', '0', '0', '0', '0', 'map', 'odom'],
        condition=IfCondition(publish_map_to_odom),
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_cfg],
        condition=IfCondition(rviz_use),
    )

    ld = LaunchDescription()
    ld.add_action(declare_use_sim_time)
    ld.add_action(declare_config_path)
    ld.add_action(declare_config_file)
    ld.add_action(declare_rviz)
    ld.add_action(declare_rviz_cfg)
    ld.add_action(declare_publish_map_to_odom)

    ld.add_action(livox_driver)
    ld.add_action(delayed_fast_lio_node)
    ld.add_action(map_to_odom_static_tf)
    ld.add_action(rviz_node)

    return ld
