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

ECA_ALL.hdf
eca_blend_rr directory with RR_STAID000010.txt like files
__init__.py
SECRET.py with mapbox_access_token="xxxxx"

How to get updated data

https://www.ecad.eu/dailydata/predefinedseries.php 

 download ECA_blend_rr.zip

 