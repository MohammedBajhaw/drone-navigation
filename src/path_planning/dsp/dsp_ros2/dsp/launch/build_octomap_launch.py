#!/usr/bin/env python3
"""
Amaç: Bir PointCloud2 veri akışından octomap oluşturmak.
Özellikler: 0.3 çözünürlükte harita, 15m maksimum algılama mesafesi, 'ouster/points' topic'inden veri alır.

İlişkiler: Bu dosya dsp_3d_start_launch.py tarafından doğrudan çağrılmaz, ancak benzer işlevi olan
octomap_gazebo_launch.py dosyası onun tarafından çağrılır. Bu dosya bağımsız olarak çalıştırılarak
DSP path planning için harita oluşturulabilir.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

"""
  Example launch file for octomap_server mapping: 
  Listens to incoming PointCloud2 data and incrementally builds an octomap. 
  The data is sent out in different representations.
"""

def generate_launch_description():
    # Declare arguments
    name = LaunchConfiguration('name')
    name_arg = DeclareLaunchArgument(
        'name',
        default_value='shafter4',
        description='Name prefix for the node namespace'
    )
    
    # Create octomap server node
    octomap_server_node = Node(
        package='octomap_server',
        executable='octomap_server_node',
        name='octomap_server',
        namespace=name,
        parameters=[{
            'resolution': 0.3,
            'frame_id': [name, '/odom'],
            'sensor_model/max_range': 15.0,
            'sensor_model/min_range': 0.5,
            'publish_free_space': True,
        }],
        remappings=[
            ('cloud_in', 'ouster/points'),
        ]
    )
    
    # Return the launch description
    return LaunchDescription([
        name_arg,
        octomap_server_node
    ]) 