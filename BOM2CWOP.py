#!/usr/bin/env python3

#
#  BOM JSON Observation to APRS Uploader
#  Robert Middelmann <vk5trm@gmail.com>
#  Mark Jessop <vk5qi@rfhead.net>
#  2025-10-19
#  Rob VK5TRM 2026-07-12 -Fixed HTTP API Version - Fixed for 403)
#  Modified to include Browser-like headers to bypass BOM WAF
#

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

import json
import sys
import time
from socket import *
import requests

# --- USER CONFIGURATION ---
#
# 1. Station Configuration: Station ID -> APRS Call
# Ensure these station IDs match the region of your selected state.
STATION_CONFIG = {
    "IDS60910.94682": "VK5TRM-12",  # Example: A SA station
    "IDS60910.95687": "VK5TRM-15",  # Example: Another SA station
}

# 2. APRS Configuration
APRS_CALL = 'VK5TRM-13'    
APRS_PASSCODE = 00000      # ⚠️ WARNING: Replace with your real passcode
APRS_SERVER = 'cwop.aprs.net'
APRS_PORT = 14580
#
#
#
# --- SYSTEM CONFIGURATION ---

BOM_BASE_URL = "http://www.bom.gov.au/fwo/{product_code}/{product_code}.{station_id}.json"

HTTP_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'http://www.bom.gov.au/',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

# --- Helper Classes & Functions ---

class APRSClient:
    def __init__(self, user, passwd, host=APRS_SERVER, port=APRS_PORT, timeout=10):
        self.user = user
        self.passwd = passwd
        self.host = host
        self.port = port
        self.sock = None
        self.timeout = timeout

    def connect(self):
        if self.sock: return
        s = socket(AF_INET, SOCK_STREAM)
        s.settimeout(self.timeout)
        try:
            s.connect((self.host, self.port))
            # Login using the global APRS_CALL
            login_msg = f'user {self.user} pass {self.passwd} vers BOMWX_HTTP 0.1\n'
            s.send(login_msg.encode())
            self.sock = s
        except Exception as e:
            print(f"Failed to connect to APRS-IS: {e}")
            raise

    def send_packet(self, wx_call, data):
        if self.sock is None: self.connect()
        packet = f'{wx_call}>APRS:{data}\n'
        self.sock.send(packet.encode())

    def close(self):
        if self.sock:
            try: self.sock.shutdown(0)
            except: pass
            try: self.sock.close()
            except: pass
            self.sock = None

def str_or_dots(number, length):
    if number is None: return '.' * length
    try:
        if isinstance(number, float): return f'%0{length}.0f' % round(number)
        else: return f'%0{length}d' % int(number)
    except: return '.' * length
def make_aprs_wx(lat_str, lon_str, comment="BOMWX", wind_dir=None, wind_speed=None, wind_gust=None, 
                 temperature=None, rain_since_midnight=None, humidity=None, pressure=None):
    # Format: !Lat/Long_Dir/SpeedgGusttTempPrainHumPressComment
    # Note: The 'g' is for gust, 't' is for temp.
    # We need to ensure we have exactly 10 arguments for the 10 %s placeholders.
    return '!%s/%s_%s/%sg%st%sP%sh%sb%s%s' % (
        lat_str, 
        lon_str,
        str_or_dots(wind_dir, 3),
        str_or_dots(wind_speed, 3),
        str_or_dots(wind_gust, 3),   # Gust goes here
        str_or_dots(temperature, 3), # Temp goes here
        str_or_dots(rain_since_midnight, 3),
        str_or_dots(humidity, 2),
        str_or_dots(pressure, 5),
        comment
    )
#
#
cardinal_lookup = {
    'N': 0, 'NNE': 22, 'NE': 45, 'ENE': 67, 'E': 90, 'ESE': 112, 'SE': 135, 'SSE': 157,
    'S': 180, 'SSW': 202, 'SW': 225, 'WSW': 247, 'W': 270, 'WNW': 292, 'NW': 315, 'NNW': 337, 'CALM': 0
}

