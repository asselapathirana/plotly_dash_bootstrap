import pandas as pd
import pycountry
import numpy as np

missingthres = dict(Y=365*.1, M=30*.1, W=7*.1, Q=365/4*.1)
hdf_store = './data/ECA_ALL.hdf'


def read_rain(hdfstore, name, file):
    tomm= lambda x: np.NaN if float(x) < 0 else 0.1*float(x) # negative values = missing data
    df = pd.read_csv(file, names=["Date", "Rainfall_mm"], index_col="Date", usecols=[2,3], header=15, parse_dates=['Date'], converters={3:tomm})
    df.replace(-9999, np.nan, inplace=True)
    hdfstore.put(name,df, format='table', data_columns=True)

def rainfall2hdf():
    stns = pd.read_hdf(hdf_store, 'stations', columns=['STAID'])
    with  pd.HDFStore(hdf_store,"a") as hdfstore:
        for index, s in stns.iterrows():
            stnid=s['STAID']
            read_rain(hdfstore, 'stations/{}'.format(stnid), './data/eca_blend_rr/{}.txt'.format(stnid))

def resampled(staid,freq):
    data=pd.read_hdf('./data/ECA_ALL.hdf','stations/{}'.format(staid))
    ds=data.resample(freq).apply(lambda x: 
                                 x.sum(skipna=True) if x.isnull().sum() < missingthres[freq] 
                                 else x.sum(skipna=False))
    return ds    
    
    
def format_stations(stfile="./data/eca_blend_rr/stations.txt"):
    def dms2dd(v):
        v=[float(x) for x in v.split(':')]
        return v[0]+v[1]/60.+v[2]/3600.
    country2to3 = lambda x: pycountry.countries.get(alpha_2=x).alpha_3
    strp=lambda x: x.strip()
    stationsdf = pd.read_csv(stfile, header=13, converters={1:strp, 2:country2to3, 3:dms2dd, 4:dms2dd})
    stationsdf.rename(inplace=True, columns=lambda x: x.strip())
    stationsdf['STAID']=stationsdf['STAID'].apply('RR_STAID{0:06d}'.format, 8)
    stationsdf['TXT']=stationsdf['STANAME']+" ("+stationsdf['CN']+")"
    
    with  pd.HDFStore(hdf_store,"w") as hdfstore:
        hdfstore.put('stations',stationsdf, format='table', data_columns=True)
        
def stations():
    data=pd.read_hdf('./data/ECA_ALL.hdf','stations')
    return data

def pre_process():
    format_stations()
    rainfall2hdf()    
    
if __name__ == "__main__":
    #pre_process() # takes several minutes (10min?) 
    freq="Y"
    staid = 'RR_STAID000001'
    ds = resampled(staid, freq)
    print(ds)