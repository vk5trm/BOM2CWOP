#!/usr/bin/env python3
#
#  BOM JSON Observation to APRS Uploader
#  Robert Middelmann <vk5trm@gmail.com>
#  Mark Jessop <vk5qi@rfhead.net>
#  2025-10-19
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

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# This is intended to be run as a regular (30 minute) cron job.
# This Python script will only work in Austraila using the Australian Bureau of Meteorology data 
# Update the TAR_PATH, APRS_CALL, APRS_PASSCODE(00000 for CWOP server)  and Station > APRS call mapping(STATION_JSON) Fields below before using.
# Put the name of the TGZ file from the list below of the state you want in the TAR_PATH in the Settings for FTP download  
#    
#       /anon/gen/fwo/IDN60910.tgz	Weather Observations 72hr History - New South Wales and Australian Capital Territory
#       /anon/gen/fwo/IDV60910.tgz	Weather Observations 72hr History - Victoria
#       /anon/gen/fwo/IDQ60910.tgz	Weather Observations 72hr History - Queensland
#       /anon/gen/fwo/IDS60910.tgz	Weather Observations 72hr History - South Australia
#       /anon/gen/fwo/IDW60910.tgz  Weather Observations 72hr History - Western Australia
#       /anon/gen/fwo/IDT60910.tgz	Weather Observations 72hr History - Tasmania
#       /anon/gen/fwo/IDD60910.tgz	Weather Observations 72hr History - Northern Territory
#
# Download manualy the state you are interested in and open the gzfile and find the name of file in json format of area you are interested in and put the .json 
# file name in the STATION_JSON= with mapping to a callsign in the Settings below. You can have as many SSID mapping as you like 
#
#
import json
import sys
import traceback
import ftplib
import tarfile
import io
import time
import os
from socket import *

# SETTINGS
FTP_SERVER = "ftp.bom.gov.au"
TAR_PATH = "/anon/gen/fwo/IDS60910.tgz"

# STATION_JSON mapping: json filename (as in archive or basename) -> APRS wx_call
STATION_JSON = {
    "IDS60910.94682.json": "VK5TRM-13",
    "IDS60910.95687.json": "VK5TRM-15",
}

APRS_CALL = 'VK5TRM-13'    # login user for APRS-IS session (fallback)
APRS_PASSCODE = 00000
APRS_SERVER = 'cwop.aprs.net'
APRS_PORT = 14580


class APRSClient:
    def __init__(self, user, passwd, host=APRS_SERVER, port=APRS_PORT, timeout=10):
        self.user = user
        self.passwd = passwd
        self.host = host
        self.port = port
        self.sock = None
        self.timeout = timeout

    def connect(self):
        if self.sock:
            return
        s = socket(AF_INET, SOCK_STREAM)
        s.settimeout(self.timeout)
        s.connect((self.host, self.port))
        s.send(('user %s pass %s vers BOMWX 0.1\n' % (self.user, self.passwd)).encode())
        self.sock = s

    def send_packet(self, wx_call, data):
        if self.sock is None:
            self.connect()
        self.sock.send(('%s>APRS:%s\n' % (wx_call, data)).encode())

    def close(self):
        if self.sock:
            try:
                self.sock.shutdown(0)
            except Exception:
                pass
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None


def str_or_dots(number, length):
    if number is None:
        return '.' * length
    else:
        format_type = {'int': 'd', 'float': '.0f'}[type(number).__name__]
        return ''.join(('%0', str(length), format_type)) % number


def make_aprs_wx(lat_str, lon_str, comment="BOMWX", wind_dir=None, wind_speed=None, wind_gust=None, temperature=None, rain_since_midnight=None, humidity=None, pressure=None):
    return '!%s/%s_%s/%sg%st%sP%sh%sb%s%s' % (
        lat_str, lon_str,
        str_or_dots(wind_dir, 3),
        str_or_dots(wind_speed, 3),
        str_or_dots(wind_gust, 3),
        str_or_dots(temperature, 3),
        str_or_dots(rain_since_midnight, 3),
        str_or_dots(humidity, 2),
        str_or_dots(pressure, 5),
        comment
    )


