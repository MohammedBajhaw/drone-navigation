import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler
from launch.event_handlers import OnProcessStart
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution, LaunchConfiguration # <--- أضفنا LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    pkg_project_description = get_package_share_directory('drone')
    pkg_sim_worlds = get_package_share_directory('sim_worlds')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    # 1. إعداد مسار العالم الافتراضي (للحفاظ على عمل الكود القديم إذا لم تحدد عالماً)
    default_world_path = PathJoinSubstitution([
        pkg_sim_worlds,
        'worlds',
        'custom_cave.sdf'
    ])

    # 2. استقبال معامل "world" من التيرمينال
    world_arg = DeclareLaunchArgument(
        'world',
        default_value=default_world_path,
        description='Path to the world file (SDF) to load'
    )

    sdf_file  = os.path.join(pkg_project_description, 'model','X3','model2.sdf')
    with open(sdf_file, 'r') as infp:
        robot_desc = infp.read()

    # 3. تعديل تشغيل الجازيبو لاستخدام المتغير بدلاً من المسار الثابت
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                pkg_ros_gz_sim,
                'launch',
                'gz_sim.launch.py'
            ])
        ),
        launch_arguments={
            'gz_args': ['-r ', LaunchConfiguration('world')] # -r للتشغيل التلقائي + مسار العالم
        }.items(),
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{
            'config_file': os.path.join(pkg_project_description, 'config', 'drone_gz_bridge.yaml'),
            'qos_overrides./tf_static.publisher.durability': 'transient_local',
        }],
        output='screen'
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        namespace='X3',
        output='both',
        parameters=[
            {'use_sim_time': True},
            {'robot_description': robot_desc}
        ]
    )

    gz_spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=[
            '-topic', '/X3/robot_description',
            '-name', 'X3',
            '-allow_renaming', 'true',
            '-z', '0.2',
            '-x', '0.0', # جعلتها 0.0 لتكون في بداية النفق المستقيم
            '-y', '0.0',
        ]
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', os.path.join(pkg_project_description, 'config', 'drone_rviz.rviz')]
    )

    # 4. لا تنسَ إضافة world_arg إلى القائمة النهائية
    return LaunchDescription([
        world_arg,
        gz_sim,
        robot_state_publisher,
        gz_spawn_entity,
        bridge,
        rviz
    ])
