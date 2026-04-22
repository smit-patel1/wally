# SPDX-License-Identifier: Apache-2.0
# Wally perception: PeopleSemSegNet ShuffleSeg pipeline via Isaac ROS U-Net + Triton.
#
# Pipeline: ResizeNode -> DnnImageEncoderNode -> TritonNode -> UNetDecoderNode
#
# Based on the NVIDIA reference:
#   nvblox_examples_bringup/launch/perception/segmentation.launch.py
#   isaac_ros_unet/launch/isaac_ros_unet_triton.launch.py

import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode


# ShuffleSeg model constants (from nvblox_ros_python_utils.nvblox_constants)
NETWORK_IMAGE_WIDTH = 960
NETWORK_IMAGE_HEIGHT = 544

# Model repository — parent dir of the model directory
# (Triton expects model_repository_paths to point to the dir *containing* the model dir)
MODEL_REPOSITORY_PATH = os.path.join(
    os.environ.get('ISAAC_ROS_WS', '/workspaces/isaac_ros-dev'),
    'isaac_ros_assets', 'models', 'peoplesemsegnet')

MODEL_NAME = 'optimized_deployable_shuffleseg_unet_amr_v1.0'


def generate_launch_description():
    launch_args = [
        DeclareLaunchArgument(
            'input_image_topic',
            default_value='/camera/color/image_raw',
            description='Input color image topic'),
        DeclareLaunchArgument(
            'input_camera_info_topic',
            default_value='/camera/color/camera_info',
            description='Input camera info topic'),
        DeclareLaunchArgument(
            'input_image_width',
            default_value='640',
            description='Width of the camera input image'),
        DeclareLaunchArgument(
            'input_image_height',
            default_value='480',
            description='Height of the camera input image'),
    ]

    input_image_topic = LaunchConfiguration('input_image_topic')
    input_camera_info_topic = LaunchConfiguration('input_camera_info_topic')

    # ── 1. Resize to network resolution ─────────────────────────────────
    # Matches nvblox_examples segmentation.launch.py pattern
    resize_node = ComposableNode(
        name='segmentation_resize_node',
        package='isaac_ros_image_proc',
        plugin='nvidia::isaac_ros::image_proc::ResizeNode',
        parameters=[{
            'output_width': NETWORK_IMAGE_WIDTH,
            'output_height': NETWORK_IMAGE_HEIGHT,
            'keep_aspect_ratio': False,
            'input_qos': 'SENSOR_DATA',
        }],
        remappings=[
            ('image', input_image_topic),
            ('camera_info', input_camera_info_topic),
            ('resize/image', '/segmentation/image_resized'),
            ('resize/camera_info', '/segmentation/camera_info_resized'),
        ],
    )

    # ── 2. DNN Image Encoder ────────────────────────────────────────────
    # ShuffleSeg expects NHWC input, so use_planar_input=False
    # (skips the InterleavedToPlanar step in the encoder).
    # Input and network resolution are the same since we already resized.
    dnn_image_encoder_node = ComposableNode(
        name='dnn_image_encoder',
        package='isaac_ros_dnn_image_encoder',
        plugin='nvidia::isaac_ros::dnn_inference::DnnImageEncoderNode',
        parameters=[{
            'input_image_width': NETWORK_IMAGE_WIDTH,
            'input_image_height': NETWORK_IMAGE_HEIGHT,
            'network_image_width': NETWORK_IMAGE_WIDTH,
            'network_image_height': NETWORK_IMAGE_HEIGHT,
            'image_mean': [0.5, 0.5, 0.5],
            'image_stddev': [0.5, 0.5, 0.5],
        }],
        remappings=[
            ('image', '/segmentation/image_resized'),
            ('encoded_tensor', 'tensor_pub'),
        ],
    )

    # ── 3. Triton inference ─────────────────────────────────────────────
    triton_node = ComposableNode(
        name='triton_node',
        package='isaac_ros_triton',
        plugin='nvidia::isaac_ros::dnn_inference::TritonNode',
        parameters=[{
            'model_name': MODEL_NAME,
            'model_repository_paths': [MODEL_REPOSITORY_PATH],
            'max_batch_size': 0,
            'input_tensor_names': ['input_tensor'],
            'input_binding_names': ['input_2'],
            'input_tensor_formats': ['nitros_tensor_list_nchw_rgb_f32'],
            'output_tensor_names': ['output_tensor'],
            'output_binding_names': ['argmax_1'],
            'output_tensor_formats': ['nitros_tensor_list_nhwc_rgb_f32'],
        }],
    )

    # ── 4. UNet Decoder ─────────────────────────────────────────────────
    unet_decoder_node = ComposableNode(
        name='unet_decoder_node',
        package='isaac_ros_unet',
        plugin='nvidia::isaac_ros::unet::UNetDecoderNode',
        parameters=[{
            'network_output_type': 'argmax',
            'color_segmentation_mask_encoding': 'rgb8',
            'mask_width': NETWORK_IMAGE_WIDTH,
            'mask_height': NETWORK_IMAGE_HEIGHT,
            'color_palette': [
                0x556B2F, 0x800000, 0x008080, 0x000080, 0x9ACD32,
                0xFF0000, 0xFF8C00, 0xFFD700, 0x00FF00, 0xBA55D3,
                0x00FA9A, 0x00FFFF, 0x0000FF, 0xF08080, 0xFF00FF,
                0x1E90FF, 0xDDA0DD, 0xFF1493, 0x87CEFA, 0xFFDEAD,
            ],
        }],
    )

    # ── Composable container ────────────────────────────────────────────
    unet_container = ComposableNodeContainer(
        name='unet_container',
        namespace='',
        package='rclcpp_components',
        executable='component_container_mt',
        composable_node_descriptions=[
            resize_node,
            dnn_image_encoder_node,
            triton_node,
            unet_decoder_node,
        ],
        output='screen',
    )

    return LaunchDescription(launch_args + [unet_container])
