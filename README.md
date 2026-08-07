# BOM to APRS Web Server

**Fetches real-time weather data from the Australian Bureau of Meteorology (BOM) and automatically uploads it to the APRS-IS network.**

This Flask-based server acts as a bridge between official Australian weather data and the APRS (Automatic Packet Reporting System) community. It runs as a background service, collecting data at regular intervals and broadcasting it as standard weather packets.

## 🚀 Features

*   **Automatic Scheduling**: Fetches data every **15 minutes** (configurable) via crontab -e.
*   **Multi-Station Support**: Configurable to monitor multiple BOM stations simultaneously.
*   **METAR Generator**: Exposes a web endpoint (`/weather`) that generates standard METAR format reports for human-readable viewing or integration.
*   **APRS Integration**: Directly connects to the APRS-IS network to upload formatted weather packets.
*   **Fog & Rain Logic**: Implements custom algorithms to detect fog conditions (based on dew point spread and humidity and wind under 3 knots) and significant rainfall to enhance packet accuracy.
*   **Web Interface**: Includes a simple dashboard to view active stations and trigger manual uploads.

## 📋 Prerequisites

*   **Python 3.6+**
*   Required Python packages:
    *   `flask`
    *   `requests`

## ⚙️ Configuration

Before running the server, you must configure the following settings in the script:

### 1. APRS Credentials
Locate the **Global APRS Config** section near the top of the file.
```python
APRS_CALL = 'VK5TRM-5'          # Your callsign
APRS_PASSCODE = '00000'         # ⚠️ REPLACE with your real APRS passcode
APRS_SERVER = 'aunz.aprs2.net'  # APRS-IS server (check documentation for your region)
APRS_PORT = 14580               # APRS-IS port
```

### 2. Station Configuration
Define which BOM stations you want to monitor in the `STATION_CONFIG` dictionary.

*Format:* "ProductCode.StationID": { "aprs_call": "CALLSIGN", "name": "Friendly Name" }

The 'aprs_call' here is for display/menu reference, but the UPLOAD uses the global APRS_CALL

**Use these product codes for each state in Australia**
```Bash
  IDN60910      New South Wales and Australian Capital Territory
  IDV60910      Victoria
  IDQ60910      Queensland
  IDS60910      South Australia
  IDW60910      Western Australia
  IDT60910      Tasmania
  IDD60910      Northern Territory
```
How to find your Station ID:
1. Visit the BOM Weather Data website.
2. Search for your local weather station by clicking on your state then click on "Latest Observations"
3. Go though the list and find the town/city you are interested in and click on the name.
4. look at the URL of the page and  Note the last numeric ID between the 2 dots (.NNNNN.shtml) in the URL
    (ie https://www.bom.gov.au/fwo/IDS60910/IDS60910.95687.shtml) would be StationID=95687
5. Enter this ID for the StationID

```python
STATION_CONFIG = {
    "IDS60910.94682": {
        "aprs_call": "YLOX",     # The callsign displayed on APRS for this station
        "name": "YLOX"           # Friendly name for the web interface
    },
    "IDS60910.95687": {
        "aprs_call": "YREN",
        "name": "YREN"
    }
}
```

## 🛠️ Installation & Run

1.  **Install Dependencies**:
    ```bash
    pip install flask requests
    ```

2.  **Test run the Server**:
    ```bash
    python BOM2CWOP_Server.py
    ```

3.  **Verify**:
    *   The console will output: `Web server starting on port 5000...`
    *   Open your browser to `http://localhost:5000` to see the dashboard
    *   
4a.  **Copy Main BOM2CWOP_server file to correct location**:

  ```bash
  sudo cp BOM2CWOP_server /usr/local/bin
  ```

4b. **Copy BOM2CWOP_server system.service file to correct location**:

  ```bash
  sudo cp BOM2CWOP_server.service /usr/lib/systemd/system/    
  ```

5a.  **Enable service**:
  ```bash
  sudo systemctl enable BOM2CWOP_server.service
  ```
5b.  **Start service**: 
  ```bash
  sudo systemctl start BOM2CWOP_server.service
  ```
6.   **Create Crontab entry using `crobtab -e`.
 ```bash
 */15 * * * * curl http://127.0.0.1:5000/aprs >/dev/null
 ``` 
      
## 🌐 Web Endpoints

Once running, the server exposes the following endpoints:

| Endpoint | Description |
| :--- | :--- |
| `/` | **Home Page**: Dashboard showing active stations, links to raw BOM data, and status. |
| `/weather` | **METAR Output**: Returns formatted METAR text for all configured stations. |
| `/weather?station={name}` | **Filtered METAR**: Returns METAR for a specific station by name. |
| `/aprs` | **Manual Trigger**: Forces an immediate data fetch and upload to APRS. Returns JSON status. |

## 🧠 How It Works

1.  **Data Fetching**: The server queries the BOM JSON API (`www.bom.gov.au`) for the latest observations.
2.  **Rain**: The rain is taken over the last hour for APRS and for the last 10 minutes for metar data rain detection.
3.  **Fog Detection**: If cloud data is missing, the script infers fog conditions by checking:
    *   Dew point spread ≤ 2°C **AND** Relative Humidity > 96%
    *   Wind speed ≤ 3 knots
4.  **APRS Formatting**: Data is converted into APRS weather packet format (`!LAT/LON_...`) and sent via TCP to the APRS-IS server.

## ⚠️ Security Note

*   **Passcode**: Never commit your `APRS_PASSCODE` to a public repository. The script includes a placeholder (`00000`) and a warning comment to ensure you replace it.
*   **Network**: The server listens on `0.0.0.0:5000`. If exposing this to a public network, ensure you have appropriate firewall rules or authentication in place.

## 📄 License

Created by **Robert Middelmann (vk5trm)** & **Mark Jessop (vk5qi)**.
Version: 1.5-Final

---


