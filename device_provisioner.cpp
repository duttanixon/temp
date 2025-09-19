// device_provisioner.cpp
#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <filesystem>
#include <chrono>
#include <thread>
#include <regex>
#include <cstring>
#include <algorithm>
#include <memory>
#include <iomanip>

// System headers
#include <sys/stat.h>
#include <unistd.h>
#include <pwd.h>
#include <grp.h>

// For network operations
#include <curl/curl.h>

// For JSON handling
#include <nlohmann/json.hpp>

namespace fs = std::filesystem;
using json = nlohmann::json;

// ANSI color codes for output
const std::string GREEN = "\033[32m";
const std::string RED = "\033[31m";
const std::string RESET = "\033[0m";

class DeviceProvisioner {
private:
    // Configuration constants
    const std::vector<std::string> base_dirs = {
        "/home/cybercore/application",
        "/home/cybercore/certificates",
        "/home/cybercore/configs",
        "/home/cybercore/db",
        "/home/cybercore/models",
        "/var/log/edge-analytics"
    };
    
    const std::string certificates_dir = "/home/cybercore/certificates";
    const std::string api_url = "https://platform.cybercore.co.jp/api/v2/devices/certificates-for-devices";
    const std::string api_key = "k-TzDzlJew9s3Z_NXJprY4cwgL0IeiaQeZ8fHVx2N8M";
    const std::string amazon_root_ca_url = "https://www.amazontrust.com/repository/AmazonRootCA1.pem";
    const std::string aws_endpoint = "a23bd20ty64577-ats.iot.ap-northeast-1.amazonaws.com";

    // Helper struct for download response
    struct MemoryStruct {
        char* memory;
        size_t size;
    };

    // CURL write callback
    static size_t WriteMemoryCallback(void* contents, size_t size, size_t nmemb, void* userp) {
        size_t realsize = size * nmemb;
        struct MemoryStruct* mem = (struct MemoryStruct*)userp;

        char* ptr = (char*)realloc(mem->memory, mem->size + realsize + 1);
        if (!ptr) {
            std::cerr << "Not enough memory (realloc returned NULL)" << std::endl;
            return 0;
        }

        mem->memory = ptr;
        memcpy(&(mem->memory[mem->size]), contents, realsize);
        mem->size += realsize;
        mem->memory[mem->size] = 0;

        return realsize;
    }

    void printSuccess(const std::string& message) {
        std::cout << GREEN << "✓ " << RESET << message << std::endl;
    }

    void printError(const std::string& message) {
        std::cout << RED << "✗ " << RESET << message << std::endl;
    }

    std::string urlEncode(const std::string& value) {
        std::ostringstream escaped;
        escaped.fill('0');
        escaped << std::hex;

        for (char c : value) {
            if (c == ':') {
                escaped << "%3A";
            } else {
                escaped << c;
            }
        }

        return escaped.str();
    }

    std::string extractFilenameFromUrl(const std::string& url, const std::string& fallback) {
        size_t lastSlash = url.find_last_of('/');
        if (lastSlash != std::string::npos && lastSlash < url.length() - 1) {
            std::string filename = url.substr(lastSlash + 1);
            
            // Check for query parameters and remove them
            size_t queryPos = filename.find('?');
            if (queryPos != std::string::npos) {
                filename = filename.substr(0, queryPos);
            }
            
            if (!filename.empty() && filename.find('.') != std::string::npos) {
                return filename;
            }
        }
        return fallback;
    }

    bool downloadFile(const std::string& url, const std::string& filepath) {
        CURL* curl;
        CURLcode res;
        FILE* fp;
        
        curl = curl_easy_init();
        if (!curl) {
            printError("Failed to initialize CURL");
            return false;
        }

        fp = fopen(filepath.c_str(), "wb");
        if (!fp) {
            printError("Failed to open file for writing: " + filepath);
            curl_easy_cleanup(curl);
            return false;
        }

        curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, fwrite);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, fp);
        curl_easy_setopt(curl, CURLOPT_TIMEOUT, 30L);
        curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 1L);
        curl_easy_setopt(curl, CURLOPT_SSL_VERIFYHOST, 2L);

        res = curl_easy_perform(curl);
        
        fclose(fp);
        curl_easy_cleanup(curl);

        if (res != CURLE_OK) {
            printError("CURL error: " + std::string(curl_easy_strerror(res)));
            fs::remove(filepath);
            return false;
        }

        return true;
    }

    bool setOwnership(const std::string& path, const std::string& user, const std::string& group) {
        struct passwd* pwd = getpwnam(user.c_str());
        struct group* grp = getgrnam(group.c_str());
        
        if (!pwd || !grp) {
            printError("Failed to get user/group information");
            return false;
        }

        if (chown(path.c_str(), pwd->pw_uid, grp->gr_gid) != 0) {
            printError("Failed to set ownership for: " + path);
            return false;
        }

        return true;
    }

