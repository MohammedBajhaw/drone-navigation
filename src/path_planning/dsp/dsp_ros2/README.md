# DSP: D*+ path planner on a uniformly spaced 3D or 2D grid integrated with Octomap and slam_toolbox

This is an implementation of D*+ on a uniformly spaced 3D or 2D grid for use in global path planning.
- **Maps:** Uses `octomap` for 3D and `slam_toolbox` for 2D mapping (instead of cartographer).
- **ROS2 Support:** Tested on ROS2 Humble & Jazzy.
- **Repository:** [alitekes1/dsp_ros2](https://github.com/alitekes1/dsp_ros2)

# 1. Installation (ROS2)

## Install the dsl library
```bash
cd
# Clone the DSL library
git clone https://github.com/jhu-asco/dsl.git
cd dsl
git checkout 61cf588668309e87de209cd95f03a0f792a16c33
mkdir build
cd build
cmake ..
sudo make install
```

## Clone and build DSP in your ROS2 workspace
Assuming your ROS2 workspace is `~/ros2_ws`:
```bash
cd ~/ros2_ws/src
git clone https://github.com/alitekes1/dsp_ros2.git
cd ..
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

# 2. Quickstart

- Launch your preferred map server:
  - For 2D: `slam_toolbox`
  - For 3D: `octomap_server`
- Ensure that `tf` is properly configured between the map frame and your odometry.
- Launch DSP:
```bash
ros2 launch dsp dsp_3d_start.launch.py
```
- Open RViz2 and add the `/dsp/path`, `/dsp/spline_path`, and `/dsp/occupancy_map` topics for visualization.
- To set a goal, use the "2D Nav Goal" tool in RViz2 and publish to `/dsp/set_goal`.

**Note:** The goal pose must be inside the map.

# 3. Topics
### Subscribed
* `/dsp/set_start`: [`geometry_msgs/Point`] Used to set the start position.
* `/dsp/set_goal`: [`geometry_msgs/Point`] Used to set the goal position.
* `/octomap_full`: [`octomap_msgs/Octomap`] Used for 3D map input.
* `/map`: [`nav_msgs/OccupancyGrid`] Used for 2D map input (from slam_toolbox).

### Published
* `/dsp/occupancy_map`: [`visualization_msgs/Marker`] Occupancy grid for RViz2 visualization.
* `/dsp/path`: [`nav_msgs/Path`] The generated path from start to goal.
* `/dsp/spline_path`: [`nav_msgs/Path`] Smoothed (splined) path.

# 4. Parameters
* `map_topic`: [`string`] The topic of the input map.
* `lower_thresh`: [`int`] Threshold for free space in 2D map.
* `upper_thresh`: [`int`] Threshold for occupied space in 2D map.
* `risk`: [`int`] Number of voxels next to occupied space considered as risk area.
* `use_odometry`: [`bool`] Set to true to use odometry for start position.
* `use_3d`: [`bool`] Set to true for 3D planning.
* `odom_topic`: [`string`] Odometry topic.
* `odom_frame_id`: [`string`] Frame in which to plan.
* `DSP_UNKNOWN`: [`int`] Traversal cost for unknown voxels.

# 5. Example Launch & RViz2 Usage

## 1. Launching
First, start your map server (e.g., slam_toolbox or octomap_server). Then launch DSP:
```bash
ros2 launch dsp dsp_3d_start.launch.py
```

## 2. Visualization with RViz2
- Start RViz2:
  ```bash
  rviz2
  ```
- Add the following topics:
  - `/dsp/path` (nav_msgs/Path)
  - `/dsp/spline_path` (nav_msgs/Path)
  - `/dsp/occupancy_map` (visualization_msgs/Marker)
- Use the "2D Nav Goal" tool to set a goal on the map. This will automatically publish to the `/dsp/set_goal` topic.

## 3. Changing Parameters
Default parameters can be overridden in the launch file or via the command line:
```bash
ros2 launch dsp dsp_3d_start.launch.py use_3d:=false map_topic:=/map
```

# 6. Troubleshooting

- **Map or path not visible:**  
  - Check that the correct `frame_id` (e.g., `odom` or `map`) is selected in RViz2.
  - Ensure map topics (e.g., `/map`, `/octomap_full`) are being received by the DSP node.
- **No path found to the goal:**  
  - Make sure the goal is inside the map and reachable.
  - Try lowering the `risk` or `upper_thresh` parameter values.
- **TF errors:**  
  - Ensure there is a valid TF connection between odometry and map frames.
- **Dependency errors:**  
  - Run `rosdep install --from-paths src --ignore-src -r -y` again.
  - Make sure the DSL library is installed correctly.

# 7. Citation
If you use the $D^*_{+}$ path planner in your work, please cite the [$D^*_{+}$ paper](https://arxiv.org/abs/2112.05563):
```bibtex
@misc{karlsson2021d,
      title={$D^*_{+}$: A Generic Platform-Agnostic and Risk-Aware Path Planing Framework with an Expandable Grid}, 
      author={Samuel Karlsson and Anton Koval and Christoforos Kanellakis and Ali-akbar Agha-mohammadi and George Nikolakopoulos},
      year={2021},
      eprint={2112.05563},
      archivePrefix={arXiv},
      primaryClass={cs.RO}
}
```
