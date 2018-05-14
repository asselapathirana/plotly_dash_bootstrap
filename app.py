# -*- coding: utf-8 -*-
import sys
import json

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from plotly.colors import DEFAULT_PLOTLY_COLORS as COLORS

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
            'displayModeBar': False} 
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

graph2= dcc.Graph(
    id='stationgraph')
stat_display = html.Div(id='statdisplay')

row2 = html.Div([  # row 2 start ([
                html.Div([graph2], className="eight columns"),
                html.Div([stat_display], className="four columns"),                   
], className="row")  # row 2 end ])

app.layout = html.Div([  # begin container
    banner,
    row1,
    row2,
], className="container",
)  # end container


@app.callback(
    dash.dependencies.Output('statdisplay', 'children'),
    [dash.dependencies.Input('stationmap', 'clickData'),
     ]
)
def display_stats(clickData):
    #print(clickData, file=sys.stderr)
    return html.Pre( json.dumps(clickData, indent=2))


@app.callback(
    dash.dependencies.Output('stationgraph', 'figure'),
    [dash.dependencies.Input('stationmap', 'clickData'),
     ]
)


def display_chart(clickData):
    print(clickData, file=sys.stderr)
    bars =[]
    for i,pt in enumerate(clickData['points']):
        df=rp.resampled(pt['customdata'], 'Y')
        
        marker = dict(
            size = 5,
                color=COLORS[i%10],
                line = dict(
                    width = 1,
                    color=COLORS[i%10],
                )
        )             
        
        bars.append(go.Scatter(
            x=df.index,
            y=df['Rainfall_mm'],
            name=pt['text'],
            mode="markers+lines",
            marker=marker,       
            
        ))
        yfit, pval = rp.linear_fit(df)
        bars.append(go.Scatter( x=df.index, y=yfit, mode='lines',
                                name=pt['text']+" trend (p-value for slope {:4.4f})".format(pval),
                                hoverinfo='none',
                                marker=marker,))
        
    return {
        'data' : bars,
        'layout':  go.Layout(
                title="Annual Rainfall",
                showlegend= True,
                legend=dict(x=.1,y=1.0),
                xaxis=dict(
                    title='Date',
                    ),
                yaxis=dict(
                    title="Precipitation (mm)",
                ),
            
            margin=go.Margin(
                l=50,
                r=10,
                b=50, 
                t=70,
                pad=4
                ),
            ),
            
    }


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