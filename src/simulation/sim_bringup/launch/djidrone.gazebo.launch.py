import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution, LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    pkg_project_description = get_package_share_directory('drone')
    pkg_sim_worlds = get_package_share_directory('sim_worlds')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    default_world_path = PathJoinSubstitution([pkg_sim_worlds, 'worlds', 'custom_cave.world'])
    
    sdf_file = os.path.join(pkg_project_description, 'model', 'Mavic2', 'model.sdf')
    with open(sdf_file, 'r') as infp:
        robot_desc = infp.read()

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py'])),
        launch_arguments={'gz_args': [LaunchConfiguration('world'), ' -r']}.items(),
    )

    # الجسر المعدل
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            # نقل بيانات الموقع الحقيقي (Pose Array)
            '/model/Mavic2/pose@geometry_msgs/msg/PoseArray[ignition.msgs.Pose_V',
            # نقل التحكم والليزر
            '/model/Mavic2/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist',
            '/scan@sensor_msgs/msg/LaserScan[ignition.msgs.LaserScan',
            '/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock',
        ],
        remappings=[
            ('/model/Mavic2/cmd_vel', '/cmd_vel'),
            ('/model/Mavic2/pose', '/sim_pose') # سنستخدم هذا التوبيك لتوليد الاودوم
        ],
        output='screen'
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='both',
        parameters=[{'use_sim_time': True}, {'robot_description': robot_desc}]
    )

    gz_spawn_entity = Node(
        package='ros_gz_sim', executable='create', output='screen',
        arguments=['-topic', '/robot_description', '-name', 'Mavic2', '-allow_renaming', 'true', '-z', '0.2']
    )

    # تشغيل محول الأودوميتري (سننشئه في الخطوة القادمة)
    odom_converter = Node(
        package='drone', # تأكد أن هذا اسم الباكيج الصحيح لديك
        executable='odom_converter.py', # سننشئ هذا الملف
        output='screen'
    )

    rviz = Node(
        package='rviz2', executable='rviz2',
        arguments=['-d', os.path.join(pkg_project_description, 'config', 'drone_rviz.rviz')]
    )

    return LaunchDescription([
        DeclareLaunchArgument('world', default_value=default_world_path),
        gz_sim, robot_state_publisher, gz_spawn_entity, bridge, 
        # rviz  <-- يمكنك تفعيل هذا السطر إذا كنت تريد فتح Rviz
    ])
