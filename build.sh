#!/bin/bash

# Device Provisioner - Automated Build Script
# This script handles dependency installation and building

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BUILD_TYPE="Release"
USE_CMAKE=true
INSTALL_DEPS=false
RUN_AFTER_BUILD=false

# Print colored output
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Options:
    -h, --help          Show this help message
    -d, --debug         Build in debug mode
    -i, --install-deps  Install dependencies before building
    -m, --makefile      Use Makefile instead of CMake
    -r, --run           Run the application after building (requires sudo)
    -c, --clean         Clean build directories before building
    --install           Install to system after building

Examples:
    $0                  # Standard release build with CMake
    $0 -d               # Debug build
    $0 -i -r            # Install deps, build, and run
    $0 -m               # Build using Makefile instead of CMake

EOF
}

# Detect OS
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
        print_info "Detected OS: $OS $OS_VERSION"
    else
        print_error "Cannot detect OS"
        exit 1
    fi
}

# Install dependencies for Ubuntu/Debian
install_deps_debian() {
    print_info "Installing dependencies for Debian/Ubuntu..."
    
    sudo apt-get update
    sudo apt-get install -y \
        build-essential \
        cmake \
        libcurl4-openssl-dev \
        nlohmann-json3-dev \
        libssl-dev \
        pkg-config
    
    print_success "Dependencies installed"
}

# Install dependencies for RHEL/CentOS/Fedora
install_deps_rhel() {
    print_info "Installing dependencies for RHEL/CentOS/Fedora..."
    
    sudo yum install -y \
        gcc-c++ \
        cmake \
        libcurl-devel \
        json-devel \
        openssl-devel \
        pkg-config
    
    print_success "Dependencies installed"
}

# Install dependencies for Arch Linux
install_deps_arch() {
    print_info "Installing dependencies for Arch Linux..."
    
    sudo pacman -S --needed --noconfirm \
        base-devel \
        cmake \
        curl \
        nlohmann-json \
        openssl
    
    print_success "Dependencies installed"
}

# Install dependencies based on OS
install_dependencies() {
    detect_os
    
    case $OS in
        ubuntu|debian)
            install_deps_debian
            ;;
        rhel|centos|fedora)
            install_deps_rhel
            ;;
        arch|manjaro)
            install_deps_arch
            ;;
        *)
            print_error "Unsupported OS: $OS"
            print_info "Please install dependencies manually:"
            print_info "  - C++17 compiler (g++ or clang++)"
            print_info "  - CMake 3.14+"
            print_info "  - libcurl with SSL support"
            print_info "  - nlohmann-json 3.2.0+"
            exit 1
            ;;
    esac
}

# Check if required commands exist
check_requirements() {
    local missing_deps=false
    
    print_info "Checking build requirements..."
    
    # Check for compiler
    if ! command -v g++ &> /dev/null && ! command -v clang++ &> /dev/null; then
        print_error "No C++ compiler found (g++ or clang++)"
        missing_deps=true
    else
        print_success "C++ compiler found"
    fi
    
    # Check for build system
    if [ "$USE_CMAKE" = true ]; then
        if ! command -v cmake &> /dev/null; then
            print_error "CMake not found"
            missing_deps=true
        else
            print_success "CMake found: $(cmake --version | head -n1)"
        fi
    else
        if ! command -v make &> /dev/null; then
            print_error "Make not found"
            missing_deps=true
        else
            print_success "Make found"
        fi
    fi
    
    # Check for libcurl
    if ! pkg-config --exists libcurl 2>/dev/null; then
        print_error "libcurl not found"
        missing_deps=true
    else
        print_success "libcurl found"
    fi
    
    if [ "$missing_deps" = true ]; then
        print_warning "Missing dependencies detected"
        if [ "$INSTALL_DEPS" = false ]; then
            print_info "Run with -i flag to install dependencies automatically"
            exit 1
        fi
        install_dependencies
    else
        print_success "All requirements satisfied"
    fi
}

# Clean build directories
clean_build() {
    print_info "Cleaning build directories..."
    rm -rf build build-debug bin
    print_success "Build directories cleaned"
}

# Build with CMake
build_cmake() {
    print_info "Building with CMake (${BUILD_TYPE})..."
    
    mkdir -p build
    cd build
    
    cmake -DCMAKE_BUILD_TYPE=${BUILD_TYPE} ..
    make -j$(nproc)
    
    cd ..
    print_success "Build complete: build/bin/device_provisioner"
}

# Build with Makefile
build_makefile() {
    print_info "Building with Makefile (${BUILD_TYPE})..."
    
    if [ "$BUILD_TYPE" = "Debug" ]; then
        make debug
    else
        make release
    fi
    
    print_success "Build complete: bin/device_provisioner"
}

# Run the application
run_application() {
    print_info "Running device provisioner (requires sudo)..."
    
    if [ "$USE_CMAKE" = true ]; then
        if [ -f build/bin/device_provisioner ]; then
            sudo build/bin/device_provisioner
        else
            print_error "Executable not found. Build may have failed."
            exit 1
        fi
    else
        if [ -f bin/device_provisioner ]; then
            sudo bin/device_provisioner
        else
            print_error "Executable not found. Build may have failed."
            exit 1
        fi
    fi
}

# Install to system
install_to_system() {
    print_info "Installing to system..."
    
    if [ "$USE_CMAKE" = true ]; then
        cd build
        sudo make install
        cd ..
    else
        sudo make install
    fi
    
    print_success "Installed to /usr/local/bin/device_provisioner"
}

# Main script
main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -d|--debug)
                BUILD_TYPE="Debug"
                shift
                ;;
            -i|--install-deps)
                INSTALL_DEPS=true
                shift
                ;;
            -m|--makefile)
                USE_CMAKE=false
                shift
                ;;
            -r|--run)
                RUN_AFTER_BUILD=true
                shift
                ;;
            -c|--clean)
                CLEAN_BUILD=true
                shift
                ;;
            --install)
                INSTALL_AFTER_BUILD=true
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    print_info "=== Device Provisioner Build Script ==="
    print_info "Build Type: ${BUILD_TYPE}"
    print_info "Build System: $([ "$USE_CMAKE" = true ] && echo "CMake" || echo "Makefile")"
    
    # Clean if requested
    if [ "$CLEAN_BUILD" = true ]; then
        clean_build
    fi
    
    # Check requirements
    check_requirements
    
    # Build the project
    if [ "$USE_CMAKE" = true ]; then
        build_cmake
    else
        build_makefile
    fi
    
    # Install if requested
    if [ "$INSTALL_AFTER_BUILD" = true ]; then
        install_to_system
    fi
    
    # Run if requested
    if [ "$RUN_AFTER_BUILD" = true ]; then
        run_application
    fi
    
    print_success "=== Build script completed successfully ==="
    
    # Print next steps
    if [ "$RUN_AFTER_BUILD" = false ]; then
        print_info "Next steps:"
        if [ "$USE_CMAKE" = true ]; then
            print_info "  Run: sudo build/bin/device_provisioner"
        else
            print_info "  Run: sudo bin/device_provisioner"
        fi
        print_info "  Install: $([ "$USE_CMAKE" = true ] && echo "cd build && sudo make install" || echo "sudo make install")"
    fi
}

# Run main function
main "$@"