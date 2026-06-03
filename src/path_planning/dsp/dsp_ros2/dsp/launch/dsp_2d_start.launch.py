#!/usr/bin/env python3
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    pkg_dir = get_package_share_directory('dsp')
    
    slam_toolbox_launch= IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_dir, 'launch', 'slam.launch.py')
        )
    )
    dsp_grid_2d_gazebo_launch = Node(
        package='dsp',
        executable='dsp',
        name='dsp',
        output='screen',
        parameters=[
            os.path.join(pkg_dir, 'config', 'params.yaml'),
            {
                'use_gazebo_odom': True,
                'odom_topic': 'go2/odom',
                'odom_frame_id': 'odom',
                'map_topic': '/map',
                'use_3d': False
            }
        ]
    )
    path_to_pose_node = Node(
        package='dsp',
        executable='path_to_pose.py',
        name='path_to_pose',
        output='screen'
    )
    rviz_config_path = os.path.join(pkg_dir, 'config', 'dsp_2d.rviz')
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_path]
    )
    ld=LaunchDescription()
    ld.add_action(slam_toolbox_launch)
    ld.add_action(dsp_grid_2d_gazebo_launch)
    ld.add_action(path_to_pose_node)
    ld.add_action(rviz_node)
    return ld