import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    # Launch OAK-D with RealSense-compatible topic names so nvblox can consume
    # them directly without remapping:
    #   /camera/depth/image_rect_raw   (depth)
    #   /camera/depth/camera_info
    #   /camera/color/image_raw        (color → segmentation pipeline)
    #   /camera/color/camera_info
    #
    # parent_frame=oakd_frame attaches the camera TF tree to our URDF.
    # publish_tf_from_calibration=false lets our URDF own the static transform.

    camera_model = LaunchConfiguration('camera_model', default='OAK-D-LR')

    return LaunchDescription([
        DeclareLaunchArgument(
            'camera_model',
            default_value='OAK-D-LR',
            description='OAK-D camera model (OAK-D-LR, OAK-D, OAK-D-PRO, etc.)'),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(
                    get_package_share_directory('depthai_ros_driver'),
                    'launch', 'camera.launch.py')),
            launch_arguments={
                'name':                       'camera',
                'camera_model':               camera_model,
                'rs_compat':                  'true',   # gives /camera/depth/image_rect_raw
                'parent_frame':               'oakd_frame',
                'publish_tf_from_calibration':'false',  # URDF owns the static TF
                'rectify_rgb':                'true',
                'pointcloud.enable':          'false',
            }.items(),
        ),
    ])