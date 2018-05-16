# -*- coding: utf-8 -*-
import sys
import json

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from plotly.colors import DEFAULT_PLOTLY_COLORS as COLORS
import pycountry

import pandas as pd
import pycountry
try:
    from data.SECRET  import mapbox_access_token
except: 
    mapbox_access_token="foo"

import rainproc as rp

app = dash.Dash('_template App', static_folder='static')
server = app.server

df = rp.stations() 
graph1data = [ go.Scattermapbox(
        lat=df['LAT'],
        lon=df['LON'],
        mode='markers',
        text=df['TXT'],
        hoverinfo = 'text',
        customdata = df['STAID'],
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
        t=10,
        pad=4
        ),    
)

graph1= dcc.Graph(
        id='stationmap',
        figure=dict(data=graph1data,
                    layout=graph1layout,
                    ),
        config={
            #'modeBarButtonsToRemove': ['pan2d', 'lasso2d']
        }
)

banner = html.Div([
    html.H2("_template"),
    html.Img(src="/static/apLogo2.png"),
], className='banner')

row1 = html.Div([  # row 1 start ([
        html.Div(
            [graph1],
            className="twelve columns"),
], className="row")  # row 1 end ])


def plot_ts(pts):
    traces =[]
    for i,pt in enumerate(pts):
        data = resampled(pt)
        
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
            name=df.iloc[pt]['TXT']+" trend (p={:4.4f})".format(pval),
            mode="markers+lines",
            marker=marker,       
        ))
        
        traces.append(go.Scatter( x=data.index, y=yfit, mode='lines',
                                hoverinfo='none',
                                showlegend=False,
                                marker=marker,))
    layout=go.Layout(
        title="Annual Rainfall",
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

def resampled(pt):
    data=rp.resampled(df.iloc[pt]['STAID'], 'Y')
    return data


ind=df[df['STAID']=='RR_STAID000162'].index[0] # De Buit (NL)

graph2= dcc.Graph(id='stationgraph')
stat_display = html.Div(id='statdisplay')

row2 = html.Div([
    html.Div([graph2])
    ], className='row')
row3 = html.Div([
    html.Div([stat_display]),
    ], className='row')

app.layout = html.Div([  # begin container
    banner,
    row1,
    row2,
    row3,
], className="container",
)  # end container


@app.callback(
    dash.dependencies.Output('statdisplay', 'children'),
    [dash.dependencies.Input('stationmap', 'clickData'),
     ]
)
def display_stats(clickData):
    print("STAT:", clickData, file=sys.stderr)
    if (clickData):
        pts = mapClickData2staindex(clickData)
    else:
        pts=[ind]
    print(stats(pts), file=sys.stderr)
    return stats(pts)

def stats(pts):
    dfs=[]
    for pt in pts:
        dfs.append(resampled(pt))
    alls={**staindex2stadesc(pts), **rp.stats(dfs)}
    
    return html.Table(
        [
            html.Tr( [html.Th(x) for x in alls.keys()] )
        ] +
        
        [ html.Tr([  html.Td(alls[k][i]) for k in alls.keys()]) for i in range(len(list(alls.values())[0]))]
            #for i in alls.values()[0]:
            #html.Tr( [html.Td("walter"), html.Td("rudin"), html.Td("wr@analysis.com")] ),
            #html.Tr( [html.Td("gilbert"), html.Td("strang"), html.Td("gb@algebra.com")] )
        
    )
    

@app.callback(
   dash.dependencies.Output('stationgraph', 'figure'),
   [dash.dependencies.Input('stationmap', 'clickData'),
    ]
)
def display_chart(clickData):
    print("CHART:", clickData, file=sys.stderr)
    if (clickData):
        pts = mapClickData2staindex(clickData)
    else:
        pts=[ind]
    return plot_ts(pts)

def mapClickData2staindex(clickData):
    pts=[]
    for pt in clickData['points']:
        pts.append(df[df['STAID']==pt['customdata']].index[0])
    return pts

def staindex2stadesc(pts):
    res={'Station':[], 'Country':[], 'Elevation':[], 'LON':[], 'LAT':[],}
    for pt in pts:
        res['Station'].append(df.iloc[pt]['STANAME'])
        res['Country'].append(pycountry.countries.get(alpha_3=df.iloc[pt]['CN']).name)
        res['Elevation'].append('{:5.0f}'.format(df.iloc[pt]['HGHT']))
        res['LON'].append('{:5.3f}'.format(df.iloc[pt]['LON']))
        res['LAT'].append('{:5.3f}'.format(df.iloc[pt]['LAT']))
    return res


# load the styles
external_css = [
    "https://cdnjs.cloudflare.com/ajax/libs/skeleton/2.0.4/skeleton.min.css",
    "/static/boxed.css",
    "https://fonts.googleapis.com/css?family=Raleway:400,400i,700,700i",
    "https://fonts.googleapis.com/css?family=Product+Sans:400,400i,700,700i",
]

for css in external_css:
    app.css.append_css({"external_url": css})

if __name__ == '__main__':
    app.run_server(debug=True, use_debugger=False, use_reloader=True)
    s=stats([1,5])
    plot_ts([1,5])
    print(s)