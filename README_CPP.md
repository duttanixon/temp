# Device Provisioner - C++ Implementation

A robust C++ application for provisioning IoT devices with certificates and configuration for AWS IoT Core connectivity.

## Features

- **Directory Management**: Creates and manages required directory structure with proper permissions
- **MAC Address Detection**: Automatically detects device MAC address from network interfaces
- **Certificate Management**: Downloads and manages device certificates and keys from API
- **AWS IoT Integration**: Configures device for AWS IoT Core connectivity
- **Hostname Management**: Updates system hostname based on certificate information
- **Configuration Generation**: Creates AWS IoT device configuration in JSON format

## Prerequisites

### System Requirements
- Linux-based operating system (Ubuntu, Debian, etc.)
- C++17 compatible compiler (GCC 7+ or Clang 5+)
- CMake 3.14 or higher
- Root/sudo privileges for system operations

### Required Libraries

Install the following dependencies:

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    cmake \
    libcurl4-openssl-dev \
    nlohmann-json3-dev \
    libssl-dev

# For CentOS/RHEL/Fedora
sudo yum install -y \
    gcc-c++ \
    cmake \
    libcurl-devel \
    json-devel \
    openssl-devel
```

## Building the Application

### Standard Build

```bash
# Clone or download the source code
mkdir build
cd build
cmake ..
make -j$(nproc)
```

### Debug Build

```bash
mkdir build-debug
cd build-debug
cmake -DCMAKE_BUILD_TYPE=Debug ..
make -j$(nproc)
```

### Installation

```bash
# From the build directory
sudo make install
```

This will install the binary to `/usr/local/bin/device_provisioner`

## Usage

The application must be run with root privileges:

```bash
sudo ./device_provisioner
```

Or if installed:

```bash
sudo device_provisioner
```

## Application Workflow

1. **Directory Creation**: Creates required directories under `/home/cybercore/` and `/var/log/`
2. **Certificate Check**: Verifies if certificates already exist
3. **MAC Address Detection**: Retrieves device MAC address from network interfaces
4. **Certificate Download**: Downloads device certificates using the MAC address
5. **Amazon Root CA**: Downloads AWS Root CA certificate
6. **Permission Setup**: Sets appropriate file permissions (600 for keys, 644 for certificates)
7. **Hostname Configuration**: Updates system hostname to match certificate
8. **Configuration File**: Creates AWS IoT configuration at `/etc/dc-configs/config.json`

## Directory Structure

After successful provisioning:

```
/home/cybercore/
├── application/
├── certificates/
│   ├── *.pem          (Device certificate)
│   ├── *.key          (Private key)
│   └── AmazonRootCA1.pem
├── configs/
├── db/
└── models/

/var/log/
└── edge-analytics/

/etc/
└── dc-configs/
    └── config.json    (AWS IoT configuration)
```

## Configuration

The application uses the following hardcoded configuration:

- **API Endpoint**: `https://platform.cybercore.co.jp/api/v2/devices/certificates-for-devices`
- **AWS IoT Endpoint**: `a23bd20ty64577-ats.iot.ap-northeast-1.amazonaws.com`
- **Amazon Root CA URL**: `https://www.amazontrust.com/repository/AmazonRootCA1.pem`

To modify these settings, edit the constants in `device_provisioner.cpp` and rebuild.

## Error Handling

The application includes comprehensive error handling:
- Network connectivity issues
- File system permissions
- Certificate download failures
- Invalid MAC address detection
- JSON parsing errors

All errors are logged with descriptive messages using color-coded output:
- ✓ Green checkmarks for successful operations
- ✗ Red crosses for errors

## Security Considerations

- Private keys are stored with 600 permissions (owner read/write only)
- Certificates are stored with 644 permissions (owner write, all read)
- API key is embedded in the binary (consider using environment variables for production)
- All HTTPS connections use SSL/TLS verification

## Troubleshooting

### Common Issues

1. **Permission Denied Errors**
   - Ensure the application is run with sudo
   - Verify the cybercore user exists

2. **Network Interface Not Found**
   - Check available interfaces: `ls /sys/class/net/`
   - Ensure at least one network interface is up

3. **Certificate Download Fails**
   - Verify network connectivity
   - Check if the MAC address is registered in the system
   - Ensure the API key is valid

4. **Build Errors**
   - Verify all dependencies are installed
   - Check compiler version supports C++17
   - Ensure nlohmann-json version is 3.2.0 or higher

### Debug Mode

For detailed debugging information:

```bash
# Build in debug mode
cmake -DCMAKE_BUILD_TYPE=Debug ..
make

# Run with strace for system call debugging
sudo strace -e trace=file ./device_provisioner

# Check generated config file
cat /etc/dc-configs/config.json | jq .
```

## Development

### Code Structure

The application is organized as a single class `DeviceProvisioner` with the following key methods:

- `createDirectories()`: Sets up directory structure
- `getMacAddress()`: Detects network interface MAC
- `downloadCertificates()`: Retrieves certificates from API
- `checkAndUpdateHostname()`: Manages system hostname
- `createConfigFile()`: Generates AWS IoT configuration

### Adding New Features

To extend the application:

1. Add new methods to the `DeviceProvisioner` class
2. Update the `run()` method to include new steps
3. Add appropriate error handling
4. Update this README

### Testing

```bash
# Run unit tests (if implemented)
cd build
ctest

# Manual testing checklist
- [ ] Directory creation with correct permissions
- [ ] MAC address detection on different interfaces
- [ ] Certificate download and storage
- [ ] Hostname update verification
- [ ] Configuration file generation
- [ ] Error handling for network failures
```

## License

[Specify your license here]

## Support

For issues or questions, please contact the development team or create an issue in the project repository.

## Version History

- **1.0.0** - Initial C++ implementation
  - Full feature parity with Python version
  - Enhanced error handling
  - Improved performance

## Authors

[Your name/team here]

---

**Note**: This application will trigger a system reboot after updating the hostname. Ensure all work is saved before running.