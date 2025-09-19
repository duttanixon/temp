cmake_minimum_required(VERSION 3.14)
project(DeviceProvisioner VERSION 1.0.0 LANGUAGES CXX)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Set build type if not specified
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# Compiler flags
set(CMAKE_CXX_FLAGS_DEBUG "-g -O0 -Wall -Wextra -Wpedantic")
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -Wall -Wextra -Wpedantic -DNDEBUG")

# Find required packages
find_package(CURL REQUIRED)
find_package(Threads REQUIRED)

# Find nlohmann_json
find_package(nlohmann_json 3.2.0 REQUIRED)

# Create executable
add_executable(device_provisioner device_provisioner.cpp)

# Link libraries
target_link_libraries(device_provisioner 
    PRIVATE 
        CURL::libcurl
        nlohmann_json::nlohmann_json
        Threads::Threads
        stdc++fs  # For filesystem support
)

# Set executable properties
set_target_properties(device_provisioner PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
)

# Installation rules
install(TARGETS device_provisioner
    RUNTIME DESTINATION bin
)

# Add a custom target to run the provisioner (requires sudo)
add_custom_target(run
    COMMAND sudo ${CMAKE_BINARY_DIR}/bin/device_provisioner
    DEPENDS device_provisioner
    COMMENT "Running device provisioner (requires sudo)"
)

# Print configuration summary
message(STATUS "")
message(STATUS "Configuration Summary:")
message(STATUS "  Build Type: ${CMAKE_BUILD_TYPE}")
message(STATUS "  C++ Standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "  Compiler: ${CMAKE_CXX_COMPILER}")
message(STATUS "  CURL Found: ${CURL_FOUND}")
message(STATUS "  nlohmann_json Found: ${nlohmann_json_FOUND}")
message(STATUS "")