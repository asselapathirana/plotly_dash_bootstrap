import pandas as pd
import pycountry


def format_stations(stfile="./data/eca_blend_rr/stations.txt"):
    def dms2dd(v):
        v=[float(x) for x in v.split(':')]
        return v[0]+v[1]/60.+v[2]/3600.
    country2to3 = lambda x: pycountry.countries.get(alpha_2=x).alpha_3
    strp=lambda x: x.strip()
    stationsdf = pd.read_csv(stfile, header=13, converters={1:strp, 2:country2to3, 3:dms2dd, 4:dms2dd})
    stationsdf.rename(inplace=True, columns=lambda x: x.strip())
    stationsdf['TXT']=stationsdf['STANAME']+" ("+stationsdf['CN']+")"
    
    print(stationsdf.head())
    stationsdf.to_csv("./data/stations.dat")

if __name__ == "__main__":
    format_stations()

