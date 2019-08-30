# -*- coding: utf-8 -*-
import sys
import json

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from plotly.colors import DEFAULT_PLOTLY_COLORS as COLORS
import pycountry
import datetime
import urllib.parse 

import pandas as pd
import pycountry
try:
    from data.SECRET  import mapbox_access_token
except: 
    mapbox_access_token="foo"

import rainproc as rp

BUTTONSTOREMOVE=['zoomIn2d', 'zoomOut2d', 'sendDataToCloud','hoverCompareCartesian', 
                 'sendDataToCloud', 'autoScale2d', 'hoverClosestCartesian', 'hoverCompareCartesian', 
                 'lasso2d', 'select2d', 'pan2d']

CONFIG={'modeBarButtonsToRemove': BUTTONSTOREMOVE, 'displaylogo': False,} 

app = dash.Dash('Rainfall trends in and around Europe')
server = app.server

station_df = rp.stations() 
graph1data = [ go.Scattermapbox(
        lat=station_df['LAT'],
        lon=station_df['LON'],
        mode='markers',
        text=station_df['TXT'],
        hoverinfo = 'text',
        customdata = station_df['STAID'],
        marker=dict(
            size=5,
        ),
        
    )]
graph1layout = go.Layout(
    autosize=True,
    hovermode='closest',
    mapbox=dict(
        accesstoken=mapbox_access_token,
        bearing=0,
        center=dict(
            lat=54,
            lon=15
        ),
        pitch=0,
        zoom=4,
    ),
    margin=go.Margin(
        l=10,
        r=10,
        b=10,
        t=30,
        pad=4
        ),    
)

graph1= dcc.Graph(
        id='stationmap',
        figure=dict(data=graph1data,
                    layout=graph1layout,
                    ),
        config=CONFIG
)

banner = html.Div([
    html.H2("Rainfall patterns in and around Europe"),
    html.Img(src=app.get_asset_url("apLogo2.png")),
], className='banner')

name = html.Div([html.H5("Assela Pathirana      (source: European Climate Assessment & Dataset)")], className='name')
row1 = html.Div([  # row 1 start ([
        html.Div(
            [graph1],
            className="twelve columns"),
], className="row")  # row 1 end ])


def plot_ts(pts, trange, freq, summ):
    print("TRANGE:", trange, file=sys.stderr)
    pts=[int(pt) for pt in pts]
    traces =[]
    for i,pt in enumerate(pts):
        data = resampled(pt,freq, summ)
        data = _subset_to_range(trange, data)
        marker = dict(
            size = 5,
            color=COLORS[i%10],
            line = dict(
                width = 1,
                color=COLORS[i%10],
            )
        ) 
        if (data['Rainfall_mm'].count()>=2): # at least 2 non-Nan values
            yfit, pval = rp.linear_fit(data)
        else:
            yfit=[]
            pval=1.0
        
        traces.append(go.Scatter(
            x=data.index,
            y=data['Rainfall_mm'],
            name=station_df.iloc[pt]['TXT']+" (trend, p={:4.4f})".format(pval),
            mode="markers+lines",
            marker=marker,       
        ))
        
        traces.append(go.Scatter( x=data.index, y=yfit, mode='lines',
                                hoverinfo='none',
                                showlegend=False,
                                marker=marker,))
    layout=go.Layout(
        #title="Annual Rainfall",
        showlegend= True,
        legend=dict(x=.1,y=1.0),
        xaxis=dict(
            title='Date',
            ),
        yaxis=dict(
            title="Precipitation (mm)",
            ),
        margin=go.Margin(l=50, r=10, b=50, t=30, pad=4),
    )    
        
    return {
        'data' : traces,
        'layout': layout
    }

def _subset_to_range(trange, data):
    if(trange):
        data=data['{}-01-01'.format(trange[0]):'{}-01-01'.format(trange[1]+1)]
    return data

def resampled(pt, freq, summ):
    data=rp.resampled(station_df.iloc[pt]['STAID'], freq, summ)
    return data


