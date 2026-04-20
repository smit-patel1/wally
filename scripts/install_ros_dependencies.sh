#!/usr/bin/env bash
#
# Installs ROS runtime dependencies required by wally_bringup full Jetson launch.
# Supports a non-root check mode:
#   ./scripts/install_ros_dependencies.sh --check

set -euo pipefail

REQUIRED_PACKAGES=(
  ros-humble-depthai-ros-driver
  ros-humble-nvblox-ros
)

MODE="install"
if [[ "${1:-}" == "--check" ]]; then
  MODE="check"
fi

if [[ "$MODE" == "check" ]]; then
  # For check mode, try to source ROS automatically if ros2 is not in PATH.
  if ! command -v ros2 >/dev/null 2>&1 && [[ -f /opt/ros/humble/setup.bash ]]; then
    # shellcheck disable=SC1091
    source /opt/ros/humble/setup.bash
  fi

  if ! command -v ros2 >/dev/null 2>&1; then
    echo "[deps] ros2 command not found. Source ROS first (e.g. source /opt/ros/humble/setup.bash)." >&2
    exit 2
  fi

  missing=0
  if ros2 pkg prefix depthai_ros_driver >/dev/null 2>&1; then
    echo "[deps] depthai_ros_driver: found"
  else
    echo "[deps] depthai_ros_driver: MISSING"
    missing=1
  fi

  if ros2 pkg prefix nvblox_ros >/dev/null 2>&1; then
    echo "[deps] nvblox_ros: found"
  else
    echo "[deps] nvblox_ros: MISSING"
    missing=1
  fi
  exit "$missing"
fi

if [[ "${EUID}" -ne 0 ]]; then
  echo "[deps] Re-running with sudo..."
  exec sudo bash "$0"
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y "${REQUIRED_PACKAGES[@]}"

echo "[deps] Installed required ROS packages:"
printf '  - %s\n' "${REQUIRED_PACKAGES[@]}"
