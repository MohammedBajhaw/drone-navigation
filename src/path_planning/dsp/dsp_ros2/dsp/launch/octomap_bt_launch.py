#!/usr/bin/env python3
"""
Amaç: Önceden kaydedilmiş .bt formatında bir octomap dosyasını yüklemek.
Özellikler: Hazır bir harita dosyasını ('/home/grammers/Downloads/Telegram Desktop/obstacle_room.bt')
sisteme yükler ve 'map' frame'ine bağlar.

İlişkiler: Bu dosya bağımsız olarak çalıştırılabilen bir octomap yükleme konfigürasyonudur.
Diğer octomap dosyalarından bağımsızdır ve DSP algoritmasına hazır bir harita sağlar.
DSP dosyalarından herhangi biriyle (dsp_grid3d_gazebo_launch.py vb.) birlikte kullanılabilir.
"""

from launch import LaunchDescription
from launch_ros.actions import Node

"""
  Example launch file for octomap_server mapping: 
  Listens to incoming PointCloud2 data and incrementally builds an octomap. 
  The data is sent out in different representations. 
  
  rosrun octomap_server octomap_server_node "forest0.bt"
"""

def generate_launch_description():
    # Create octomap server node
    octomap_server_node = Node(
        package='octomap_server',
        executable='octomap_server_node',
        name='octomap_server',
        output='screen',
        arguments=['/home/grammers/Downloads/Telegram\ Desktop/obstacle_room.bt'],
        parameters=[{
            'frame_id': 'map'
        }]
    )
    
    # Return the launch description
    return LaunchDescription([
        octomap_server_node
    ]) 