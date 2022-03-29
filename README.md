# plotly_dash_bootstrap
 
Needs mapbox api key set the key on dokku as
 dokku config:set <appname> MAPBOXAPIKEY=<key>
 
 
This app uses dokku:storage 

https://github.com/dokku/dokku/blob/master/docs/advanced-usage/persistent-storage.md
# dokku storage:report er
       Storage build mounts:
       Storage deploy mounts:         -v /opt/dokku/er/data:/app/data -v /opt/dokku/er/data:/data
       Storage run mounts:            -v /opt/dokku/er/data:/app/data -v /opt/dokku/er/data:/data


'data' directory mounted as persistent-storage should have the following 
SECRET.py with mapbox_access_token="xxxxx"
feather directory with STNRR_STAID00* files and stations.feather file. 
(Those are created by )

Download  updated data
https://www.ecad.eu/dailydata/predefinedseries.php 
 download ECA_blend_rr.zip
 unzip it to ./data/eca_blend_rr/RR_STAID0*.txt  like files
 then run rainproc.py on them. 

 