public:
    bool createDirectories() {
        std::cout << "Creating directories..." << std::endl;
        
        for (const auto& dir : base_dirs) {
            try {
                fs::create_directories(dir);
                printSuccess("Directory created/verified: " + dir);
            } catch (const fs::filesystem_error& e) {
                printError("Error creating directory " + dir + ": " + e.what());
                return false;
            }
        }

        // Set ownership to cybercore:cybercore
        std::cout << "Setting directory ownership..." << std::endl;
        for (const auto& dir : base_dirs) {
            if (!setOwnership(dir, "cybercore", "cybercore")) {
                return false;
            }
            printSuccess("Ownership set to cybercore:cybercore for: " + dir);
        }

        return true;
    }

    std::string getMacAddress() {
        std::cout << "Detecting MAC address..." << std::endl;
        
        const std::string net_path = "/sys/class/net/";
        if (!fs::exists(net_path)) {
            printError("Network interface path " + net_path + " not found");
            return "";
        }

        std::vector<std::pair<std::string, std::string>> interface_priorities = {
            {"enp", "ethernet (enp series)"},
            {"eth", "ethernet (eth series)"},
            {"wlan", "wireless (wlan series)"}
        };

        for (const auto& [prefix, description] : interface_priorities) {
            for (const auto& entry : fs::directory_iterator(net_path)) {
                std::string iface = entry.path().filename().string();
                
                if (iface.find(prefix) == 0) {
                    std::string mac = readMacFromInterface(iface);
                    if (!mac.empty()) {
                        printSuccess("MAC address found from " + iface + ": " + mac);
                        return mac;
                    }
                }
            }
        }

        printError("No suitable network interface found");
        return "";
    }

    std::string readMacFromInterface(const std::string& interface) {
        std::string address_file = "/sys/class/net/" + interface + "/address";
        
        if (!fs::exists(address_file)) {
            return "";
        }

        std::ifstream file(address_file);
        if (!file.is_open()) {
            return "";
        }

        std::string mac_address;
        std::getline(file, mac_address);
        file.close();

        // Validate MAC address format
        if (mac_address.length() == 17 && 
            std::count(mac_address.begin(), mac_address.end(), ':') == 5) {
            return mac_address;
        }

        return "";
    }

    bool checkCertificatesExist() {
        std::cout << "Checking for existing certificates..." << std::endl;
        
        int pem_count = 0, key_count = 0;
        
        for (const auto& entry : fs::directory_iterator(certificates_dir)) {
            std::string filename = entry.path().filename().string();
            if (filename.find(".pem") != std::string::npos) pem_count++;
            if (filename.find(".key") != std::string::npos) key_count++;
        }

        if (pem_count > 0 && key_count > 0) {
            printSuccess("Certificates found: " + std::to_string(pem_count) + 
                        " .pem files, " + std::to_string(key_count) + " .key files");
            return true;
        } else {
            printError("Certificates missing: " + std::to_string(pem_count) + 
                      " .pem files, " + std::to_string(key_count) + " .key files");
            return false;
        }
    }

    bool downloadCertificates(const std::string& mac_address) {
        std::cout << "Downloading certificates for MAC address: " << mac_address << std::endl;
        
        std::string encoded_mac = urlEncode(mac_address);
        std::string url = api_url + "?device_identifier=" + encoded_mac;
        
        CURL* curl;
        CURLcode res;
        struct MemoryStruct chunk = {nullptr, 0};
        
        curl_global_init(CURL_GLOBAL_DEFAULT);
        curl = curl_easy_init();
        
        if (!curl) {
            printError("Failed to initialize CURL");
            return false;
        }

        struct curl_slist* headers = nullptr;
        headers = curl_slist_append(headers, ("x-api-key: " + api_key).c_str());
        
        curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteMemoryCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, (void*)&chunk);
        curl_easy_setopt(curl, CURLOPT_TIMEOUT, 30L);
        
        std::cout << "Making API request to: " << url << std::endl;
        res = curl_easy_perform(curl);
        
        curl_slist_free_all(headers);
        curl_easy_cleanup(curl);
        
        if (res != CURLE_OK) {
            printError("API request failed: " + std::string(curl_easy_strerror(res)));
            if (chunk.memory) free(chunk.memory);
            curl_global_cleanup();
            return false;
        }

        printSuccess("API response received");
        
        // Parse JSON response
        try {
            json data = json::parse(chunk.memory);
            
            std::string certificate_url = data.value("certificate_url", "");
            std::string private_key_url = data.value("private_key_url", "");
            std::string device_id = data.value("device_id", "");
            
            if (certificate_url.empty() || private_key_url.empty()) {
                printError("Certificate or private key URL not found in response");
                if (chunk.memory) free(chunk.memory);
                curl_global_cleanup();
                return false;
            }
            
            // Download certificate
            std::string cert_filename = extractFilenameFromUrl(certificate_url, "certificate.pem");
            std::string cert_path = certificates_dir + "/" + cert_filename;
            
            std::cout << "Downloading certificate to: " << cert_path << std::endl;
            if (!downloadFile(certificate_url, cert_path)) {
                if (chunk.memory) free(chunk.memory);
                curl_global_cleanup();
                return false;
            }
            printSuccess("Certificate downloaded successfully");
            
            // Download private key
            std::string key_filename = extractFilenameFromUrl(private_key_url, "private.key");
            std::string key_path = certificates_dir + "/" + key_filename;
            
            std::cout << "Downloading private key to: " << key_path << std::endl;
            if (!downloadFile(private_key_url, key_path)) {
                if (chunk.memory) free(chunk.memory);
                curl_global_cleanup();
                return false;
            }
            printSuccess("Private key downloaded successfully");
            
            printSuccess("All certificates downloaded successfully");
            std::cout << "Device ID: " << device_id << std::endl;
            std::cout << "MAC Address: " << data.value("mac_address", "") << std::endl;
            std::cout << "Expires at: " << data.value("expires_at", "") << std::endl;
            
        } catch (const json::exception& e) {
            printError("Failed to parse API response: " + std::string(e.what()));
            if (chunk.memory) free(chunk.memory);
            curl_global_cleanup();
            return false;
        }
        
        if (chunk.memory) free(chunk.memory);
        curl_global_cleanup();
        return true;
    }

    bool downloadAmazonRootCA() {
        std::cout << "Downloading Amazon Root CA certificate..." << std::endl;
        
        std::string amazon_ca_path = certificates_dir + "/AmazonRootCA1.pem";
        
        if (fs::exists(amazon_ca_path)) {
            printSuccess("Amazon Root CA already exists: " + amazon_ca_path);
            return true;
        }
        
        std::cout << "Downloading from: " << amazon_root_ca_url << std::endl;
        if (!downloadFile(amazon_root_ca_url, amazon_ca_path)) {
            printError("Failed to download Amazon Root CA");
            return false;
        }
        
        printSuccess("Amazon Root CA downloaded: " + amazon_ca_path);
        return true;
    }

    bool setPermissions() {
        std::cout << "Setting file permissions..." << std::endl;
        
        try {
            // Set certificates directory permission to 700
            fs::permissions(certificates_dir, 
                          fs::perms::owner_all | 
                          fs::perms::group_all | fs::perms::others_all,
                          fs::perm_options::remove);
            fs::permissions(certificates_dir, fs::perms::owner_all);
            printSuccess("Set directory permission 700 for: " + certificates_dir);
            
            // Set permissions for .key and .pem files
            for (const auto& entry : fs::directory_iterator(certificates_dir)) {
                std::string filename = entry.path().string();
                
                if (filename.find(".key") != std::string::npos) {
                    fs::permissions(filename, 
                                  fs::perms::owner_read | fs::perms::owner_write);
                    printSuccess("Set permission 600 for key file: " + filename);
                } else if (filename.find(".pem") != std::string::npos) {
                    fs::permissions(filename, 
                                  fs::perms::owner_read | fs::perms::owner_write |
                                  fs::perms::group_read | fs::perms::others_read);
                    printSuccess("Set permission 644 for certificate file: " + filename);
                }
            }
            
            return true;
        } catch (const fs::filesystem_error& e) {
            printError("Error setting permissions: " + std::string(e.what()));
            return false;
        }
    }

    std::string extractHostnameFromCertificate() {
        std::cout << "Extracting hostname from certificate..." << std::endl;
        
        for (const auto& entry : fs::directory_iterator(certificates_dir)) {
            std::string filename = entry.path().filename().string();
            
            // Skip Amazon Root CA
            if (filename == "AmazonRootCA1.pem") continue;
            
            if (filename.find(".pem") != std::string::npos) {
                // Extract hostname using regex: look for pattern _HOSTNAME.pem
                std::regex pattern("_([A-Za-z0-9\\-]+)\\.pem$");
                std::smatch match;
                
                if (std::regex_search(filename, match, pattern)) {
                    std::string hostname = match[1];
                    printSuccess("Hostname extracted from certificate: " + hostname);
                    return hostname;
                }
            }
        }
        
        printError("Could not extract hostname from certificate filename");
        return "";
    }

    std::string getCurrentHostname() {
        char hostname[256];
        if (gethostname(hostname, sizeof(hostname)) == 0) {
            std::string current_hostname(hostname);
            std::cout << "Current system hostname: " << current_hostname << std::endl;
            return current_hostname;
        }
        
        printError("Error getting current hostname");
        return "";
    }

    bool updateHostname(const std::string& new_hostname) {
        std::cout << "Updating system hostname to: " << new_hostname << std::endl;
        
        try {
            // Update /etc/hostname
            std::cout << "Updating /etc/hostname..." << std::endl;
            std::ofstream hostname_file("/etc/hostname");
            if (!hostname_file.is_open()) {
                printError("Failed to open /etc/hostname");
                return false;
            }
            hostname_file << new_hostname << std::endl;
            hostname_file.close();
            printSuccess("/etc/hostname updated");
            
            // Update /etc/hosts
            std::cout << "Updating /etc/hosts..." << std::endl;
            std::ifstream hosts_in("/etc/hosts");
            std::vector<std::string> lines;
            bool hostname_updated = false;
            
            if (hosts_in.is_open()) {
                std::string line;
                while (std::getline(hosts_in, line)) {
                    if (line.find("127.0.1.1") == 0) {
                        lines.push_back("127.0.1.1\t" + new_hostname);
                        hostname_updated = true;
                    } else {
                        lines.push_back(line);
                    }
                }
                hosts_in.close();
            }
            
            if (!hostname_updated) {
                lines.push_back("127.0.1.1\t" + new_hostname);
            }
            
            std::ofstream hosts_out("/etc/hosts");
            if (!hosts_out.is_open()) {
                printError("Failed to open /etc/hosts for writing");
                return false;
            }
            
            for (const auto& line : lines) {
                hosts_out << line << std::endl;
            }
            hosts_out.close();
            printSuccess("/etc/hosts updated");
            
            std::cout << "Hostname files updated. Rebooting system to apply changes..." << std::endl;
            std::cout << "System will reboot in 5 seconds..." << std::endl;
            
            std::this_thread::sleep_for(std::chrono::seconds(5));
            
            // Reboot the system
            system("reboot");
            
            return true;
            
        } catch (const std::exception& e) {
            printError("Error updating hostname: " + std::string(e.what()));
            return false;
        }
    }

    bool checkAndUpdateHostname() {
        std::cout << "Checking hostname compatibility..." << std::endl;
        
        std::string cert_hostname = extractHostnameFromCertificate();
        if (cert_hostname.empty()) {
            printError("Cannot proceed without certificate hostname");
            return false;
        }
        
        std::string current_hostname = getCurrentHostname();
        if (current_hostname.empty()) {
            printError("Cannot get current hostname");
            return false;
        }
        
        if (current_hostname == cert_hostname) {
            printSuccess("Hostname matches certificate: " + current_hostname);
            return true;
        } else {
            printError("Hostname mismatch - Current: " + current_hostname + 
                      ", Certificate: " + cert_hostname);
            return updateHostname(cert_hostname);
        }
    }

    bool createConfigFile() {
        std::cout << "Checking/creating device configuration file..." << std::endl;
        
        const std::string config_dir = "/etc/dc-configs";
        const std::string config_file = config_dir + "/config.json";
        
        // Extract hostname from certificate for thing-name
        std::string cert_hostname = extractHostnameFromCertificate();
        if (cert_hostname.empty()) {
            printError("Cannot create config without certificate hostname");
            return false;
        }
        
        // Find certificate and key files
        std::string cert_path, key_path;
        const std::string root_ca_path = certificates_dir + "/AmazonRootCA1.pem";
        
        for (const auto& entry : fs::directory_iterator(certificates_dir)) {
            std::string filename = entry.path().string();
            
            if (filename.find(".pem") != std::string::npos && 
                filename != root_ca_path) {
                cert_path = filename;
            } else if (filename.find(".key") != std::string::npos) {
                key_path = filename;
            }
        }
        
        if (cert_path.empty() || key_path.empty()) {
            printError("Certificate or key files not found");
            return false;
        }
        
        // Create the configuration JSON
        json config = {
            {"endpoint", aws_endpoint},
            {"cert", cert_path},
            {"key", key_path},
            {"root-ca", root_ca_path},
            {"thing-name", cert_hostname},
            {"logging", {
                {"enable-sdk-logging", true},
                {"level", "DEBUG"},
                {"type", "STDOUT"},
                {"file", ""}
            }},
            {"jobs", {
                {"enabled", true},
                {"handler-directory", ""}
            }},
            {"tunneling", {
                {"enabled", false}
            }},
            {"device-defender", {
                {"enabled", false},
                {"interval", 300}
            }},
            {"fleet-provisioning", {
                {"enabled", false},
                {"template-name", ""},
                {"template-parameters", ""},
                {"csr-file", ""},
                {"device-key", ""}
            }},
            {"samples", {
                {"pub-sub", {
                    {"enabled", false},
                    {"publish-topic", ""},
                    {"publish-file", ""},
                    {"subscribe-topic", ""},
                    {"subscribe-file", ""}
                }}
            }},
            {"config-shadow", {
                {"enabled", false}
            }},
            {"sample-shadow", {
                {"enabled", false},
                {"shadow-name", ""},
                {"shadow-input-file", ""},
                {"shadow-output-file", ""}
            }}
        };
        
        try {
            // Create config directory if it doesn't exist
            fs::create_directories(config_dir);
            printSuccess("Config directory created/verified: " + config_dir);
            
            // Check if config file exists and validate it
            if (fs::exists(config_file)) {
                std::cout << "Config file exists: " << config_file << std::endl;
                
                std::ifstream existing_file(config_file);
                json existing_config;
                existing_file >> existing_config;
                existing_file.close();
                
                // Validate critical fields
                if (existing_config["endpoint"] == config["endpoint"] &&
                    existing_config["cert"] == config["cert"] &&
                    existing_config["key"] == config["key"] &&
                    existing_config["root-ca"] == config["root-ca"] &&
                    existing_config["thing-name"] == config["thing-name"]) {
                    printSuccess("Existing config file is correct");
                    return true;
                } else {
                    printError("Existing config file is incorrect, recreating...");
                }
            }
            
            // Write the config file
            std::ofstream out_file(config_file);
            out_file << std::setw(2) << config << std::endl;
            out_file.close();
            
            printSuccess("Config file created: " + config_file);
            printSuccess("Thing name set to: " + cert_hostname);
            
            return true;
            
        } catch (const std::exception& e) {
            printError("Error creating config file: " + std::string(e.what()));
            return false;
        }
    }

    bool run() {
        std::cout << "=== Device Provisioner Starting ===" << std::endl;
        
        // Step 1: Create directories
        if (!createDirectories()) {
            printError("Failed to create directories. Exiting.");
            return false;
        }
        
        // Step 2: Check if certificates already exist
        bool certificates_exist = false;
        try {
            if (fs::exists(certificates_dir)) {
                certificates_exist = checkCertificatesExist();
            }
        } catch (...) {
            certificates_exist = false;
        }
        
        if (!certificates_exist) {
            // Step 3: Get MAC address
            std::string mac_address = getMacAddress();
            if (mac_address.empty()) {
                printError("Could not detect MAC address. Exiting.");
                return false;
            }
            
            // Step 4: Download certificates
            if (!downloadCertificates(mac_address)) {
                printError("Failed to download certificates. Exiting.");
                return false;
            }
        } else {
            printSuccess("Device certificates already exist. Skipping device certificate download.");
        }
        
        // Step 5: Download Amazon Root CA certificate
        if (!downloadAmazonRootCA()) {
            printError("Failed to download Amazon Root CA certificate. Exiting.");
            return false;
        }
        
        // Step 6: Set file permissions
        if (!setPermissions()) {
            printError("Failed to set file permissions. Exiting.");
            return false;
        }
        
        // Step 7: Check and update hostname if needed
        if (!checkAndUpdateHostname()) {
            printError("Failed to check/update hostname. Exiting.");
            return false;
        }
        
        // Step 8: Create or update device configuration file
        if (!createConfigFile()) {
            printError("Failed to create/update configuration file. Exiting.");
            return false;
        }
        
        std::cout << "=== Device Provisioner Completed Successfully ===" << std::endl;
        return true;
    }
};

int main() {
    try {
        DeviceProvisioner provisioner;
        bool success = provisioner.run();
        return success ? 0 : 1;
    } catch (const std::exception& e) {
        std::cerr << "Fatal error: " << e.what() << std::endl;
        return 1;
    }
}