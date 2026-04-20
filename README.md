# Wally

Wally is an autonomous indoor robotics project focused on real-time navigation and 3D mapping in indoor environments. The system combines LiDAR+IMU odometry, GPU-accelerated 3D reconstruction, semantic segmentation for human-aware mapping, and autonomous navigation.

## Hardware

- **Compute:** NVIDIA Jetson AGX Orin 64GB (JetPack 6.1 / L4T r36.4)
- **LiDAR:** Livox Mid-360
- **IMU:** Built-in Livox Mid-360 IMU
- **Camera:** Depth camera (RealSense-compatible, topic remappings configurable)
- **Storage:** External SSD mounted at `/media/wally/ssd/`

## Architecture

```
Camera --> wally_perception (U-Net segmentation) --> mask --+
                                                            |
Camera depth -----------------------------------------------+--> wally_nvblox (3D reconstruction)
                                                                        |
LiDAR+IMU --> FAST-LIO (odometry + TF) -----------------------> Nav2 MPPI (navigation)
```

### Perception Pipeline (`wally_perception`)

Runs NVIDIA PeopleSemSegNet ShuffleSeg through the Isaac ROS U-Net pipeline:

1. **ResizeNode** -- scales camera image to 960x544 network resolution
2. **DnnImageEncoderNode** -- normalizes and encodes to tensor (NHWC)
3. **TritonNode** -- runs TensorRT inference (~1.7ms on Orin)
4. **UNetDecoderNode** -- decodes argmax output to segmentation mask

Output: `/unet/raw_segmentation_mask`

### 3D Reconstruction (`wally_nvblox`)

Runs `NvbloxHumanNode` in `human_with_static_tsdf` mode:

- Builds a static TSDF map from depth data
- Maintains a separate dynamic occupancy layer for detected humans
- Publishes 2D ESDF slices for Nav2 costmap integration
- Pose from FAST-LIO TF tree (`odom` -> `base_link`)
- Also supports an alternate LiDAR+segmentation mode (`nvblox_lidar.launch.py`) that consumes FAST-LIO `/cloud_registered`

### Odometry (`wally_fastlio`)

FAST-LIO provides LiDAR+IMU fused odometry, publishing the `odom` -> `base_link` transform.

### Navigation (`wally_navigation`)

Nav2 with MPPI controller for autonomous indoor navigation.

### Bringup (`wally_bringup`)

Launch orchestration for robot description, LiDAR, camera, and FAST-LIO (`jetson.launch.py`).

## Docker Setup

The Isaac ROS perception stack runs inside NVIDIA's `isaac_ros_dev-aarch64` Docker container (27GB, CUDA 12.6, ROS 2 Humble, TensorRT 10.3).

**Pre-built packages installed via apt** (from `isaac.download.nvidia.com/isaac-ros/release-3`):

- `ros-humble-nvblox-ros` (3.2.5)
- `ros-humble-isaac-ros-unet` (3.2.10)
- `ros-humble-isaac-ros-triton`, `ros-humble-isaac-ros-tensor-rt`
- `ros-humble-isaac-ros-dnn-image-encoder`, `ros-humble-isaac-ros-image-proc`
- Full NITROS stack and GXF extensions

**Models** (downloaded and converted at setup time):

- PeopleSemSegNet Vanilla U-Net -- 119MB ONNX, 87MB TensorRT plan
- PeopleSemSegNet ShuffleSeg AMR -- 3.8MB ONNX, 2.4MB TensorRT plan (1.7ms inference)

Model files live at: `/workspaces/isaac_ros-dev/isaac_ros_assets/models/peoplesemsegnet/`

### Container Launch

The container is launched via `isaac_ros_common/scripts/run_dev.sh`, which mounts the host workspace at `/workspaces/isaac_ros-dev/`.

### Known Fix: libnvdla_compiler.so

TensorRT's `libnvinfer_plugin.so.10` links against `libnvdla_compiler.so`, which is missing in the container image. The `scripts/fix_nvdla_compiler.sh` script extracts it from the `nvidia-l4t-dla-compiler` apt package and installs it at container startup. See `scripts/` for details.

## ROS 2 Packages

```
ros2_ws/src/
  wally_bringup/       # Robot description + sensor/odometry bringup
  wally_fastlio/       # Integrated FAST-LIO package
  livox_ros_driver2/   # Integrated Livox Mid-360 ROS 2 driver
  wally_navigation/    # Nav2 launch and config (WIP)
  wally_nvblox/        # Nvblox human-aware 3D reconstruction
  wally_perception/    # Isaac ROS U-Net segmentation pipeline
```

### Building

Inside the Isaac ROS container:

```bash
source /opt/ros/humble/setup.bash
cd /workspaces/isaac_ros-dev/ros2_ws
colcon build --symlink-install --packages-select wally_perception wally_nvblox
source install/setup.bash
```

### Running

```bash
# Terminal 1: Segmentation
ros2 launch wally_perception segmentation.launch.py

# Terminal 2: Nvblox (default depth+segmentation mode)
ros2 launch wally_nvblox nvblox.launch.py

# Optional: Nvblox LiDAR+segmentation mode (uses FAST-LIO /cloud_registered)
ros2 launch wally_nvblox nvblox_lidar.launch.py
```

## Topic Map

| Topic | Type | Source |
|-------|------|--------|
| `/camera/color/image_raw` | sensor_msgs/Image | Camera driver |
| `/camera/color/camera_info` | sensor_msgs/CameraInfo | Camera driver |
| `/camera/depth/image_rect_raw` | sensor_msgs/Image | Camera driver |
| `/camera/depth/camera_info` | sensor_msgs/CameraInfo | Camera driver |
| `/segmentation/image_resized` | sensor_msgs/Image | wally_perception ResizeNode |
| `/segmentation/camera_info_resized` | sensor_msgs/CameraInfo | wally_perception ResizeNode |
| `/unet/raw_segmentation_mask` | sensor_msgs/Image | wally_perception UNetDecoder |
| `/cloud_registered` | sensor_msgs/PointCloud2 | wally_fastlio (for `nvblox_lidar.launch.py`) |
| `/nvblox_node/mesh` | nvblox_msgs/Mesh | wally_nvblox |
| `/nvblox_node/static_esdf_pointcloud` | sensor_msgs/PointCloud2 | wally_nvblox |

## Directory Layout

```
wally/
  README.md
  .gitignore
  configs/           # Configuration files for subsystems
    fast_lio/
    nav2/
    nvblox/
  ros2_ws/           # ROS 2 workspace (source packages)
  scripts/           # Host-side setup and fix scripts
  docker/            # Cloned NVIDIA Isaac ROS repos (gitignored)
  archive/           # Old workspace experiments
```
