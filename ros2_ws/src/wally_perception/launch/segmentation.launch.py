from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():

    unet_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('isaac_ros_unet'),
                'launch',
                'isaac_ros_unet_tensor_rt.launch.py'
            )
        ),
        launch_arguments={
            'engine_file_path': os.path.join(
                os.environ.get('ISAAC_ROS_WS', ''),
                'isaac_ros_assets/models/peoplesemsegnet/'
                'deployable_quantized_vanilla_unet_onnx_v2.0/1/model.plan'
            ),
            'input_binding_names': "['input_1:0']",
            'output_binding_names': "['argmax_1']",
            'network_output_type': 'argmax',
            'mask_width': '960',
            'mask_height': '544',
        }.items()
    )

    mask_converter = Node(
        package='wally_perception',
        executable='mask_converter_node',
        name='mask_converter_node',
        output='screen'
    )

    return LaunchDescription([
        unet_launch,
        mask_converter,
    ])