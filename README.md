# BOM2CWOP
Australian Bureau of Meteorology Observations to APRS CWOP Uploader/n
 This is intended to be run as a regular (10 to 20 minute) cron job./n
       This Python script will only work in Austraila using the /n
       Australian Bureau of Meteorology data/n 
       Update the TAR_PATH, APRS_CALL, APRS_PASSCODE (00000 for CWOP)/n
       and Station > APRS call mapping(STATION_JSON) Fields before using./n
       Put the name of the TGZ file from the list below of the state/n
       you want in the TAR_PATH in the Settings for FTP download/n  
           
       /anon/gen/fwo/IDN60910.tgz	New South Wales and Australian Capital Territory/n
       /anon/gen/fwo/IDV60910.tgz	Victoria/n
       /anon/gen/fwo/IDQ60910.tgz	Queensland/n
       /anon/gen/fwo/IDS60910.tgz	South Australia/n
       /anon/gen/fwo/IDW60910.tgz   Western Australia/n
       /anon/gen/fwo/IDT60910.tgz	Tasmania/n
       /anon/gen/fwo/IDD60910.tgz	Northern Territory/n

       Download manualy the state you are interested in and open the gzfile/n
       and find the name of file in json format of area you are interested in/n
       and put the .json file name in the STATION_JSON= with mapping to a callsign/n
       in the Settings below. You can have as many SSID mapping as you like/n 
