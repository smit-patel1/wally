import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import numpy as np

# PeopleSemSegNet class labels
PERSON_CLASS_ID = 1  # class 1 = person in PeopleSemSegNet

class MaskConverterNode(Node):
    def __init__(self):
        super().__init__("mask_converter_node")

        self.bridge = CvBridge()

        self.sub = self.create_subscription(
            Image,
            "/unet/raw_segmentation_mask",
            self.mask_callback,
            10
        )

        self.pub = self.create_publisher(
            Image,
            "/camera_0/mask/image",
            10
        )

        self.get_logger().info("Mask converter node ready")

    def mask_callback(self, msg: Image):
        # Convert to numpy
        raw_mask = self.bridge.imgmsg_to_cv2(msg, desired_encoding="mono8")

        # Binary: 1 where person, 0 everywhere else
        binary_mask = (raw_mask == PERSON_CLASS_ID).astype(np.uint8)

        # Publish with original timestamp for nvblox sync
        out_msg = self.bridge.cv2_to_imgmsg(binary_mask, encoding="mono8")
        out_msg.header = msg.header
        self.pub.publish(out_msg)


def main(args=None):
    rclpy.init(args=args)
    node = MaskConverterNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()