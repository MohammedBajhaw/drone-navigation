#!/usr/bin/env python3
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    pkg_dir = get_package_share_directory('dsp')
    
    drone_odom_frame = 'X3/odom'         
    drone_base_frame = 'X3/base_link'
    
    # 1. Octomap Server (تحسينات الأداء القصوى)
    octomap_server_node = Node(
        package='octomap_server',
        executable='octomap_server_node',
        name='octomap_server',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'resolution': 0.40,               # <--- رفعنا القيمة لتخفيف الرام والحسابات
            'frame_id': drone_odom_frame,
            'base_frame_id': drone_base_frame,
            'sensor_model/max_range': 5.0,    # <--- قللنا المدى لـ 5 أمتار فقط (لا داعي لرؤية آخر النفق)
            'latch': False,
            'filter_ground': False,
            'pointcloud_min_z': -100.0,
            'pointcloud_max_z': 100.0,
            'occupancy_min_z': 0.2,           # تجاهل الأرضية المنخفضة جداً
            'occupancy_max_z': 5.0,           # تجاهل السقف العالي جداً
        }],
        remappings=[
            ('cloud_in', '/X3/scan/points'),
            ('octomap_full', '/octomap_full')
        ]
    )

    # 2. DSP Planner
    dsp_grid_3d_node = Node(
        package='dsp',
        executable='dsp',
        name='dsp',
        output='screen',
        parameters=[
            os.path.join(pkg_dir, 'config', 'params.yaml'),
            {
                'use_sim_time': True,
                'odom_frame_id': drone_odom_frame,
                'base_link_frame_id': drone_base_frame,
                'odom_topic': '/X3/odom',
                'map_topic': '/octomap_full',
                'use_3d': True,
                'use_odometry': True
            }
        ]
    )

    # 3. RViz
    rviz_config_path = os.path.join(pkg_dir, 'config', 'dsp_3d.rviz')
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_path],
        parameters=[{'use_sim_time': True}]
    )

    return LaunchDescription([
        octomap_server_node,
        dsp_grid_3d_node,
        rviz_node
    ])
