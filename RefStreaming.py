import warnings
warnings.filterwarnings("ignore")
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import dash_daq as daq
import datetime as dt
import pandas as pd
from dbConnect import dbServices as db
from collections import deque

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    external_stylesheets=external_stylesheets
)

X = deque(maxlen=20)
Y = deque(maxlen=20)

tab_style = {
    'padding': '6px',
    'background': '#040830',
    'color': 'white'
}

app_color = { "graph_bg": "#792721", "graph_line": "#009BEF"}

app.title = "ISE CNC Dashboard"
server = app.server
app.config["suppress_callback_exceptions"] = True


def build_banner():
    return html.Div(
        style=tab_style,
        id="banner",
        className="banner",
        children=[
            html.Div(
                id='ncsu-logo',
                style={'width': '33.33%', 'display': 'inline-block', 'textAlign': 'left', 'verticalAlign': 'center'},
                children=[
                    html.A
                    (html.Img(id="logo2", src='https://brand.ncsu.edu/img/logo/brick2x2.jpg', height="50px",
                              style={'textAlign': 'left'}
                              ),
                     href="https://www.ncsu.edu/",
                     )
                ],
            ),
            html.Div(
                id="banner-text",
                children=[
                    html.H5("ISE 725 Smart Manufacturing Dashboard"),
                ],
                style={'textAlign': 'center', 'width': '33.33%', 'display': 'inline-block', 'verticalAlign': 'center'}
            ),
            html.Div(
                id="banner-logo",
                style={'width': '33.33%', 'display': 'inline-block', 'textAlign': 'right', 'verticalAlign': 'center'},
                children=[
                    html.Button(
                        id="learn-more-button", children="LEARN MORE", n_clicks=0, style={'verticalAlign': 'center',
                                                                                          'marginRight': 10}
                    ),
                    html.A(
                        html.Img(id="logo", src='https://www.ise.ncsu.edu/wp-content/uploads/2016/01/'
                                                'ise-symbol-logo-01.jpg', height='50px'),
                        style={'verticalAlign': 'center',
                               'marginRight': 10},
                        href="https://www.ise.ncsu.edu/",
                    ),
                ],
            ),
        ],
    )


def generate_modal():
    return html.Div(
        id="markdown",
        className="modal",
        style=tab_style,
        children=(
            html.Div(
                id="markdown-container",
                className="markdown-container",
                children=[
                    html.Div(
                        className="close-container",
                        children=html.Button(
                            "Close",
                            id="markdown_close",
                            n_clicks=0,
                            className="closeButton",
                        ),
                    ),
                    html.Div(
                        className="markdown-text",
                        style=tab_style,
                        children=dcc.Markdown(
                            children=(
                                """
                        ##### Overview:
                        This dashboard is created for the purpose of demonstrating a plotly dashboard can 
                        access the data in a PostgreSQL database located on a heroku cloud server. 
                        All code is written in python and the protocol used to transmit data is MQTT. 
                    """
                            )
                        ),
                    ),
                ],
            )
        ),
    )


def build_hmi():
    return html.Div(style=tab_style,
                    children=[
                        html.Div(
                            className='twelve columns',
                            children=[
                                html.P('Machine_1'),
                            ],
                            style={'marginTop': 10, 'marginBottom': 30,
                                   'font-size': 18,
                                   'color': 'white',
                                   'background': '#040830'
                                   }
                        ),

                        html.Div(
                            style=tab_style,
                            id="card-0",
                            children=[
                                daq.LEDDisplay(
                                    id="machine-led",
                                    label="machine ID",
                                    labelPosition="top",
                                    value="1521",
                                    color="#92e0d3",
                                    backgroundColor="#1e2130",
                                    size=50,
                                    style={'width': '25%', 'display': 'inline-block',
                                           'verticalAlign': 'center'}
                                        ),
                                daq.Tank(
                                    id="humidity",
                                    label="Humidity",
                                    labelPosition="top",
                                    min=0,
                                    max=100,
                                    showCurrentValue=True,
                                    units='%',
                                    style={'width': '25%', 'display': 'inline-block',
                                           'verticalAlign': 'center'}
                                        ),
                                daq.Gauge(
                                    color={"gradient": True,
                                           "ranges": {"green": [0, 60], "yellow": [60, 80], "red": [80, 100]}},
                                    label="Temperature deg F",
                                    labelPosition="top",
                                    id="temperature-gauge",
                                    # max=max_length * 2,
                                    min=0,
                                    showCurrentValue=True,  # default size 200 pixel
                                    max=100,
                                    style={'width': '25%', 'display': 'inline-block',
                                           'verticalAlign': 'center'}
                                        ),
                                daq.Gauge(
                                    color={"gradient": True,
                                           "ranges": {"green": [0, 60], "yellow": [60, 80], "red": [80, 100]}},
                                    label="Pressure kPa",
                                    labelPosition="top",
                                    id="pressure-gauge",
                                    # max=max_length * 2,
                                    min=0,
                                    showCurrentValue=True,  # default size 200 pixel
                                    max=100,
                                    style={'width': '25%', 'display': 'inline-block',
                                           'verticalAlign': 'center'}
                                )
                                    ]
                        ),

                        html.Div(
                            style=tab_style,
                            children=[
                                dcc.Graph(id= "sensor-temperature", animate=True)
                            ]
                        )
            ]
    )


app.layout = html.Div(
    style={'background': '#333333', 'width': '100%','height': '100%'},
    id="big-app-container",
    children=[
        build_banner(),
        generate_modal(),
        dcc.Interval(
            id="interval-component",
            interval=1*1000,  # in milliseconds
            n_intervals=0,
            disabled=False,
        ),
        html.Div(
            id="app-container",
            children=[
                build_hmi()
            ],
        ),
    ],
)


# ======= Callbacks for modal popup =======
@app.callback(
    Output("markdown", "style"),
    [Input("learn-more-button", "n_clicks"), Input("markdown_close", "n_clicks")],
)
def update_click_output(button_click, close_click):
    ctx = dash.callback_context

    if ctx.triggered:
        prop_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if prop_id == "learn-more-button":
            return {"display": "block"}

    return {"display": "none"}


# ======= update progress gauge =========
@app.callback(
    output=[Output("temperature-gauge", "value"),
            Output("pressure-gauge", "value"),
            Output("machine-led", "value"),
            Output("humidity", "value"),
            Output("sensor-temperature", "figure")],
    inputs=[Input("interval-component", "n_intervals")],
)
def update_gauge(interval):
    tablename = "sensorData"
    if interval < 20000:
        temperature = db.getData(tablename)['temperature'].tolist()[0]
        pressure = db.getData(tablename)['pressure'].tolist()[0]
        machine_id = db.getData(tablename)['machine_id'].tolist()[0]
        humidity = db.getData(tablename)['humidity'].tolist()[0]
        X.append(get_current_time())
        Y.append(temperature)
        data = go.Scatter(
            x=list(X),
            y=list(Y),
            name='Scatter',
            mode='lines+markers'
        )
        figure = {'data': [data], 'layout': go.Layout(xaxis=dict(range=[min(X), max(X)]),
                                             yaxis=dict(range=[min(Y), max(Y)]), title="Sensor Temperature Live",)}
        return temperature, pressure, machine_id, humidity, figure


#---Helper function
def get_current_time():
    now = dt.datetime.now()
    total_time = (now.hour * 3600) + (now.minute * 60) + (now.second)
    return total_time


if __name__ == "__main__":
    app.run_server(debug=False)


