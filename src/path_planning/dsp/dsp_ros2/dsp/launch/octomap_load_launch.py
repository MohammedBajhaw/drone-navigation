#!/usr/bin/env python3
"""
Amaç: Kullanıcının belirttiği bir konumdan octomap dosyası yüklemek.
Özellikler: Argüman olarak harita dosyasının yolunu ve namespace'i alır, 15m maksimum
algılama mesafesi, 0.5 çözünürlükte harita.

İlişkiler: Bu dosya bağımsız olarak çalıştırılabilen bir octomap yükleme konfigürasyonudur.
octomap_bt_launch.py'ye benzer işlevi yapar, ancak bu dosya argüman ile harita yolunu 
belirlemeye izin verir. DSP dosyalarından herhangi biriyle (dsp_grid3d_gazebo_launch.py vb.)
birlikte kullanılabilir.
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, EnvironmentVariable
from launch_ros.actions import Node

def generate_launch_description():
    # Declare arguments
    name = LaunchConfiguration('name')
    map_path = LaunchConfiguration('map_path')
    
    name_arg = DeclareLaunchArgument(
        'name',
        default_value='shafter4',
        description='Name prefix for the node namespace'
    )
    
    map_path_arg = DeclareLaunchArgument(
        'map_path',
        default_value=['/home/', EnvironmentVariable('USER'), '/maps/test.bt'],
        description='Path to the octomap .bt file'
    )
    
    # Create octomap server node
    octomap_server_node = Node(
        package='octomap_server',
        executable='octomap_server_node',
        name='octomap_map',
        namespace=name,
        output='screen',
        arguments=[map_path],
        parameters=[{
            'frame_id': 'map',
            'sensor_model/max_range': 15.0,
            'sensor_model/min_range': 0.5,
            'resolution': 0.5,
            'publish_free_space': True,
            # Commented parameters:
            # 'sensor_model/hit': 0.99,
            # 'sensor_model/miss': 0.4,
            # 'occupancy_min_z': 0.0,
            # 'occupancy_max_z': 0.5,
        }],
        remappings=[
            ('cloud_in', '/os_cloud_node/points'),
        ]
    )
    
    # Return the launch description
    return LaunchDescription([
        name_arg,
        map_path_arg,
        octomap_server_node
    ]) 