cardinal_lookup = {
    'N': 0, 'NNE': 22, 'NE': 45, 'ENE': 67, 'E': 90, 'ESE': 112, 'SE': 135, 'SSE': 157,
    'S': 180, 'SSW': 202, 'SW': 225, 'WSW': 247, 'W': 270, 'WNW': 292, 'NW': 315, 'NNW': 337, 'CALM': 0
}


def bom_json_to_aprs(obs, comment="BOMWX"):
    if obs is None:
        return None
    try:
        lat = float(obs.get("lat", 0.0))
        lat_degree = abs(int(lat))
        lat_minute = abs(lat - int(lat)) * 60.0
        lat_min_str = ("%02.2f" % lat_minute).zfill(5)
        lat_dir = "N" if lat > 0 else "S"
        lat_str = "%02d%s" % (lat_degree, lat_min_str) + lat_dir
    except Exception:
        return None
    try:
        lon = float(obs.get("lon", 0.0))
        lon_degree = abs(int(lon))
        lon_minute = abs(lon - int(lon)) * 60.0
        lon_min_str = ("%02.2f" % lon_minute).zfill(5)
        lon_dir = "W" if lon < 0 else "E"
        lon_str = "%03d%s" % (lon_degree, lon_min_str) + lon_dir
    except Exception:
        return None
    try:
        temp_f = float(obs.get('air_temp')) * (9.0 / 5.0) + 32
    except Exception:
        temp_f = None
    try:
        press_hpa = int(float(obs.get('press')) * 10)
    except Exception:
        press_hpa = None
    try:
        rain_in = float(obs.get('rain_trace')) * 3.93700787
    except Exception:
        rain_in = None
    try:
        humidity = float(obs.get('rel_hum'))
    except Exception:
        humidity = None
    try:
        wind_speed = float(obs.get('wind_spd_kt')) * 1.15077945
    except Exception:
        wind_speed = None
    try:
        wind_gust = float(obs.get('gust_kt')) * 1.15077945
    except Exception:
        wind_gust = None
    wind_dir_value = obs.get('wind_dir')
    if wind_dir_value in cardinal_lookup:
        wind_dir = cardinal_lookup[wind_dir_value]
    else:
        try:
            wind_dir = int(float(wind_dir_value))
        except Exception:
            wind_dir = None

    return make_aprs_wx(
        lat_str, lon_str,
        comment=comment,
        temperature=temp_f,
        pressure=press_hpa,
        rain_since_midnight=rain_in,
        humidity=humidity,
        wind_speed=wind_speed,
        wind_gust=wind_gust,
        wind_dir=wind_dir
    )


def _normalize_station_json_param(station_json):
    # expected to be a dict mapping filename->wx_call
    if station_json is None:
        return [], {}
    if isinstance(station_json, dict):
        wanted = [k for k in station_json.keys() if k and str(k).strip()]
        mapping = {k: v for k, v in station_json.items() if k and str(k).strip()}
        return wanted, mapping
    if isinstance(station_json, str):
        s = station_json.strip()
        if s == '' or s == '*':
            return [], {}
        parts = [p.strip() for p in s.split(',') if p.strip()]
        mapping = {p: APRS_CALL for p in parts}
        return parts, mapping
    return [], {}


