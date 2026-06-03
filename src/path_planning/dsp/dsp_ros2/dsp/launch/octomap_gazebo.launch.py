#!/usr/bin/env python3
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    # Create octomap server node
    octomap_server_node = Node(
        package='octomap_server',
        executable='octomap_server_node',
        name='octomap_server',
        parameters=[{
            'resolution': 0.5,
            'frame_id': 'odom',
            'sensor_model/max_range': 10.0,
            'sensor_model/min_range': 0.4,
        }],
        remappings=[
            ('cloud_in', '/scan/points'),
        ]
    )
    
    # Commented static transform publisher
    # static_transform_publisher = Node(
    #     package='tf2_ros',
    #     executable='static_transform_publisher',
    #     name='fake_loc',
    #     arguments=['0', '0', '0', '0', '0', '0', 'odom', 'world']
    # )
    
    # Return the launch description
    return LaunchDescription([
        octomap_server_node,
        # static_transform_publisher
    ]) 