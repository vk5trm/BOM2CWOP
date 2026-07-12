# BOM2CWOP

Australian Bureau of Meteorology Observations to APRS CWOP Uploader

This Python script fetches real-time weather observations directly from the Australian Bureau of Meteorology (BOM) HTTP API and uploads them to the APRS (Automatic Packet Reporting System) via the CWOP (Citizen Weather Observer Program) network.

## Overview

BOM2CWOP is designed to run as a periodic cron job (recommended every 10–20 minutes). It automatically queries the BOM API for the latest JSON observation data for your selected station and pushes the data to the global CWOP network.

> **Note:** This script works **only** in Australia using official BOM data.

## Requirements

- Python 3.x
- The `requests` library (if not using standard `urllib`)
- Access to the internet
- A valid APRS callsign and password (or use `00000` for generic CWOP password)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/vk5trm/BOM2CWOP.git
   cd BOM2CWOP
   ```

2. **Important:** Ensure you pull the latest commit (`e695573`) to use the new HTTP API logic.
   ```bash
   git pull origin main
   ```

## Configuration

Update the following variables in `BOM2CWOP.py`:

| Variable | Description | Example |
|----------|-------------|---------|
| `APRS_CALL` | Your APRS callsign | `VK1ABC` |
| `APRS_PASSCODE` | Your APRS passcode (use `00000` for generic CWOP) | `00000` |
| `STATION_ID` | The BOM Observation Station ID (e.g., `002043`) | `002043` |
| `STATE_CODE` | Your state code (e.g., `NSW`, `VIC`, `QLD`) | `NSW` |

> **How to find your Station ID:**
> 1. Visit the BOM Weather Data website.
> 2. Search for your local weather station by clicking on you state then click on "Latest Observations"
> 3. Go though the list and find the town/city you are interested in and click on the name.
> 4. go to the bottom of the page and find the link to the .JSON file Note the full numeric ID (LLLNNNNN.NNNNN.JSON) in the URL
     (ie https://www.bom.gov.au/fwo/IDS60910/IDS60910.95687.json) would be STATION_ID="IDS60910.95687": "VK5TRM-13 
> 5. Enter this ID in the `STATION_ID` field.

### Supported States

The script automatically constructs the correct API URL based on your state:
- **NSW** (New South Wales & ACT)
- **VIC** (Victoria)
- **QLD** (Queensland)
- **SA** (South Australia)
- **WA** (Western Australia)
- **TAS** (Tasmania)
- **NT** (Northern Territory)

## Usage

Run the script manually for testing:
```bash
python BOM2CWOP.py
```

### Automate with Cron

To run automatically every 15 minutes, add this to your crontab (`crontab -e`):

```bash
*/15 * * * * /usr/bin/python3 /path/to/BOM2CWOP/BOM2CWOP.py >> /var/log/bom2cwop.log 2>&1
```

## Changes in Latest Version (v1.1)

- **Removed FTP dependency:** No more manual downloading of `.tgz` or `.gz` files.
- **Direct API Access:** Fetches JSON data directly via HTTP.
- **403 Error Fix:** Resolved authentication/access issues with the BOM server.
- **Simplified Config:** Replaced `TAR_PATH` and complex file extraction logic with a simple `STATION_ID`.

## Troubleshooting

- **403 Forbidden Error:** Ensure you have updated to the latest version (`e695573`). The previous version had an API version mismatch.
- **Station Not Found:** Verify your `STATION_ID` is correct. You can find valid IDs on the [BOM Weather Data](http://www.bom.gov.au) site.
- **No Data Uploaded:** Check your `APRS_CALL` and `APRS_PASSCODE`.

## License

This project is open source.

## Credits

Created by Robert Middelmann **VK5TRM** & Mark Jessop **VK5QI**
```
