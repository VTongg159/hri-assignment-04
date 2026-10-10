#!/usr/bin/env python3
"""Keyboard teleoperation for TurtleBot 4 using W/A/S/D."""

import select
import sys
import termios
import time
import tty

from geometry_msgs.msg import Twist
import rclpy
from rclpy.node import Node


HELP = """
Điều khiển TurtleBot 4 bằng bàn phím
------------------------------------
        W: đi thẳng
  A: quay trái    D: quay phải
        S: đi lùi

  Space hoặc X: dừng
  Q: thoát

Giữ phím để robot tiếp tục di chuyển.
"""


class WasdTeleop(Node):
    def __init__(self):
        super().__init__('wasd_teleop')
        self.declare_parameter('linear_speed', 0.15)
        self.declare_parameter('angular_speed', 0.60)
        self.declare_parameter('key_timeout', 0.50)

        self.linear_speed = float(self.get_parameter('linear_speed').value)
        self.angular_speed = float(self.get_parameter('angular_speed').value)
        self.key_timeout = float(self.get_parameter('key_timeout').value)
        self.publisher = self.create_publisher(Twist, 'cmd_vel', 10)
        self.last_key_time = time.monotonic()
        self.moving = False

    def publish_command(self, linear_x=0.0, angular_z=0.0):
        command = Twist()
        command.linear.x = linear_x
        command.angular.z = angular_z
        self.publisher.publish(command)
        self.moving = linear_x != 0.0 or angular_z != 0.0
        self.last_key_time = time.monotonic()

    def handle_key(self, key):
        key = key.lower()
        if key == 'w':
            self.publish_command(linear_x=self.linear_speed)
        elif key == 's':
            self.publish_command(linear_x=-self.linear_speed)
        elif key == 'a':
            self.publish_command(angular_z=self.angular_speed)
        elif key == 'd':
            self.publish_command(angular_z=-self.angular_speed)
        elif key in (' ', 'x'):
            self.publish_command()
        elif key in ('q', '\x03', '\x04'):
            self.publish_command()
            return False
        return True

    def stop_if_key_released(self):
        if self.moving and time.monotonic() - self.last_key_time > self.key_timeout:
            self.publish_command()


def main(args=None):
    if not sys.stdin.isatty():
        print('Lỗi: wasd_teleop phải được chạy trong terminal tương tác.', file=sys.stderr)
        return 1

    rclpy.init(args=args)
    node = WasdTeleop()
    terminal_settings = termios.tcgetattr(sys.stdin)
    print(HELP)

    try:
        # Cbreak keeps Ctrl+C available while reading keys without Enter.
        tty.setcbreak(sys.stdin.fileno())
        keep_running = True
        while rclpy.ok() and keep_running:
            rclpy.spin_once(node, timeout_sec=0.0)
            readable, _, _ = select.select([sys.stdin], [], [], 0.05)
            if readable:
                keep_running = node.handle_key(sys.stdin.read(1))
            else:
                node.stop_if_key_released()
    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, terminal_settings)
        if rclpy.ok():
            node.publish_command()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
        print('\nĐã dừng robot và thoát WASD teleop.')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