def bom_json_to_aprs(obs, comment="BOMWX"):
    if obs is None: return None
    
    # Coordinates
    try:
        lat = float(obs.get("lat", 0.0))
        lat_degree = abs(int(lat))
        lat_minute = abs(lat - int(lat)) * 60.0
        lat_min_str = ("%02.2f" % lat_minute).zfill(5)
        lat_dir = "N" if lat > 0 else "S"
        lat_str = "%02d%s" % (lat_degree, lat_min_str) + lat_dir
    except: return None

    try:
        lon = float(obs.get("lon", 0.0))
        lon_degree = abs(int(lon))
        lon_minute = abs(lon - int(lon)) * 60.0
        lon_min_str = ("%02.2f" % lon_minute).zfill(5)
        lon_dir = "W" if lon < 0 else "E"
        lon_str = "%03d%s" % (lon_degree, lon_min_str) + lon_dir
    except: return None

    # Weather Data
    try: temp_f = float(obs.get('air_temp')) * (9.0 / 5.0) + 32
    except: temp_f = None
    try: press_hpa = int(float(obs.get('press')) * 10)
    except: press_hpa = None
    try: 
        rain_mm = float(obs.get('rain_trace'))
        rain_in = rain_mm * 0.0393700787
    except: rain_in = None
    try: humidity = float(obs.get('rel_hum'))
    except: humidity = None
    
    try:
        spd_val = obs.get('wind_spd_kt') or (obs.get('wind_spd_kmh') / 1.852) or (obs.get('wind_spd_ms') * 1.94384)
        wind_speed = float(spd_val)
    except: wind_speed = None
    
    try:
        gust_val = obs.get('gust_kt') or (obs.get('gust_kmh') / 1.852) or (obs.get('gust_ms') * 1.94384)
        wind_gust = float(gust_val)
    except: wind_gust = None

    wind_dir_value = obs.get('wind_dir')
    if wind_dir_value in cardinal_lookup:
        wind_dir = cardinal_lookup[wind_dir_value]
    else:
        try: wind_dir = int(float(wind_dir_value))
        except: wind_dir = None

    return make_aprs_wx(lat_str, lon_str, comment=comment, temperature=temp_f, pressure=press_hpa, 
                        rain_since_midnight=rain_in, humidity=humidity, wind_speed=wind_speed, 
                        wind_gust=wind_gust, wind_dir=wind_dir)

def fetch_bom_data(station_id, product_code):
    url = BOM_BASE_URL.format(product_code=product_code, station_id=station_id)
    try:
        session = requests.Session()
        session.headers.update(HTTP_HEADERS)
        response = session.get(url, timeout=10)
        if response.status_code != 200: return None, None
        data = response.json()
        
        observations_list = []
        if 'observations' in data:
            if isinstance(data['observations'], dict) and 'data' in data['observations']:
                observations_list = data['observations']['data']
            elif isinstance(data['observations'], list):
                observations_list = data['observations']
        if not observations_list and 'data' in data:
            if isinstance(data['data'], list): observations_list = data['data']
        
        if not observations_list: return None, None
        
        latest_obs = observations_list[0]
        station_name = latest_obs.get('name') or latest_obs.get('station_name') or f"Station {station_id}"
        return latest_obs, station_name
    except: return None, None

# --- Main Execution ---

if __name__ == '__main__':
    if not STATION_CONFIG:
        print("Error: No stations configured.")
        sys.exit(1)

    print(f"Starting BOM to APRS Uploader. Monitoring {len(STATION_CONFIG)} stations across multiple states.")

    # Connect once to APRS-IS
    aprs_client = APRSClient(APRS_CALL, APRS_PASSCODE, host=APRS_SERVER, port=APRS_PORT)
    try: aprs_client.connect()
    except: sys.exit(1)

    try:
        sent_count = 0
        for full_id, wx_call in STATION_CONFIG.items():
            # Parse the key: "ProductCode.StationID"
            if '.' not in full_id:
                print(f"Error: Station key '{full_id}' is invalid. Must be 'ProductCode.StationID'.")
                continue
            
            parts = full_id.split('.')
            # The first part is the Product Code for THIS specific station
            station_product_code = parts[0]
            # The last part is the Station ID
            station_id = parts[-1]
            
            print(f"Fetching data for Station ID: {station_id} (State Code: {station_product_code}) -> Sending to: {wx_call}")

            obs, station_name = fetch_bom_data(station_id, station_product_code)
            
            if obs is None: 
                print(f"  -> Failed to fetch data for {station_name} ({station_id})")
                continue
            
            comment = ("%s WX" % station_name) or ("BOMWX %s" % station_id)
            aprs_str = bom_json_to_aprs(obs, comment=comment)
            
            if not aprs_str: 
                print(f"  -> Failed to format APRS packet for {station_name}")
                continue
            
            print(f"  -> Sent packet for {station_name} ({station_id}) via {wx_call}")
            
            try:
                aprs_client.send_packet(wx_call, aprs_str)
                sent_count += 1
                time.sleep(0.5) # Be polite to the server
            except Exception as e:
                print(f"  -> Error sending packet: {e}")

    finally:
        aprs_client.close()

    if sent_count > 0:
        print(f"Finished. Total packets sent: {sent_count}")
    else:
        print("No packets sent.")
    
    sys.exit(0)
