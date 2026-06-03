import os
import xacro
from launch_ros.actions import Node
from launch import LaunchDescription
from launch.conditions import IfCondition
from launch_ros.parameter_descriptions import ParameterFile
from ament_index_python.packages import get_package_share_directory
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription

def process_xacro():
    pkg_go2_description = get_package_share_directory('go2_description')
    xacro_file = os.path.join(pkg_go2_description, 'xacro', 'robot.xacro')
    robot_description_config = xacro.process_file(xacro_file)
    return robot_description_config.toxml()

def generate_launch_description():
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')
    pkg_sim_worlds = get_package_share_directory('sim_worlds')
    pkg_go2_description = get_package_share_directory('go2_description')
    config_path = get_package_share_directory("champ_config")
    
    default_links_param = PathJoinSubstitution([config_path, 'config', 'links', 'links.yaml'])
    default_joints_param = PathJoinSubstitution([config_path, 'config', 'joints', 'joints.yaml'])
    default_gait_param = PathJoinSubstitution([config_path, 'config', 'gait', 'gait.yaml'])

    links_param_arg = DeclareLaunchArgument(
        name="links_param",
        default_value=default_links_param,
        description="Path to links parameter YAML file"
    )
    joints_param_arg = DeclareLaunchArgument(
        name="joints_param",
        default_value=default_joints_param,
        description="Path to joints parameter YAML file"
    )
    gait_param_arg = DeclareLaunchArgument(
        name="gait_param",
        default_value=default_gait_param,
        description="Path to gait parameter YAML file"
    )
    world_file_arg = DeclareLaunchArgument(
        'world_file',
        default_value='exp_room.sdf',
        description='Name of the world file to load'
    )
    rviz_arg = DeclareLaunchArgument(
        'rviz',
        default_value='true', 
        description='Open RViz.'
    )
    
    default_urdf_file = os.path.join(pkg_go2_description, 'urdf', 'go2.urdf')
    urdf_file_arg = DeclareLaunchArgument(
        name='urdf_file',
        default_value=default_urdf_file,
        description="Path to URDF file"
    )

    links_param = ParameterFile(LaunchConfiguration('links_param'), allow_substs=True)
    joints_param = ParameterFile(LaunchConfiguration('joints_param'), allow_substs=True)
    gait_param = ParameterFile(LaunchConfiguration('gait_param'), allow_substs=True)

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={
            'gz_args': PathJoinSubstitution([
                pkg_sim_worlds, 
                'worlds', 
                'drone_world.sdf'
            ])
        }.items(),
    )

    # ROS - Gazebo Bridge
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        output='screen',
        parameters=[{
            'config_file': os.path.join(pkg_go2_description, 'config', 'go2_bridge.yaml'),
            'qos_overrides./tf_static.publisher.durability': 'transient_local',
        }]
    )

    # Robot State Publisher
    robot_desc = process_xacro()
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        namespace='go2',
        output='both',
        parameters=[
            {'use_sim_time': True},
            {'robot_description': robot_desc},
            {'frame_prefix': 'go2/'},  
            {'publish_frequency': 200.0},
        ]
    )
    gz_spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=[
            '-topic', '/go2/robot_description',  # Namespace'e uygun topic
            '-name', 'go2',
            '-allow_renaming', 'true',
            '-y', '1.0',
            '-z', '0.4'
        ]
    )

    pkg_drone_description = get_package_share_directory('drone')
    robot2_urdf = os.path.join(pkg_drone_description, 'model', 'X3','model.sdf')
    with open(robot2_urdf, 'r') as infp:
        robot2_desc = infp.read()

    # # Drone spawn düğümü (düzeltilmiş)
    # gz_spawn_entity_drone = Node(
    #     package='ros_gz_sim',
    #     executable='create',
    #     output='screen',
    #     arguments=[
    #         '-topic', '/X3/robot_description',
    #         '-name', 'X3',
    #         '-allow_renaming', 'true',
    #         '-y', '0.0', '-z', '2.0'
    #     ]
    # )
    # Robot state publisher (düzeltilmiş)
    robot_state_publisher_drone = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='drone_state_publisher',
        namespace='/X3',
        output='both',
        parameters=[
            {'use_sim_time': True},
            {'robot_description': robot2_desc},
            {'frame_prefix': 'X3/'},
            {'publish_frequency': 200.0},
        ]
    )

    # RViz visualization node
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', os.path.join(pkg_go2_description, 'config', 'go2.rviz')],
        condition=IfCondition(LaunchConfiguration('rviz'))
    )

    quadruped_controller_node = Node(
        package="champ_base",
        executable="quadruped_controller_node",
        output="screen",
        parameters=[
            {"use_sim_time": True},
            {"gazebo": True},
            {"publish_joint_states": False},
            {"publish_foot_contacts": False},
            {"publish_joint_control": True},
            {"joint_controller_topic": "/go2/joint_trajectory"},
            {"urdf": LaunchConfiguration('urdf_file')},
            links_param,
            joints_param,
            gait_param
        ],
        # remappings=[("/cmd_vel/smooth", "/cmd_vel")],
    )

    return LaunchDescription([
        world_file_arg,
        rviz_arg,
        urdf_file_arg,
        links_param_arg,
        joints_param_arg,
        gait_param_arg,
        gz_sim,
        bridge,
        robot_state_publisher,
        robot_state_publisher_drone,
        gz_spawn_entity,
        # gz_spawn_entity_drone,  # ✅ Yinelenen satır kaldırıldı
        quadruped_controller_node,
        rviz,
    ])