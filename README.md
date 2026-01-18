# BOM2CWOP
Australian Bureau of Meteorology Observations to APRS CWOP Uploader 
 This is intended to be run as a regular (10 to 20 minute) cron job. 
       This Python script will only work in Austraila using the  
       Australian Bureau of Meteorology data  
       Update the TAR_PATH, APRS_CALL, APRS_PASSCODE (00000 for CWOP) 
       and Station filename in the (STATION_JSON) Fields before using. 
       Put the name of the TGZ file from the list below of the state 
       you want in the TAR_PATH in the Settings for FTP download   
           
       /anon/gen/fwo/IDN60910.tgz	New South Wales and Australian Capital Territory 
       /anon/gen/fwo/IDV60910.tgz	Victoria 
       /anon/gen/fwo/IDQ60910.tgz	Queensland 
       /anon/gen/fwo/IDS60910.tgz	South Australia 
       /anon/gen/fwo/IDW60910.tgz   Western Australia 
       /anon/gen/fwo/IDT60910.tgz	Tasmania 
       /anon/gen/fwo/IDD60910.tgz	Northern Territory 

       Download manualy the state you are interested in and open the gzfile 
       and find the name of file in json format of area you are interested in 
       and put the .json file name in the STATION_JSON= in the Settings.
         
