import math
import numpy as np
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from ackermann_msgs.msg import AckermannDriveStamped
from sensor_msgs.msg import LaserScan

class OdomCalibration(Node):
    def __init__(self):
        super().__init__('odom_calibration')
        self.publish_period = 0.05  # [s]
        self.max_time = 5 # [s]
        self.max_linX = 1 # [m/s]
        self.acceleration = 0.5 # [m/s^2]
        self.displacement = 0 # [m]
        self.last_linX = 0 # [m/s]
        self.last_time = 0 # [s]

        self.create_subscription(LaserScan, '/scan', self.scan_callback, 10)
        self.create_subscription(Odometry, '/odom', self.odom_callback, 10)
        self.publisher_ = self.create_publisher(AckermannDriveStamped, '/ackermann_cmd_mux/input/default', 10)
        self.timer = self.create_timer(self.publish_period, self.timer_callback)
        self.get_logger().info("Odom Calibration Node has been created")

    def scan_callback(self, msg):
        self.scan = msg

    def odom_callback(self, msg):
        self.odom = msg

    def timer_callback(self):
      self.start_time = self.get_clock().now().nanoseconds
      if self.get_clock().now().nanoseconds - self.start_time <= self.max_time:
        twist_msg = self.get_twist_msg()
        self.publisher_.publish(twist_msg)
      else:
        self.get_logger().info("Finished")
        self.get_logger().info(f"Expected: {self.displacement}")
        print(f"Expected: {self.displacement}")
        self.timer.cancel()

    def get_twist_msg(self):
      current_time = (self.get_clock().now().nanoseconds - self.start_time)/1e9
      if current_time < self.max_time/3 and self.last_linX < self.max_linX:
        linX = self.last_linX + self.acceleration * (current_time - self.last_time)
      elif current_time < 2 * self.max_time/3:
        linX = self.last_linX
      elif current_time < self.max_time:
        linX = self.last_linX - self.acceleration * (current_time - self.last_time)
      else:
        linX = 0
      twist = AckermannDriveStamped()
      twist.drive.speed = linX
      self.displacement += linX * (current_time - self.last_time)
      self.last_time = current_time
      self.last_linX = linX
      return twist