#!/usr/bin/env python3
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    pkg_dir = get_package_share_directory('dsp')
    
    # الأسماء الصحيحة
    drone_odom_frame = 'odom'         
    drone_base_frame = 'Iris/base_link'
    
    # 1. Octomap Server
    octomap_server_node = Node(
        package='octomap_server',
        executable='octomap_server_node',
        name='octomap_server',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'resolution': 0.15,
            'frame_id': drone_odom_frame,
            'base_frame_id': drone_base_frame,
            'sensor_model/max_range': 8.0,
            'latch': False,
            'filter_ground': True,            # تفعيل فلتر الأرضية الذكي
            'ground_filter/distance': 0.2,    # مسافة التسامح
            'ground_filter/plane_distance': 0.2,

            'pointcloud_min_z': 0.2,          # تجاهل أي نقطة ليزر ارتفاعها أقل من 20 سم
            'occupancy_min_z': 0.2,           # لا ترسم أي مكعب ارتفاعه أقل من 20 سم
            'occupancy_max_z': 5.0,
        }],
        remappings=[
            ('cloud_in', '/scan/points'),
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
                'odom_topic': '/odom',
                'map_topic': '/octomap_full',
                'use_3d': True,
                'use_odometry': True
            }
        ],
        remappings=[
             ('path', '/dsp/path'),
             ('set_goal', '/dsp/set_goal')
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
    
    # 4. الحل السحري لمشكلة الـ Queue Full: ربط الحساس بجسم الطائرة
    # نربط Iris/base_link بـ Iris/lidar_link/lidar
    tf_lidar = Node(
        package='tf2_ros', executable='static_transform_publisher',
        arguments=['0', '0', '0.1', '0', '0', '0', 'Iris/base_link', 'Iris/lidar_link/lidar']
    )

    return LaunchDescription([
        octomap_server_node,
        dsp_grid_3d_node,
        rviz_node,
        tf_lidar  # <--- ضروري جداً
    ])
