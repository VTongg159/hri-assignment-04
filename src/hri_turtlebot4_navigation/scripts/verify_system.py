#!/usr/bin/env python3
"""Check topics and lifecycle states without changing the running system."""

import sys
import time

from lifecycle_msgs.srv import GetState
import rclpy
from rclpy.node import Node


TOPICS = {
    'LiDAR': ['/scan'],
    'odometry': ['/odom'],
    'velocity command': ['/cmd_vel', '/cmd_vel_smoothed', '/cmd_vel_nav'],
    'dynamic TF': ['/tf'],
    'static TF': ['/tf_static'],
    'occupancy map': ['/map'],
}


class SystemCheck(Node):
    def __init__(self):
        super().__init__('hri_turtlebot4_system_check')

    def graph_topics(self):
        result = {}
        for name, types in self.get_topic_names_and_types():
            publishers = self.count_publishers(name)
            subscribers = self.count_subscribers(name)
            result[name] = (types, publishers, subscribers)
        return result

    def lifecycle_state(self, node_name):
        client = self.create_client(GetState, f'/{node_name}/get_state')
        if not client.wait_for_service(timeout_sec=0.35):
            return None
        future = client.call_async(GetState.Request())
        rclpy.spin_until_future_complete(self, future, timeout_sec=1.0)
        if future.done() and future.result() is not None:
            return future.result().current_state.label
        return 'unknown'


def find_first(graph, candidates):
    return next((name for name in candidates if name in graph), None)


def aggregate_state(check, names):
    available = {name.lstrip('/') for name in check.get_node_names()}
    missing = [name for name in names if name not in available]
    if missing:
        return 'INACTIVE (missing: ' + ', '.join(missing) + ')'
    states = [check.lifecycle_state(name) for name in names]
    if all(state == 'active' for state in states):
        return 'ACTIVE'
    return 'INACTIVE (' + ', '.join(
        f'{name}={state or "state unavailable"}'
        for name, state in zip(names, states)
    ) + ')'


def main():
    rclpy.init(args=sys.argv)
    check = SystemCheck()
    # Give DDS time to discover nodes started in other terminals.
    deadline = time.monotonic() + 6.0
    while time.monotonic() < deadline:
        rclpy.spin_once(check, timeout_sec=0.1)

    graph = check.graph_topics()
    print('=== TurtleBot 4 System Check ===\n')
    for label, candidates in TOPICS.items():
        actual = find_first(graph, candidates)
        if actual is None:
            print(f'[MISSING] {label}: expected one of {", ".join(candidates)}')
            continue
        types, publishers, subscribers = graph[actual]
        # A command topic is healthy when the simulator/controller subscribes;
        # sensor/state topics are healthy when something publishes.
        connected = subscribers > 0 if label == 'velocity command' else publishers > 0
        status = 'OK' if connected else 'WARN'
        print(
            f'[{status}] {actual} ({", ".join(types)}) '
            f'publishers={publishers}, subscribers={subscribers}'
        )

    print()
    print('SLAM:', aggregate_state(check, ['slam_toolbox']))
    print('Localization:', aggregate_state(check, ['map_server', 'amcl']))
    print('Nav2:', aggregate_state(check, [
        'controller_server', 'planner_server', 'bt_navigator'
    ]))

    check.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
