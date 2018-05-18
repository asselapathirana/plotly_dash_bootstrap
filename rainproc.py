import pandas as pd
import pycountry
import numpy as np
import statsmodels.formula.api as smf
import datetime

notmissingthres = {"Y":365*.9, "M":30*.9, "W":7*.9, "Q":365/4*.9, "24H":.9}
hdf_store = './data/ECA_ALL.hdf'
#COMPRESS = 'blosc:snappy'
#COMPRESS = 'bzip2'
#COMPRESS = 'blosc:lz4hc'
COMPRESS = 'blosc:zlib'
#COMPRESS = 'bzip2'
COMPLEVEVL = 9
COMP=dict(complib=COMPRESS, complevel=COMPLEVEVL, format='table',  )
TOTAL=1
MAX = 2

def auto_tick(data_range, max_tick=10, tf_inside=False):
    """
    tool function that automatically calculate optimal ticks based on range and the max number of ticks
    :param data_range:   range of data, e.g. [-0.1, 0.5]
    :param max_tick:     max number of ticks, an interger, default to 10
    :param tf_inside:    True/False if only allow ticks to be inside
    :return:             list of ticks
    """
    data_span = data_range[1] - data_range[0]
    scale = 10.0**np.floor(np.log10(data_span))    # scale of data as the order of 10, e.g. 1, 10, 100, 0.1, 0.01, ...
    list_tick_size_nmlz = [5.0, 2.0, 1.0, 0.5, 0.2, 0.1, 0.05, 0.02, 0.01]   # possible tick sizes for normalized data in range [1, 10]
    tick_size_nmlz = 1.0     # initial tick size for normalized data
    for i in range(len(list_tick_size_nmlz)):                 # every loop reduces tick size thus increases tick number
        num_tick = data_span/scale/list_tick_size_nmlz[i]     # number of ticks for the current tick size
        if num_tick > max_tick:                               # if too many ticks, break loop
            tick_size_nmlz = list_tick_size_nmlz[i-1]
            break
    tick_size = tick_size_nmlz * scale             # tick sizse for the original data
    ticks = np.unique(np.arange(data_range[0]/tick_size, data_range[1]/tick_size).round())*tick_size    # list of ticks

    if tf_inside:     # if only allow ticks within the given range
        ticks = ticks[ (ticks>=data_range[0]) * (ticks<=data_range[1])]

    return ticks



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
def resampled(staid,freq, summ):
    data=pd.read_hdf(hdf_store,'stations/{}'.format(staid))
    if summ==TOTAL:
        return data.resample(freq).apply(lambda x: 
                                 x.sum(skipna=True) if x.notnull().sum() > notmissingthres[freq] 
                                 else np.NaN)
    if summ==MAX:
        return data.resample(freq).apply(lambda x: 
                                         x.max(skipna=True) if x.notnull().sum() > notmissingthres[freq] 
                                     else np.NaN)        
    return None # error   

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
        
def stats(dfs):
    res=[]
    for ds in dfs:
        res.append(dict(
        missing='{:.2%}'.format(ds['Rainfall_mm'].isnull().sum()/ds['Rainfall_mm'].shape[0]),
        mean="{:8.2f}".format(ds['Rainfall_mm'].mean()),
        std="{:8.2f}".format(ds['Rainfall_mm'].std()),
        years="{:10d}".format(ds['Rainfall_mm'].shape[0]),
        maxv="{:8.1f}".format(ds['Rainfall_mm'].max()),
        minv="{:8.1f}".format(ds['Rainfall_mm'].min()),
        ))
    resd={}
    for k in res[0]:
        resd[k] = tuple(d[k] for d in res)    
    return resd
 
def get_timelimits(dfs):
    maxt=[]
    mint=[]
    for ds in dfs:
        maxt.append(ds.index.max().to_pydatetime().year)
        mint.append(ds.index.min().to_pydatetime().year)
    return (min(mint),max(maxt))


def stations():
    data=pd.read_hdf(hdf_store,'stations')
    return data

def pre_process():
    format_stations()
    rainfall2hdf()    
    
if __name__ == "__main__":
    # pre_process() # takes several minutes (10min?) 
    freq="Y"
    staid = 'RR_STAID000094'
    ds = resampled(staid, freq, summ=TOTAL)
    
    dm = resampled(staid, freq, summ=MAX)
    ds2 = resampled('RR_STAID011416', summ=TOTAL)
    get_timelimits([ds,ds2])
    lf=linear_fit(ds)
    print(ds)