# Launch Guide (Individual Packages) + Current Issues

This document shows how to launch each package individually and lists all launch files currently in this repo.

ALSO REMOVE ALL THE DUPLICATE FILES


## 1) Environment setup

From repo root:

```bash
source /opt/ros/humble/setup.bash
source ~/wally/install/setup.bash
```

## 2) Launch packages individually

### Core robot (host)

```bash
# Robot description + TF bridges
ros2 launch wally_bringup robot_description.launch.py

# Livox LiDAR
ros2 launch wally_bringup lidar.launch.py

# FAST-LIO mapping
ros2 launch wally_fastlio mapping.launch.py
```

### Camera (direct package, not bringup)

```bash
ros2 launch depthai_ros_driver camera.launch.py \
  name:=camera \
  camera_model:=OAK-D-LR \
  rs_compat:=true \
  parent_frame:=oakd_frame \
  publish_tf_from_calibration:=false \
  rectify_rgb:=true \
  pointcloud.enable:=false
```

### Segmentation

```bash
ros2 launch wally_perception segmentation.launch.py
```

### Nvblox

```bash
# Depth mode
ros2 launch wally_nvblox nvblox.launch.py

# LiDAR mode
ros2 launch wally_nvblox nvblox_lidar.launch.py
```

### Nav2

```bash
ros2 launch nav2_bringup bringup_launch.py \
  use_sim_time:=false \
  map:=~/wally/configs/maps/map.yaml \
  params_file:=~/wally/configs/nav2/nav2_parameters.yaml
```

### Frontier exploration

```bash
ros2 launch frontier_exploration classical_exploration.launch.py
```

## 3) Running nvblox inside Docker

Nvblox is expected to run in the Isaac ROS container.

```bash
# Find containers
sudo docker ps -a

# Start one (if stopped)
sudo docker start <container_name_or_id>

# Run nvblox inside it
sudo docker exec -it <container_name_or_id> bash -lc '
source /opt/ros/humble/setup.bash
source /workspaces/isaac_ros-dev/ros2_ws/install/setup.bash
ros2 launch wally_nvblox nvblox.launch.py
'
```

## 4) Launch files present in this repo

### `wally_bringup`
- `ros2_ws/src/wally_bringup/launch/jetson.launch.py`
- `ros2_ws/src/wally_bringup/launch/workspace.launch.py`
- `ros2_ws/src/wally_bringup/launch/robot_description.launch.py`
- `ros2_ws/src/wally_bringup/launch/lidar.launch.py`
- `ros2_ws/src/wally_bringup/launch/camera.launch.py`
- `ros2_ws/src/wally_bringup/launch/teleop.launch.py`

### `wally_fastlio`
- `ros2_ws/src/wally_fastlio/launch/mapping.launch.py`
- `ros2_ws/src/wally_fastlio/launch/mid360_bringup.launch.py`

### `wally_nvblox`
- `ros2_ws/src/wally_nvblox/launch/nvblox.launch.py`
- `ros2_ws/src/wally_nvblox/launch/nvblox_lidar.launch.py`

### `wally_perception`
- `ros2_ws/src/wally_perception/launch/segmentation.launch.py`

### `frontier_exploration`
- `ros2_ws/src/frontier_exploration/frontier_exploration/launch/classical_exploration.launch.py`
- `ros2_ws/src/frontier_exploration/frontier_exploration/launch/custom_nav_bringup.launch.py`
- `ros2_ws/src/frontier_exploration/frontier_exploration/launch/lite_turtlebot_full_stack.launch.py`
- `ros2_ws/src/frontier_exploration/frontier_exploration/launch/turtlebot_full_stack.launch.py`

### `livox_ros_driver2`
- `ros2_ws/src/livox_ros_driver2/launch_ROS2/msg_MID360_launch.py`
- `ros2_ws/src/livox_ros_driver2/launch_ROS2/msg_HAP_launch.py`
- `ros2_ws/src/livox_ros_driver2/launch_ROS2/rviz_MID360_launch.py`
- `ros2_ws/src/livox_ros_driver2/launch_ROS2/rviz_HAP_launch.py`

### `wally_navigation`
- No `.launch.py` files currently present.

## 5) Documented issues (current state)

1. **nvblox host launch not supported:** `nvblox_ros` is still not available in host ROS environment. Run nvblox from the Isaac ROS Docker container.
2. **segmentation not working:** Isaac ROS segmentation dependencies are not available in host environment.
3. **frontier_exploration not working (full stack):** Turtlebot4 simulation dependencies are missing (for the full-stack launch files).
4. **Isaac ROS Docker image/container (nvblox):** available and confirmed working for individual nvblox launch.
5. **nav2 not fully working:** Nav2 core is installed, but full integration with current robot stack/frontier flow is incomplete.
