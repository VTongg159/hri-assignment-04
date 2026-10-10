"""Launch Nav2 planning and control; localization must already be running."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    package_dir = get_package_share_directory('hri_turtlebot4_navigation')
    nav2_dir = get_package_share_directory('nav2_bringup')

    navigation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_dir, 'launch', 'navigation_launch.py')
        ),
        launch_arguments={
            'params_file': os.path.join(package_dir, 'config', 'nav2_params.yaml'),
            'use_sim_time': 'true',
            'autostart': 'true',
            'use_composition': 'False',
        }.items(),
    )

    return LaunchDescription([navigation])
