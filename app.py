# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html

app = dash.Dash('_template App', static_folder='static')
server = app.server

graph1= dcc.Graph(
        id='example-graph')

banner = html.Div([
    html.H2("_template"),
    html.Img(src="/static/apLogo2.png"),
], className='banner')

row1 = html.Div([  # row 1 start ([
        html.Div(
            [graph1],
            className="twelve columns"),
], className="row")  # row 1 end ])


app.layout = html.Div([  # begin container
    banner,
    row1,
], className="container",
)  # end container

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