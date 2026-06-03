#!/bin/bash

export MODEL_PATHS="/home/$USER/oadrone_ws/src/simulation/sim_worlds/worlds:/home/$USER/oadrone_ws/src/simulation/sim_worlds/worlds/models:/home/$USER/oadrone_ws/src/simulation/sim_worlds/worlds/models/collapsed_fire_station/materials/textures:/home/$USER/oadrone_ws/src/simulation/sim_worlds/worlds/models/collapsed_fire_station/meshes:/home/$USER/.gazebo/models"
export IGN_GAZEBO_RESOURCE_PATH=$IGN_GAZEBO_RESOURCE_PATH:$MODEL_PATHS
export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:$MODEL_PATHS

# --- خيار اختيار البيئة (World Selection) ---
# الاستخدام: ./start_mission.sh [mine|cave|room]
WORLD_NAME="${1:-cave}"

case $WORLD_NAME in
    "mine")
        WORLD_PATH="/home/$USER/oadrone_ws/src/simulation/sim_worlds/worlds/edgar_mine/edgar_mine.sdf"
        SPAWN_ARGS="x:=70.0 y:=0.0 z:=0.5"
        echo "⚒️ Switching to MINE environment..."
        ;;
    "disaster")
        WORLD_PATH="/home/$USER/oadrone_ws/src/simulation/sim_worlds/worlds/disaster_mine.sdf"
        SPAWN_ARGS="x:=70.0 y:=0.0 z:=0.5"
        echo "🆘 Switching to DISASTER MINE rescue environment..."
        ;;
    "warehouse")
        WORLD_PATH="/home/$USER/oadrone_ws/src/simulation/sim_worlds/worlds/sim_world/Warehouse/tugbot_warehouse.sdf"
        SPAWN_ARGS="x:=0.0 y:=0.0 z:=0.5"
        echo "🏭 Switching to WAREHOUSE environment..."
        ;;
    "room")
        WORLD_PATH="/home/$USER/oadrone_ws/src/simulation/sim_worlds/worlds/exp_room.sdf"
        SPAWN_ARGS="x:=0.0 y:=0.0 z:=0.5"
        echo "🏠 Switching to EXPERIMENTAL ROOM environment..."
        ;;
    "house" | "ruins")
        WORLD_PATH="/home/$USER/oadrone_ws/src/simulation/sim_worlds/worlds/collapsed_building.sdf"
        SPAWN_ARGS="x:=0.0 y:=0.0 z:=0.5"
        echo "🏚️ Switching to COLLAPSED BUILDING environment..."
        ;;
    "office")
        WORLD_PATH="/home/$USER/oadrone_ws/src/simulation/sim_worlds/worlds/disaster_office.sdf"
        SPAWN_ARGS="x:=2.0 y:=1.0 z:=0.5"
        echo "🏢 Switching to WILLOW GARAGE OFFICE environment..."
        ;;
    "gas")
        WORLD_PATH="/home/$USER/oadrone_ws/src/simulation/sim_worlds/worlds/disaster_gas.sdf"
        SPAWN_ARGS="x:=5.0 y:=-5.0 z:=0.5"
        echo "⛽ Switching to GAS STATION environment..."
        ;;
    "park")
        WORLD_PATH="/home/$USER/oadrone_ws/src/simulation/sim_worlds/worlds/disaster_park.sdf"
        SPAWN_ARGS="x:=0.0 y:=0.0 z:=0.5"
        echo "🌲 Switching to PLAYGROUND PARK environment..."
        ;;
    "fire")
        WORLD_PATH="/home/$USER/oadrone_ws/src/simulation/sim_worlds/worlds/disaster_fire_station.sdf"
        SPAWN_ARGS="x:=0.0 y:=0.0 z:=3.0"
        echo "🚒 Switching to COLLAPSED FIRE STATION environment..."
        ;;
    *)
        WORLD_PATH="/home/$USER/oadrone_ws/src/simulation/sim_worlds/worlds/custom_cave.sdf"
        SPAWN_ARGS="x:=0.0 y:=0.0 z:=0.5"
        echo "🦇 Using default CAVE environment..."
        ;;
esac

echo "🚀 Starting LIGHTWEIGHT OA-Drone Mission..."

# 0. Cleanup old processes
echo "🧹 Cleaning up old simulation processes..."
pkill -9 -f "ign gazebo" || true
sleep 2

# 1. Gazebo
gnome-terminal --tab --title="Gazebo" -- bash -c "source install/setup.bash; export IGN_GAZEBO_RESOURCE_PATH=$IGN_GAZEBO_RESOURCE_PATH; ros2 launch sim_bringup iris.gazebo.launch.py world:=$WORLD_PATH $SPAWN_ARGS; exec bash"
sleep 5

# 2. TF Bridge
gnome-terminal --tab --title="TF Bridge" -- bash -c "source install/setup.bash; python3 run_scripts/odom_to_tf.py; exec bash"

# 3. Mapping
gnome-terminal --tab --title="Mapping" -- bash -c "source install/setup.bash; ros2 launch dsp iris_dsp_mapping.launch.py; exec bash"
sleep 3

# 4. Controller
gnome-terminal --tab --title="Controller" -- bash -c "source install/setup.bash; python3 run_scripts/iris_dsp_controller.py; exec bash"

# 5. Explorer
gnome-terminal --tab --title="Explorer" -- bash -c "source install/setup.bash; python3 run_scripts/auto_explorer.py; exec bash"

echo "✅ System stable and optimized."