def get_bom_jsons(ftp_server, tar_path, wanted_list):
    if not wanted_list:
        print("ERROR: No STATION_JSON filenames provided")
        return []
    try:
        ftp = ftplib.FTP(ftp_server)
        ftp.login()
        tar_bytes = io.BytesIO()
        ftp.retrbinary("RETR %s" % tar_path, tar_bytes.write)
        ftp.quit()
        tar_bytes.seek(0)
        result = []
        with tarfile.open(fileobj=tar_bytes, mode='r:gz') as tar:
            names = tar.getnames()
            # print("DEBUG: requested/wanted list:", wanted_list)
            candidates = [n for n in names if n in wanted_list or os.path.basename(n) in wanted_list]
            # print("DEBUG: matched candidates:", candidates)
            if not candidates:
                print("No matching JSON files found in archive for the requested filenames.")
                return []
            for cand in candidates:
                try:
                    extracted = tar.extractfile(cand)
                    if not extracted:
                        print(f"Could not extract {cand} from archive")
                        continue
                    json_data = extracted.read().decode()
                    parsed_data = json.loads(json_data)
                    observations_list = parsed_data.get('observations', {}).get('data', [])
                    # Debug: show structure keys to help identify where name is
                    try:
                        obs_keys = parsed_data.get('observations', {}).keys()
                    except Exception:
                        obs_keys = None
                    # print(f"DEBUG: {cand} observations keys: {obs_keys}; top-level keys: {list(parsed_data.keys())}")
                    # determine station name robustly by trying multiple likely locations
                    station_name = None
                    header = parsed_data.get('observations', {}).get('header')
                    # header can be dict or list
                    if isinstance(header, dict):
                        station_name = header.get('name') or header.get('station_name') or station_name
                    elif isinstance(header, list):
                        for h in header:
                            if isinstance(h, dict):
                                station_name = h.get('name') or h.get('station_name') or station_name
                                if station_name:
                                    break
                    # try top-level name
                    if not station_name:
                        station_name = parsed_data.get('name')
                    # try first observation entry's name fields
                    if not station_name and observations_list:
                        first_obs = observations_list[0] if isinstance(observations_list, list) and observations_list else None
                        if isinstance(first_obs, dict):
                            station_name = first_obs.get('name') or first_obs.get('station_name') or first_obs.get('station') or station_name
                    # final fallback to filename basename
                    if not station_name:
                        station_name = os.path.basename(cand)
                    if observations_list:
                        result.append((cand, observations_list, station_name))
                    else:
                        print(f"No observations found in {cand}")
                except Exception:
                    print(f"ERROR: Could not parse {cand}: " + traceback.format_exc())
                    continue
        return result
    except Exception:
        print("ERROR: Grabbing data from BOM FTP failed: " + traceback.format_exc())
        return []


def determine_aprs_call_for_file(station_filename, mapping):
    if not mapping:
        return APRS_CALL
    if station_filename in mapping:
        return mapping[station_filename] or APRS_CALL
    base = os.path.basename(station_filename)
    if base in mapping:
        return mapping[base] or APRS_CALL
    return APRS_CALL


if __name__ == '__main__':
    wanted, aprs_mapping = _normalize_station_json_param(STATION_JSON)
    if not wanted:
        print("ERROR: STATION_JSON must be mapping or comma-separated filenames. Exiting.")
        sys.exit(1)

    station_obs_list = get_bom_jsons(FTP_SERVER, TAR_PATH, wanted)
    if not station_obs_list:
        print("No observations to process. Exiting.")
        sys.exit(1)

    aprs_client = APRSClient(APRS_CALL, APRS_PASSCODE, host=APRS_SERVER, port=APRS_PORT)
    try:
        aprs_client.connect()
    except Exception:
        print("ERROR: Could not connect/login to APRS-IS: " + traceback.format_exc())
        aprs_client.close()
        sys.exit(1)

    try:
        sent_count = 0
        for station_filename, observations, station_name in station_obs_list:
            try:
                obs = observations[0]
                # Use the station "name" field from the JSON (station_name), fallback to filename if not present.
                comment = station_name or ("BOMWX %s" % station_filename)
                aprs_str = bom_json_to_aprs(obs, comment=comment)
                if not aprs_str:
                    print("Skipping invalid observation for %s" % station_filename)
                    continue
                wx_call = determine_aprs_call_for_file(station_filename, aprs_mapping)
                print("Using APRS call '%s' for station file %s" % (wx_call, station_filename))
                print("CWOP String: %s" % aprs_str)
                aprs_client.send_packet(wx_call, aprs_str)
                sent_count += 1
                print("Sent packet #%d for %s" % (sent_count, station_filename))
                time.sleep(0.5)
            except Exception:
                print("ERROR processing observation for %s: " % (station_filename) + traceback.format_exc())
    finally:
        aprs_client.close()
    print("Finished. Total packets sent:", sent_count)
    sys.exit(0)
