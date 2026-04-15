# SPDX-License-Identifier: Apache-2.0
# Wally nvblox: human-aware 3D reconstruction using NvbloxHumanNode.
#
# Pose comes from FAST-LIO via TF (odom -> base_link).
# Depth from a depth camera, segmentation mask from wally_perception.
#
# Based on the NVIDIA reference:
#   nvblox_examples_bringup/launch/perception/nvblox.launch.py
#   nvblox_examples_bringup/launch/realsense_example.launch.py

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import ComposableNodeContainer, Node
from launch_ros.descriptions import ComposableNode


def generate_launch_description():
    # ── Launch arguments ────────────────────────────────────────────────
    launch_args = [
        DeclareLaunchArgument(
            'depth_image_topic',
            default_value='/camera/depth/image_rect_raw',
            description='Depth image topic'),
        DeclareLaunchArgument(
            'depth_camera_info_topic',
            default_value='/camera/depth/camera_info',
            description='Depth camera info topic'),
        DeclareLaunchArgument(
            'color_image_topic',
            default_value='/segmentation/image_resized',
            description='Color image topic (resized to segmentation resolution)'),
        DeclareLaunchArgument(
            'color_camera_info_topic',
            default_value='/segmentation/camera_info_resized',
            description='Color camera info topic (resized to segmentation resolution)'),
        DeclareLaunchArgument(
            'segmentation_mask_topic',
            default_value='/unet/raw_segmentation_mask',
            description='Segmentation mask from UNet decoder'),
        DeclareLaunchArgument(
            'segmentation_camera_info_topic',
            default_value='/segmentation/camera_info_resized',
            description='Camera info for the segmentation mask'),

        # TF Frames
        DeclareLaunchArgument(
            'global_frame',
            default_value='map',
            description='Global frame published by Fast-LIO'),
        DeclareLaunchArgument(
            'pose_frame',
            default_value='base_link',
            description='Robot pose frame from TF tree'),
    ]

    depth_image_topic = LaunchConfiguration('depth_image_topic')
    depth_camera_info_topic = LaunchConfiguration('depth_camera_info_topic')
    color_image_topic = LaunchConfiguration('color_image_topic')
    color_camera_info_topic = LaunchConfiguration('color_camera_info_topic')
    segmentation_mask_topic = LaunchConfiguration('segmentation_mask_topic')
    segmentation_camera_info_topic = LaunchConfiguration('segmentation_camera_info_topic')
    global_frame = LaunchConfiguration('global_frame')
    pose_frame = LaunchConfiguration('pose_frame')

    # ── Config ──────────────────────────────────────────────────────────
    wally_nvblox_dir = get_package_share_directory('wally_nvblox')
    nvblox_config = os.path.join(wally_nvblox_dir, 'config', 'nvblox_wally.yaml')

    # ── NvbloxHumanNode ─────────────────────────────────────────────────
    # Topic remapping follows the realsense people-mode pattern from
    # nvblox_examples_bringup/launch/perception/nvblox.launch.py:
    #   get_realsense_remappings(NvbloxMode.people)
    nvblox_human_node = ComposableNode(
        name='nvblox_human_node',
        package='nvblox_ros',
        plugin='nvblox::NvbloxHumanNode',
        parameters=[nvblox_config, {
            'global_frame': global_frame,
            'pose_frame': pose_frame,
        }],
        remappings=[
            # Depth camera (camera_0)
            ('camera_0/depth/image', depth_image_topic),
            ('camera_0/depth/camera_info', depth_camera_info_topic),
            # Color camera (camera_0) — use the resized images that match
            # the segmentation resolution, same as the realsense example
            ('camera_0/color/image', color_image_topic),
            ('camera_0/color/camera_info', color_camera_info_topic),
            # Segmentation mask from wally_perception
            ('mask/image', segmentation_mask_topic),
            ('mask/camera_info', segmentation_camera_info_topic),
        ],
    )

    # ── Container ───────────────────────────────────────────────────────
    nvblox_container = ComposableNodeContainer(
        name='nvblox_container',
        namespace='',
        package='rclcpp_components',
        executable='component_container_mt',
        composable_node_descriptions=[nvblox_human_node],
        output='screen',
    )
    
    # This creates a "fake" odom frame that perfectly follows the map frame
    static_odom_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_transform_publisher_map_odom',
        arguments=['0', '0', '0', '0', '0', '0', 'map', 'odom']
    )

    return LaunchDescription(launch_args + [
        nvblox_container,
        static_odom_tf
    ])
