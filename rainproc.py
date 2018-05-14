import pandas as pd
import pycountry
import numpy as np
import statsmodels.formula.api as smf

notmissingthres = dict(Y=365*.9, M=30*.9, W=7*.9, Q=365/4*.9)
hdf_store = './data/ECA_ALL.hdf'
#COMPRESS = 'blosc:snappy'
#COMPRESS = 'bzip2'
#COMPRESS = 'blosc:lz4hc'
COMPRESS = 'blosc:zlib'
#COMPRESS = 'bzip2'
COMPLEVEVL = 9
COMP=dict(complib=COMPRESS, complevel=COMPLEVEVL, format='table',  )




def read_rain(hdfstore, name, file):
    tomm= lambda x: np.NaN if float(x) < 0 else 0.1*float(x) # negative values = missing data
    df = pd.read_csv(file, names=["Date", "Rainfall_mm"], index_col="Date", usecols=[2,3], header=15, parse_dates=['Date'], converters={3:tomm})
    df.replace(-9999, np.nan, inplace=True)
    hdfstore.put(name,df, **COMP)

def rainfall2hdf():
    stns = pd.read_hdf(hdf_store, 'stations', columns=['STAID'])
    with  pd.io.pytables.HDFStore(hdf_store,"a") as hdfstore:
        #ct=0
        for index, s in stns.iterrows():
            stnid=s['STAID']
            read_rain(hdfstore, 'stations/{}'.format(stnid), './data/eca_blend_rr/{}.txt'.format(stnid))
            #ct+=1
            #if (ct>10): break;
def resampled(staid,freq):
    data=pd.read_hdf(hdf_store,'stations/{}'.format(staid))
    ds=data.resample(freq).apply(lambda x: 
                                 x.sum(skipna=True) if x.notnull().sum() > notmissingthres[freq] 
                                 else np.NaN)
    return ds    

def linear_fit(data, xcol='ndates', ycol='Rainfall_mm'):
    data['ndates'] = (data.index-pd.to_datetime('1800-01-01')).astype('timedelta64[D]')
    ft=smf.ols( '{} ~ {}'.format(ycol,xcol), data=data, missing='drop' ).fit()
    return ft.params.ndates*data.ndates+ft.params.Intercept, ft.pvalues.ndates

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
    
    with  pd.io.pytables.HDFStore(hdf_store,"w") as hdfstore:
        hdfstore.put('stations',stationsdf, **COMP)
        
def stations():
    data=pd.read_hdf(hdf_store,'stations')
    return data

def pre_process():
    format_stations()
    rainfall2hdf()    
    
if __name__ == "__main__":
    # pre_process() # takes several minutes (10min?) 
    freq="Y"
    staid = 'RR_STAID011094'
    ds = resampled(staid, freq)
    lf=linear_fit(ds)
    print(ds)