cmake_minimum_required(VERSION 3.5)

# Following directive defines the project name.
project(sim_worlds)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY worlds/
  DESTINATION share/${PROJECT_NAME}/worlds
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_environment_hooks("${CMAKE_CURRENT_SOURCE_DIR}/hooks/${PROJECT_NAME}.dsv.in")
ament_environment_hooks("${CMAKE_CURRENT_SOURCE_DIR}/hooks/${PROJECT_NAME}.sh.in")

ament_package()