init_ind=station_df[station_df['STAID']=='RR_STAID000162'].index[0] # De Buit (NL)

graph2= dcc.Graph(id='stationgraph', config=CONFIG)
stat_display = html.Div(id='statdisplay')

row2 = html.Div([
    html.Div([graph2])
    ], className='row')
row3 = html.Div([
    html.Div([stat_display]),
    ], className='row')

sdd=dcc.Dropdown(
    id = 'station_dd',
    options=[dict(label=x[1], value=x[0]) for x in station_df['TXT'].to_dict().items()],
    value=[str(init_ind)],
    multi=True
)

timeslidediv=html.Div([dcc.RangeSlider(id='time_range')], id='slider_container', className='slider-box')
freqdd=html.Div([
    dcc.Dropdown(
        id='freqdd',
        options=[
            {'label': 'Yearly', 'value': 'Y'},
            {'label': 'Monthly', 'value': 'M'},
           # {'label': 'Daily', 'value': '24H'}
        ],
        value='Y',
    )
])

summarydd=html.Div([
    dcc.Dropdown(
        id='summarydd',
        options=[
            {'label': 'Total Rainfalls', 'value': rp.TOTAL},
            {'label': 'Maximum Rainfalls', 'value': rp.MAX},
        ],
        value=rp.TOTAL,
    )    
])

toolbar = html.Div([
    html.Div([sdd]),
    summarydd,
    freqdd,
    timeslidediv,
    ], className='row')


downloadl = html.A(
     'Download Data',
        id='download-link',
        download="rawdata.csv",
        href="",
        target="_blank"
 )

row4=html.Div([
    html.Div([downloadl])
    ], className='row')

app.layout = html.Div([  # begin container
    banner,
    name,
    row1,
    toolbar, 
    row2,
    row3,
    row4,
], className="container",
)  # end container


@app.callback(
    dash.dependencies.Output('download-link', 'href'),
    [dash.dependencies.Input('station_dd', 'value'),
     dash.dependencies.Input('time_range','value'),
     dash.dependencies.Input('freqdd','value'), 
     dash.dependencies.Input('summarydd', 'value')
     ])
def update_download_link(value, trange, freq, summarydd):
    dff=_dfs_list_as_one_df(value, trange, freq, summarydd)
    csv_string = dff.to_csv(index=True, encoding='utf-8')
    csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
    return csv_string

def _dfs_list_as_one_df(value, trange, freq, summarydd):
    pts=[int(pt) for pt in value[-3:]]
    dfs=_df_list(pts, freq, trange, summarydd)
    for i in range(len(dfs)):
        dfs[i]=dfs[i].rename(columns={"Rainfall_mm":station_df.iloc[pts[i]]['STANAME']})
    dff=dfs[0] # first
    for i in range(1,len(dfs)):
        dff=dff.join(dfs[i],rsuffix='_{:1d}'.format(i), how='outer')
    return dff


@app.callback(
    dash.dependencies.Output('slider_container', 'children'),
    [dash.dependencies.Input('station_dd', 'value'),
    ]
)
def new_slider(value):
    dfs=[resampled(int(v),'Y', rp.TOTAL) for v in value] # keep this annual. We just need limits as years. 
    mint,maxt=rp.get_timelimits(dfs)
    
    marks={int(x):str(int(x)) for x in rp.auto_tick([mint,maxt],max_tick=10)}
    ticks={int(x):'' for x in rp.auto_tick([mint,maxt],max_tick=20)}
    print("XXX:", marks, file=sys.stderr)
    sli=dcc.RangeSlider(
        id='time_range',
            min=mint,
            max=maxt,
            step=1,
            value=[mint,maxt],
            marks={
                mint: "",
                **ticks,
                **marks,
                maxt: "",                
            },
            
            
    )    
    return sli

