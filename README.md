# BOM2CWOP
Australian Bureau of Meteorology Observations to APRS CWOP Uploader
 This is intended to be run as a regular (30 minute) cron job.
    This Python script will only work in Austraila using the Australian Bureau of Meteorology data 
    Update the TAR_PATH,STATION_JSON, APRS_CALL, APRS_PASSCODE and Station > APRS call mapping(STATION_JSON) Fields below before using.
      Put the name of the TGZ file from the list below of the state you want in the TAR_PATH in the Settings for FTP download  
    
       /anon/gen/fwo/IDN60910.tgz	Weather Observations 72hr History - New South Wales and Australian Capital Territory
       /anon/gen/fwo/IDV60910.tgz	Weather Observations 72hr History - Victoria
       /anon/gen/fwo/IDQ60910.tgz	Weather Observations 72hr History - Queensland
       /anon/gen/fwo/IDS60910.tgz	Weather Observations 72hr History - South Australia
       /anon/gen/fwo/IDW60910.tgz  Weather Observations 72hr History - Western Australia
       /anon/gen/fwo/IDT60910.tgz	Weather Observations 72hr History - Tasmania
       /anon/gen/fwo/IDD60910.tgz	Weather Observations 72hr History - Northern Territory

       Download manualy the state you are interested in and open the gzfile and find the area you are interested in and put the .json file name
       in the STATION_JSON in the Settings for FTP download below 

 Send latest observation from specified BOM JSON files (STATION_JSON mapping)
 Reuse one APRS-IS connection for all packets and print debug info about archive contents.
