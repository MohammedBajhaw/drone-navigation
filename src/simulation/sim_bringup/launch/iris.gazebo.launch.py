import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution, LaunchConfiguration, PythonExpression
from launch_ros.actions import Node

def generate_launch_description():
    pkg_drone = get_package_share_directory('drone')
    pkg_sim_worlds = get_package_share_directory('sim_worlds')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    # استخدام عالمك المخصص
    default_world_path = PathJoinSubstitution([pkg_sim_worlds, 'worlds', 'custom_cave.sdf'])

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py'])),
        launch_arguments={'gz_args': PythonExpression(["'", LaunchConfiguration('world'), " -r'"])}.items(),
    )

    sdf_file = os.path.join(pkg_drone, 'model', 'Iris', 'model.sdf')
    bridge_config = os.path.join(pkg_drone, 'config', 'iris_bridge.yaml')

    spawn_x = LaunchConfiguration('x', default='0.0')
    spawn_y = LaunchConfiguration('y', default='0.0')
    spawn_z = LaunchConfiguration('z', default='0.5')

    spawn = Node(
        package='ros_gz_sim', executable='create',
        arguments=['-name', 'Iris', '-file', sdf_file, '-x', spawn_x, '-y', spawn_y, '-z', spawn_z],
        output='screen'
    )

    bridge = Node(
        package='ros_gz_bridge', executable='parameter_bridge',
        parameters=[{'config_file': bridge_config, 'qos_overrides./tf_static.publisher.durability': 'transient_local'}],
        output='screen'
    )

    # تحويلات ثابتة لتكتمل شجرة TF
    static_tf = Node(
        package='tf2_ros', executable='static_transform_publisher',
        arguments=['0', '0', '0', '0', '0', '0', 'world', 'odom']
    )

    # ربط الـ base_link بالـ footprint إذا لزم الأمر
    static_tf_base = Node(
        package='tf2_ros', executable='static_transform_publisher',
        arguments=['0', '0', '0', '0', '0', '0', 'Iris/base_link', 'base_link']
    )

    from launch.actions import SetEnvironmentVariable
    
    # تحديد مسارات الموديلات (إضافة المجلدات التي تحتوي على العوالم والمجسمات)
    worlds_path = os.path.join(pkg_sim_worlds, 'worlds')
    models_path = os.path.join(pkg_sim_worlds, 'worlds', 'models')
    drone_models_path = os.path.join(pkg_drone, 'model')
    gazebo_models_path = os.path.expanduser('~/.gazebo/models')

    return LaunchDescription([
        SetEnvironmentVariable('IGN_GAZEBO_RESOURCE_PATH', 
            worlds_path + ':' + models_path + ':' + drone_models_path + ':' + gazebo_models_path),
        DeclareLaunchArgument('world', default_value=default_world_path),
        gz_sim, spawn, bridge, static_tf, static_tf_base
    ])
