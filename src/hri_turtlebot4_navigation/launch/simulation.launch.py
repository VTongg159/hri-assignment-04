"""Launch the installed official Nav2 minimal TurtleBot 4 Gazebo simulation."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    package_dir = get_package_share_directory('hri_turtlebot4_navigation')
    simulator_dir = get_package_share_directory('nav2_minimal_tb4_sim')

    headless = LaunchConfiguration('headless')
    world = LaunchConfiguration('world')
    x_pose = LaunchConfiguration('x_pose')
    y_pose = LaunchConfiguration('y_pose')
    yaw = LaunchConfiguration('yaw')

    simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(simulator_dir, 'launch', 'simulation.launch.py')
        ),
        launch_arguments={
            'headless': headless,
            'world': world,
            'x_pose': x_pose,
            'y_pose': y_pose,
            'yaw': yaw,
            'use_sim_time': 'true',
            'rviz_config_file': os.path.join(
                package_dir, 'rviz', 'turtlebot4_navigation.rviz'
            ),
        }.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'headless', default_value='False', choices=['True', 'False'],
            description='Run Gazebo without its graphical client (case-sensitive).'
        ),
        DeclareLaunchArgument(
            'world',
            default_value=os.path.join(package_dir, 'worlds', 'hri_lab.sdf'),
            description='Gazebo world. The default is local and network-free.'
        ),
        DeclareLaunchArgument('x_pose', default_value='-3.5'),
        DeclareLaunchArgument('y_pose', default_value='-2.5'),
        DeclareLaunchArgument('yaw', default_value='0.0'),
        simulation,
    ])
