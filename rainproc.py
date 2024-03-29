import chardet
import pandas as pd
import pycountry
import numpy as np
import statsmodels.formula.api as smf
import requests
import io


notmissingthres = {"YE":365*.9, "ME":30*.9, "WE":7*.9, "Q":365/4*.9, "24H":.9}

USEONLINE=True

#feather_store_online = 'http://data.pathirana.net/feather/STN{}'
#station_store_online = 'http://data.pathirana.net/feather/stations.feather'    
feather_store = './data/feather/STN{}'
station_store = './data/feather/stations.feather'

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

def read_rain_from_csv(file):
    tomm= lambda x: np.NaN if float(x) < 0 else 0.1*float(x) # negative values = missing data
    with open(file,'rb') as f:
        data = f.read()  # or a chunk, f.read(1000000)
    encoding=chardet.detect(data).get("encoding")
    
    df = pd.read_csv(file, encoding=encoding, names=["Date", "Rainfall_mm"], index_col="Date", usecols=[2,3], header=15, parse_dates=['Date'], converters={'Rainfall_mm':tomm})
    df.replace(-9999, np.nan, inplace=True)
    return df.reset_index()



def read_rain_HDF(hdfstore, name, file):
    tomm= lambda x: np.NaN if float(x) < 0 else 0.1*float(x) # negative values = missing data
    df = pd.read_csv(file, names=["Date", "Rainfall_mm"], index_col="Date", usecols=[2,3], header=16, parse_dates=['Date'], converters={3:tomm})
    df.replace(-9999, np.nan, inplace=True)
    hdfstore.put(name,df, **COMP)

def rainfallcsv2feather():
    stns = pd.read_feather(station_store, columns=['STAID'])
    ct=0
    for index, s in stns.iterrows():
        stnid=s['STAID']
        fs=feather_store.format(stnid)
        read_rain_from_csv( './data/eca_blend_rr/{}.txt'.format(stnid)).to_feather(fs)
        ct+=1
        #if (ct>10): break;
        
        
def resampled(staid,freq, summ):
    #try:
    data = pd.read_feather(feather_store.format(staid))
    #except:
    #    response = requests.get(feather_store_online.format(staid))
    #    
    #    f=io.BytesIO(response.content)
    #    data = pd.read_feather(f)            

    # set the index to Date
    data.set_index('Date', inplace=True)
    
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
    data['ndates'] = (data.index-pd.to_datetime('1800-01-01')).days
    ft=smf.ols( '{} ~ {}'.format(ycol,xcol), data=data, missing='drop' ).fit()
    return ft.params.ndates*data.ndates+ft.params.Intercept, ft.pvalues.ndates, ft.params.ndates

def format_stations(stfile="./data/eca_blend_rr/stations.txt"):
    def dms2dd(v):
        v=[float(x.strip()) for x in v.split(':')]
        return v[0]+v[1]/60.+v[2]/3600.
    def country2to3(x):
        try:
            return pycountry.countries.get(alpha_2=x.strip()).alpha_3
        except:
            return None
            

    strp=lambda x: x.strip()
    clean_data(stfile)
    stationsdf = pd.read_csv(stfile+".out", sep=',', converters={1:strp, 2:country2to3, 3:dms2dd, 4:dms2dd})
    stationsdf.rename(inplace=True, columns=lambda x: x.strip())
    stationsdf.dropna(axis=0,  inplace=True)
    stationsdf['STAID']=stationsdf['STAID'].apply('RR_STAID{0:06d}'.format, 8)
    stationsdf['TXT']=stationsdf['STANAME']+" ("+stationsdf['CN']+")"
    
    #with  pd.to_fea(station_store,"w") as hdfstore:
    #    hdfstore.put('stations',stationsdf, **COMP)
    stationsdf.reset_index().to_feather(station_store)   

def clean_data(stfile):
    found=False
    with open(stfile+".out", 'w', encoding="utf-8") as ofile:
        with open(stfile, encoding='utf-8') as myFile:
            for num, line in enumerate(myFile, 1):
                if 'STAID,STANAME' in line:
                    found=True
                if (found) and line.strip()!="": ofile.write(line)

def stats(dfs):
    res=[]
    for ds in dfs:
        res.append(get_stat_for_dataset(ds))
    resd={}
    for k in res[0]:
        resd[k] = tuple(d[k] for d in res)    
    return resd

def get_stat_for_dataset(ds):
    return dict(
    missing='{:.2%}'.format(ds['Rainfall_mm'].isnull().sum()/ds['Rainfall_mm'].shape[0]),
    mean="{:8.2f}".format(ds['Rainfall_mm'].mean()),
    std="{:8.2f}".format(ds['Rainfall_mm'].std()),
    length="{:10d}".format(ds['Rainfall_mm'].shape[0]),
    maxv="{:8.1f}".format(ds['Rainfall_mm'].max()),
    minv="{:8.1f}".format(ds['Rainfall_mm'].min()),
    )
 
def get_timelimits(dfs):
    maxt=[]
    mint=[]
    for ds in dfs:
        maxt.append(ds.index.max().to_pydatetime().year)
        mint.append(ds.index.min().to_pydatetime().year)
    return (min(mint),max(maxt))


def stations():
    #response = requests.get(station_store_online)
    #f=io.BytesIO(response.content)
    data = pd.read_feather(station_store)    
    return data

def add_stats_to_stations():
    """Calculate missing data % and legnth of each series and append to stations df"""
    stns = pd.read_feather(station_store)
    #ct=0
    stns['LENGTH']=np.nan
    stns['MISSING']=np.nan
    try:
        for index, s in stns.iterrows():
            stnid=s['STAID']
            FILE='./data/eca_blend_rr/{}.txt'.format(stnid)
            df=read_rain_from_csv(FILE)
            missing=df['Rainfall_mm'].isnull().sum()/df['Rainfall_mm'].shape[0]
            print(FILE, missing)
            length=df['Rainfall_mm'].shape[0]/360.  # convert to years.
            stns.iloc[index, stns.columns.get_loc('LENGTH')] = length
            stns.iloc[index, stns.columns.get_loc('MISSING')] = missing
            stns.iloc[index, stns.columns.get_loc('TXT')] = s['TXT'] +  ' ({:.0f}y with m={:.3%})'.format(length, missing)
            #ct+=1
    except Exception as e:
        print("Error in add_stats_to_stations stations:", e)
        print("I assume this is for testing. I will remove the rest of the station entries and continue.")
        input("Press Enter to continue...")
        stns.dropna(axis=0, inplace=True)
    stns.to_feather(station_store) 

def pre_process():
    try:
        format_stations()
    except Exception as e:
        print("Error in formatting stations:", e)
        input("Press Enter to continue...")

    try:
        rainfallcsv2feather() 
    except Exception as e:
        print("Error in rainfallcsv2feather stations:", e)
        input("Press Enter to continue...")
    try:
        add_stats_to_stations()
    except Exception as e:
        print("Error in add_stats_to_stations stations:", e)
        input("Press Enter to continue...")
if __name__ == "__main__":
    pre_process() # takes several minutes (10min?) 
    freq="ME"
    staid = 'RR_STAID000004'
    ds = resampled(staid, freq, summ=TOTAL)
    
    dm = resampled(staid, freq, summ=MAX)
    #ds2 = resampled('RR_STAID011416', summ=TOTAL)
    #get_timelimits([ds,ds2])
    lf=linear_fit(ds)
    print(lf)
