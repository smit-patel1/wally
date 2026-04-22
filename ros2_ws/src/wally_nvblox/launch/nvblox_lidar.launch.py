# SPDX-License-Identifier: Apache-2.0
# Wally nvblox: legacy LiDAR + segmentation mode using NvbloxNode.
#
# This launch keeps the older /cloud_registered integration path available
# while the default depth+segmentation mode remains in nvblox.launch.py.

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode


def generate_launch_description():
    launch_args = [
        DeclareLaunchArgument(
            'pointcloud_topic',
            default_value='/cloud_registered',
            description='Input LiDAR pointcloud topic'),
        DeclareLaunchArgument(
            'segmentation_mask_topic',
            default_value='/unet/raw_segmentation_mask',
            description='Segmentation mask from UNet decoder'),
        DeclareLaunchArgument(
            'segmentation_camera_info_topic',
            default_value='/segmentation/camera_info_resized',
            description='Camera info for the segmentation mask'),
        DeclareLaunchArgument(
            'global_frame',
            default_value='odom',
            description='Global frame used by nvblox for map integration'),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'),
    ]

    pointcloud_topic = LaunchConfiguration('pointcloud_topic')
    segmentation_mask_topic = LaunchConfiguration('segmentation_mask_topic')
    segmentation_camera_info_topic = LaunchConfiguration('segmentation_camera_info_topic')
    global_frame = LaunchConfiguration('global_frame')
    use_sim_time = LaunchConfiguration('use_sim_time')

    wally_nvblox_dir = get_package_share_directory('wally_nvblox')
    nvblox_config = os.path.join(wally_nvblox_dir, 'config', 'nvblox_lidar.yaml')

    nvblox_node = ComposableNode(
        name='nvblox_node',
        package='nvblox_ros',
        plugin='nvblox::NvbloxNode',
        parameters=[nvblox_config, {
            'global_frame': global_frame,
            'use_sim_time': use_sim_time,
        }],
        remappings=[
            ('pointcloud', pointcloud_topic),
            ('camera_0/mask/image', segmentation_mask_topic),
            ('camera_0/mask/camera_info', segmentation_camera_info_topic),
        ],
    )

    nvblox_container = ComposableNodeContainer(
        name='nvblox_lidar_container',
        namespace='',
        package='rclcpp_components',
        executable='component_container_mt',
        composable_node_descriptions=[nvblox_node],
        output='screen',
    )

    return LaunchDescription(launch_args + [nvblox_container])