@app.callback(
    dash.dependencies.Output('statdisplay', 'children'),
    [dash.dependencies.Input('station_dd', 'value'),
     dash.dependencies.Input('time_range','value'),
     dash.dependencies.Input('freqdd','value'),
     dash.dependencies.Input('summarydd','value'),
     
    ]
)
def display_stats(value, trange, freq, summ):
    print("STAT:", value, file=sys.stderr)
    return stats_astable(value[-3:], trange, freq, summ)

def stats_astable(pts, trange, freq, summ):
    alls=stat_from_indexes(pts, trange, freq, summ)   
    return html.Table(
        [html.Tr( [html.Th(x) for x in alls.keys()] )] 
        + 
        [ html.Tr([  html.Td(alls[k][i]) for k in alls.keys()]) for i in range(len(list(alls.values())[0]))],
    style={'width': "100%", 'table-layout':'fixed'})

def stat_from_indexes(pts, trange, freq, summ):
    pts=[int(pt) for pt in pts]
    dfs=_df_list(pts, freq, trange, summ)
    alls={**staindex2stadesc(pts), **rp.stats(dfs)}
    return alls

def _df_list(pts, freq, trange, summ):
    dfs=[]
    for pt in pts:
        data=resampled(pt, freq, summ)
        data=_subset_to_range(trange, data)
        dfs.append(data)
    return dfs

@app.callback(
    dash.dependencies.Output('station_dd', 'value'),
   [dash.dependencies.Input('stationmap', 'clickData')
    ],
   [dash.dependencies.State('station_dd','value')]
)
def update_station_dd(clickData, dd_value):
    if (clickData):
        pts = mapClickData2staindex(clickData)
    else:
        pts=[]
    return (dd_value+pts)[-3:]

@app.callback(
   dash.dependencies.Output('stationgraph', 'figure'),
   [dash.dependencies.Input('station_dd', 'value'),
    dash.dependencies.Input('time_range','value'),
    dash.dependencies.Input('freqdd','value'), 
    dash.dependencies.Input('summarydd','value'),
    ],
)
def display_chart(value, trange,freq, summ):
    #print("CHART:", value, file=sys.stderr)
    return plot_ts(value[-3:], trange, freq, summ)

def mapClickData2staindex(clickData):
    pts=[]
    for pt in clickData['points']:
        pts.append(station_df[station_df['STAID']==pt['customdata']].index[0])
    return pts

def staindex2stadesc(pts):
    res={'Station':[], 'Country':[], 'Elev.':[], 'LON/LAT':[]}
    for pt in pts:
        res['Station'].append(station_df.iloc[pt]['STANAME'])
        res['Country'].append(pycountry.countries.get(alpha_3=station_df.iloc[pt]['CN']).name)
        res['Elev.'].append('{:4.0f}'.format(station_df.iloc[pt]['HGHT']))
        res['LON/LAT'].append('{:3.2f}/{:3.2f}'.format(station_df.iloc[pt]['LON'],station_df.iloc[pt]['LAT']))
    return res


# load the styles
external_css = [
    "https://cdnjs.cloudflare.com/ajax/libs/skeleton/2.0.4/skeleton.min.css",
    app.get_asset_url("boxed_.css"),
    "https://codepen.io/chriddyp/pen/bWLwgP.css",
    "https://fonts.googleapis.com/css?family=Raleway:400,400i,700,700i",
    "https://fonts.googleapis.com/css?family=Product+Sans:400,400i,700,700i",
]

for css in external_css:
    app.css.append_css({"external_url": css})

if __name__ == '__main__':
    import os 
    import shutil
    if 'WINGDB_ACTIVE' in os.environ: 
        app.debug = False 
        # delete any static files (can keep old css etc. )
        try:
            shutil.rmtree("./assets/static")
        except:
            pass
        # also make sure to enable 'debug clild processes' in project properties. 
    app.run_server(use_reloader=True)     
    
    #app.run_server()
    #app.run_server(debug=True, use_debugger=False, use_reloader=True)
    #s=stats_astable([1,5],[],'Y')
    #plot_ts([1,5], [1992,2017], 'Y')
    #update_download_link([1], [1992,2017], 'Y')
    #print(s)