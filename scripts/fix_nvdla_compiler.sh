#!/bin/bash
#
# Fix missing libnvdla_compiler.so inside the Isaac ROS container.
#
# TensorRT's libnvinfer_plugin.so.10 links against libnvdla_compiler.so,
# but the nvidia-l4t-dla-compiler package can't install cleanly inside
# the container due to overlay filesystem cross-device link errors.
#
# This script extracts the library from the .deb on the host mount and
# copies it into the container's library path at container startup.

set -e

NVDLA_LIB="/usr/lib/aarch64-linux-gnu/nvidia/libnvdla_compiler.so"

if [ -f "$NVDLA_LIB" ]; then
    echo "[fix_nvdla_compiler] libnvdla_compiler.so already present, skipping."
    exit 0
fi

echo "[fix_nvdla_compiler] Installing missing libnvdla_compiler.so..."

# Check if pre-extracted library exists on the host mount
HOST_LIB="/workspaces/isaac_ros-dev/scripts/lib/libnvdla_compiler.so"
if [ -f "$HOST_LIB" ]; then
    cp "$HOST_LIB" "$NVDLA_LIB"
else
    # Extract from apt package
    TMPDIR=$(mktemp -d)
    cd "$TMPDIR"
    apt-get download nvidia-l4t-dla-compiler 2>/dev/null
    dpkg-deb -x nvidia-l4t-dla-compiler*.deb extract/
    cp extract/usr/lib/aarch64-linux-gnu/nvidia/libnvdla_compiler.so "$NVDLA_LIB"

    # Cache the extracted library on the host mount for next time
    mkdir -p /workspaces/isaac_ros-dev/scripts/lib
    cp "$NVDLA_LIB" "$HOST_LIB"

    rm -rf "$TMPDIR"
fi

ldconfig
echo "[fix_nvdla_compiler] libnvdla_compiler.so installed successfully."
