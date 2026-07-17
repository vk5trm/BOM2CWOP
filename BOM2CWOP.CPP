#include <iostream>
#include <string>
#include <sstream>
#include <iomanip>
#include <map>
#include <vector>
#include <fstream>
#include <algorithm>
#include <curl/curl.h>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

// --- Global Config Variables ---
std::string APRS_CALL;
int APRS_PASSCODE;
std::string APRS_SERVER;
int APRS_PORT;
std::string BOM_BASE_URL;
std::map<std::string, std::string> STATION_CONFIG;

// --- Simple INI Parser ---
bool load_config(const std::string& filename) {
    std::ifstream file(filename);
    if (!file.is_open()) {
        std::cerr << "Error: Could not open " << filename << ". Using defaults or exiting." << std::endl;
        return false;
    }

    std::string line, current_section;
    while (std::getline(file, line)) {
        // Trim whitespace
        line.erase(0, line.find_first_not_of(" \t\r\n"));
        line.erase(line.find_last_not_of(" \t\r\n") + 1);

        if (line.empty() || line[0] == ';' || line[0] == '#') continue;

        // Section header [section]
        if (line[0] == '[' && line.back() == ']') {
            current_section = line.substr(1, line.size() - 2);
            continue;
        }

        // Key=Value
        size_t pos = line.find('=');
        if (pos != std::string::npos) {
            std::string key = line.substr(0, pos);
            std::string value = line.substr(pos + 1);
            
            // Trim key and value
            key.erase(0, key.find_first_not_of(" \t"));
            key.erase(key.find_last_not_of(" \t") + 1);
            value.erase(0, value.find_first_not_of(" \t"));
            value.erase(value.find_last_not_of(" \t") + 1);

            if (current_section == "aprs") {
                if (key == "call") APRS_CALL = value;
                else if (key == "passcode") APRS_PASSCODE = std::stoi(value);
                else if (key == "server") APRS_SERVER = value;
                else if (key == "port") APRS_PORT = std::stoi(value);
            } else if (current_section == "stations") {
                STATION_CONFIG[key] = value;
            } else if (current_section == "api") {
                if (key == "base_url") BOM_BASE_URL = value;
            }
        }
    }
    return true;
}

// --- Helper Functions (Same as before) ---
std::string str_or_dots(const json& val, int length, bool is_float = false) {
    if (val.is_null()) return std::string(length, '.');
    try {
        int intVal = is_float ? static_cast<int>(val.get<double>()) : val.get<int>();
        std::ostringstream oss;
        oss << std::setw(length) << std::setfill('0') << intVal;
        return oss.str();
    } catch (...) {
        return std::string(length, '.');
    }
}

std::string make_aprs_wx(const std::string& lat_str, const std::string& lon_str, 
                         const std::string& comment, int wind_dir, int wind_speed, 
                         int wind_gust, int temperature, int rain_in, int humidity, int pressure) {
    std::ostringstream oss;
    oss << "!" << lat_str << "/" << lon_str << "_"
        << std::setw(3) << std::setfill('0') << (wind_dir == -1 ? 0 : wind_dir) << "/"
        << std::setw(3) << std::setfill('0') << (wind_speed == -1 ? 0 : wind_speed) << "g"
        << std::setw(3) << std::setfill('0') << (wind_gust == -1 ? 0 : wind_gust) << "t"
        << std::setw(3) << std::setfill('0') << (temperature == -1 ? 0 : temperature) << "P"
        << std::setw(3) << std::setfill('0') << (rain_in == -1 ? 0 : rain_in) << "h"
        << std::setw(2) << std::setfill('0') << (humidity == -1 ? 0 : humidity) << "b"
        << std::setw(5) << std::setfill('0') << (pressure == -1 ? 0 : pressure)
        << comment;
    return oss.str();
}

// --- APRS Client Class ---
class APRSClient {
    // ... (Implementation identical to previous version, using global APRS_SERVER/APRS_PORT)
    // Note: In a real app, pass these to constructor or use globals.
    // For this snippet, we assume globals are set before instantiation.
private:
    std::string user;
    int passwd;
    std::string host;
    int port;
    int socket_fd;

public:
    APRSClient(const std::string& u, int p, const std::string& h, int pt) 
        : user(u), passwd(p), host(h), port(pt), socket_fd(-1) {}

    bool connect() {
        if (socket_fd != -1) return true;
        struct addrinfo hints, *res;
        memset(&hints, 0, sizeof hints);
        hints.ai_family = AF_INET;
        hints.ai_socktype = SOCK_STREAM;
        std::string port_str = std::to_string(port);
        if (getaddrinfo(host.c_str(), port_str.c_str(), &hints, &res) != 0) return false;
        socket_fd = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
        if (socket_fd == -1) { freeaddrinfo(res); return false; }
        if (connect(socket_fd, res->ai_addr, res->ai_addrlen) == -1) {
            close(socket_fd); socket_fd = -1; freeaddrinfo(res); return false;
        }
        freeaddrinfo(res);
        std::string login_msg = "user " + user + " pass " + std::to_string(passwd) + " vers BOMWX_HTTP 0.1\n";
        send(socket_fd, login_msg.c_str(), login_msg.length(), 0);
        return true;
    }

    bool send_packet(const std::string& wx_call, const std::string& data) {
        if (socket_fd == -1) if (!connect()) return false;
        std::string packet = wx_call + ">APRS:" + data + "\n";
        send(socket_fd, packet.c_str(), packet.length(), 0);
        return true;
    }

    void close() { if (socket_fd != -1) { ::close(socket_fd); socket_fd = -1; } }
    ~APRSClient() { close(); }
};

// --- Fetching & Conversion (Simplified for brevity, same logic as before) ---
// ... (fetch_bom_data, bom_json_to_aprs, main logic) ...
// Note: The main function now calls load_config("config.ini") first.

int main() {
    // 1. Load Configuration
    if (!load_config("config.ini")) {
        std::cerr << "Configuration loading failed. Exiting." << std::endl;
        return 1;
    }

    if (STATION_CONFIG.empty()) {
        std::cerr << "Error: No stations configured in config.ini." << std::endl;
        return 1;
    }

    std::cout << "Starting BOM to APRS Uploader. Loaded " << STATION_CONFIG.size() << " stations." << std::endl;

    // 2. Connect APRS
    APRSClient aprs_client(APRS_CALL, APRS_PASSCODE, APRS_SERVER, APRS_PORT);
    if (!aprs_client.connect()) {
        std::cerr << "Failed to connect to APRS-IS." << std::endl;
        return 1;
    }

    // 3. Main Loop (Simplified for single run, add loop for persistent)
    int sent_count = 0;
    for (const auto& [full_id, wx_call] : STATION_CONFIG) {
        // ... (Parsing logic from previous version) ...
        // fetch_bom_data, convert, send_packet
        // ...
    }

    aprs_client.close();
    return 0;
}
