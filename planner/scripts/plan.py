import sys
import argparse
import numpy as np

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSDurabilityPolicy, QoSReliabilityPolicy

from nav_msgs.msg import Path
from geometry_msgs.msg import PointStamped   # 新增

from utils import traj2ros
from planner_wrapper import TomogramPlanner

sys.path.append('../')
from config import Config

class PCTPlanner(Node):
    def __init__(self, cfg, tomo_file, robot_height):
        super().__init__('pct_planner')
        self.cfg = cfg
        self.tomo_file = tomo_file
        self.robot_height = robot_height

        qos = QoSProfile(
            depth=1,
            reliability=QoSReliabilityPolicy.RELIABLE,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL
        )

        self.path_pub = self.create_publisher(Path, "/pct_path", qos)
        self.click_sub = self.create_subscription(PointStamped, "/clicked_point", self.clicked_point_callback, 10)

        self.planner = TomogramPlanner(cfg)
        self.planner.loadTomogram(self.tomo_file)

        self.start_pos = None
        self.start_layer = None
        self.end_pos = None
        self.end_layer = None

        self.get_logger().info("Waiting for two clicked points in RViz...")

    def clicked_point_callback(self, msg):
        point = np.array([msg.point.x, msg.point.y, msg.point.z], dtype=np.float32)

        if self.start_pos is None:
            self.start_pos = point[:2]
            self.start_layer = self.planner.height2layer(point[2])
            self.get_logger().info(f"🟢 Start point set to: {self.start_pos}")
        elif self.end_pos is None:
            self.end_pos = point[:2]
            self.end_layer = self.planner.height2layer(point[2])
            self.get_logger().info(f"🔴 End point set to: {self.end_pos}")
            self.pct_plan()
        else:
            self.get_logger().info("♻️ Resetting start/end points...")
            self.start_pos = point[:2]
            self.start_layer = self.planner.height2layer(point[2])
            self.end_pos = None

    def pct_plan(self):

        traj_3d = self.planner.plan(self.start_pos, self.end_pos, self.start_layer, self.end_layer, self.robot_height)
        if traj_3d is not None:
            self.path_pub.publish(traj2ros(traj_3d))
            self.get_logger().info("✅ Trajectory published to /pct_path")
        else:
            self.get_logger().warn("❌ Planning failed!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--scene', type=str, default='Spiral', help='Name of the scene. Available: [\'Spiral\', \'Building\', \'Plaza\', \'Map\']')
    parser.add_argument('--robot_height', type=float, default=0.05, help='Height of the robot')
    args = parser.parse_args()

    cfg = Config()

    match args.scene:
        case "Spiral":
            tomo_file = "spiral0.3_2"
        case 'Building':
            tomo_file = 'building2_9'
        case 'Plaza':
            tomo_file = 'plaza3_10'
        case "Map":
            tomo_file = "map"
        case _:
            raise ValueError('Invalid scene name')

    rclpy.init(args=None)
    node = PCTPlanner(cfg, tomo_file, args.robot_height)
    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()
