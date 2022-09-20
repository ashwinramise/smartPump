######## Imports ########
import dash
from dash.dependencies import Input, Output, State
from dash import dash_table
from dash import dcc
from dash import html
import pandas as pd
import dash_daq as daq
import plotly.express as px
from urllib.request import urlopen
import json
import dash_daq as daq
import dash_bootstrap_components as dbc
import textwrap
from datetime import datetime, timedelta, timezone
from collections import deque
import os
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from dbServices import dbServices
from mqttServices import pumpControl as ctrl

######## Imports ########

######## App Declarations ########
external_stylesheets = [dbc.themes.MINTY]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
app.config.suppress_callback_exceptions = True
######## App Declarations ########

logs = []

X = deque(maxlen=20)
Y = deque(maxlen=20)

users = {
    'mmuthumani@buckman.com': 'pass@123',
    'ramachandran@buckman.com': 'password',
    'mscatolin@buckman.com': 'password123'
}


def build_banner():
    return html.Div(
        id="banner",
        className="banner",
        children=[
            html.Div(
                id='buckman-logo',
                style={'width': '20%', 'display': 'inline-block', 'textAlign': 'left', 'verticalAlign': 'center'},
                children=[
                    html.A
                    (html.Img(id="logo2",
                              src='https://www.papnews.com/wp-content/uploads/2020/04/Buckman_Logo_Preferred_GREEN.png',
                              height="80px",
                              style={'textAlign': 'left', 'marginLeft':10}
                              ),
                     href="https://www.buckman.com/",
                     )
                ],
            ),
            html.Div(
                id="banner-text",
                children=[
                    html.H2("Smart Pump Monitoring and Control"),
                ],
                style={'textAlign': 'center', 'width': '60%', 'display': 'inline-block', 'verticalAlign': 'center'}
            ),
            html.Div(
                [
                    dbc.Button("Pages", id="open-offcanvas", n_clicks=0),
                    dbc.Offcanvas(children=[
                        html.Div([dbc.Button("Home", id="home", n_clicks=0)], style={'marginBottom': 5}),
                        html.Div([dbc.Button("Assets", id="assets", n_clicks=0)], style={'marginBottom': 5}),
                        html.Div(dbc.Button("Controls", id="controls", n_clicks=0, disabled=True))
                    ],
                        id="offcanvas",
                        title="Pages",
                        is_open=False,
                    ),
                    html.Div(dbc.Button("Login", id="login", n_clicks=0, disabled=False),
                             style={'display': 'inline-block',
                                    'marginLeft': 5}),
                    html.Div(dbc.Button("Learn More", id="learn-more-button", n_clicks=0, disabled=False),
                             style={'display': 'inline-block',
                                    'marginLeft': 5}),
                    html.Div(id='username'),
                    html.Div(
                        [
                            dbc.Modal(
                                id="modal",
                                is_open=False,
                                children=[
                                    dbc.ModalHeader(dbc.ModalTitle("Login")),
                                    dbc.ModalBody(
                                        [html.Div(
                                            [
                                                dbc.Label("Email", html_for="example-email"),
                                                dbc.Input(type="email", id="example-email", placeholder="Enter email",
                                                          value=''),
                                                dbc.FormText(
                                                    "example@buckman.com",
                                                    color="gray",
                                                ),
                                            ],
                                            className="mb-3",
                                        ),
                                            html.Div(
                                                [
                                                    dbc.Label("Password", html_for="example-password"),
                                                    dbc.Input(
                                                        type="password",
                                                        id="example-password",
                                                        placeholder="Enter password",
                                                    ),
                                                    dbc.FormText(
                                                        "Make sure its right",
                                                        color="gray"
                                                    ),
                                                ],
                                                className="mb-3",
                                            ),
                                            dbc.Button(
                                                "Submit", id="submit", className="ms-auto", n_clicks=0
                                            )
                                        ]
                                    ),
                                    dbc.ModalFooter(
                                        dbc.Button(
                                            "Close", id="close", className="ms-auto", n_clicks=0
                                        )
                                    )

                                ]
                            )
                        ]
                    ),
                    html.Div(
                        [
                            dbc.Modal(
                                id="modal2",
                                is_open=False,
                                children=[
                                    dbc.ModalHeader(dbc.ModalTitle("Learn More")),
                                    dbc.ModalBody(
                                        [html.Div(
                                            html.P(
                                                "This Dashboard allows us to remotely monitor the Grundfos DDA pump "
                                                "in the field and also allows us to have complete control over all "
                                                "the parameters that control the running of the pump "
                                            )
                                        ),
                                        ]
                                    ),
                                    dbc.ModalFooter(
                                        dbc.Button(
                                            "Close", id="close2", className="ms-auto", n_clicks=0
                                        )
                                    )

                                ]
                            )
                        ]
                    )
                ],
                style={'textAlign': 'center', 'width': '20%', 'display': 'inline-block', 'verticalAlign': 'center'}
            )
        ],
    )


@app.callback(
    Output("offcanvas", "is_open"),
    Input("open-offcanvas", "n_clicks"),
    [State("offcanvas", "is_open")],
)
def toggle_offcanvas(n1, is_open):
    if n1:
        return not is_open
    return is_open


@app.callback(
    [Output("example-email", "valid"),
     Output("example-email", "invalid")
     ],
    [Input("example-email", "value")],
)
def check_validity(user):
    for u in list(users.keys()):
        if user == u:
            return True, False
    return False, False


@app.callback(
    [Output("example-password", "valid"),
     Output("example-password", "invalid")
     ],
    [
        Input("example-password", "value"),
        Input("example-email", "value")],
)
def check_validity(pwd, user):
    if pwd == users[user]:
        return True, False
    return False, False


@app.callback(
    Output("modal", "is_open"),
    [Input("login", "n_clicks"),
     Input("close", "n_clicks"),
     Input("submit", "n_clicks"),
     ],
    [State("modal", "is_open")],
)
def toggle_modal(n1, n2, n3, is_open):
    if n1 or n2 or n3:
        return not is_open
    return is_open


@app.callback(
    Output("modal2", "is_open"),
    [Input("learn-more-button", "n_clicks"),
     Input("close2", "n_clicks")
     ],
    [State("modal2", "is_open")],
)
def toggle_modal2(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


@app.callback(
    [
        Output('controls', 'disabled'),
        Output('login', 'disabled'),
        Output('username', 'children')
    ],
    [
        Input("submit", "n_clicks"),
        Input("example-email", "value"),
        Input("example-password", "value"),
    ]
)
def editorpage(s, u, p):
    history = pd.read_csv(r'Data\user_logs.csv')
    history['Last_Access'] = [pd.Timestamp(d) for d in history['Last_Access']]
    loglist = history.to_dict('records')
    for r in loglist:
        if r not in logs:
            logs.append(r)
    if s and u in list(users.keys()) and p == users[u]:
        text = html.H6(u)
        logs.append({'User': u, 'Last_Access': pd.Timestamp(datetime.now())})
        pd.DataFrame.from_dict(logs).to_csv(r'Data\user_logs.csv', index=False)
        return False, True, text


def home():
    pass


def assets():
    pass


def control():
    return html.Div(
        style={'textAlign': 'center'},
        children=[
            html.Div(
                id='users-log',
                style={'marginTop': 15, 'width': "40%",
                       'display': 'inline-block', 'textAlign': 'center', 'marginRight': 40, 'verticalAlign': 'top'},
                children=[
                    html.Div(
                        [
                            html.Div(dcc.DatePickerRange(
                                id='my-date-picker-range',
                                end_date=datetime.now().date()
                            ), style={'display': 'inline-block', 'marginRight': 10}),
                            html.Div(dbc.Button(
                                "View Logs", id="logme", className="ms-auto", n_clicks=0),
                                style={'display': 'inline-block'}),
                        ]),
                    html.Div(
                        id='logs', style={'marginTop': 25},
                        children=[
                            html.Div(
                                [
                                    dcc.Graph(id='usage-stats'),
                                ],
                                style={'marginTop': 30}
                            )
                        ]
                    ),
                ]
            ),
            html.Div(
                id='risk-appetite',
                style={'marginTop': 15, 'width': "40%",
                       'display': 'inline-block', 'textAlign': 'center'},
                children=[
                    html.Div(html.H4("Set Pump Control Parameters")),
                    html.Div(
                        [
                            html.Div(
                                [
                                    dcc.Dropdown(
                                        id='site-1',
                                        multi=False,
                                        style={'height': 15},
                                        placeholder='Select Site',
                                        searchable=True
                                    )
                                ], style={'marginTop': 0, 'marginBottom': 10,
                                          'font-size': 18,
                                          'color': 'black',
                                          'width': '50%',
                                          'display': 'inline-block'}
                            ),
                            html.Div(
                                [
                                    dcc.Dropdown(
                                        id='pump-1',
                                        multi=False,
                                        style={'height': 15},
                                        placeholder='Select Pump',
                                        searchable=True
                                    )
                                ], style={'marginTop': 0, 'marginBottom': 10,
                                          'font-size': 18,
                                          'color': 'black',
                                          'width': '50%',
                                          'display': 'inline-block'}
                            ),
                            html.Div(
                                [
                                    html.H6("Pump Power:"),
                                    daq.PowerButton(
                                        id='powerON',
                                    )
                                ],
                                style={'marginTop': 15, 'textAlign': 'center'}
                            ),
                            html.Div(
                                [
                                    html.H6("Pump Speed: % "),
                                    html.Div(
                                        dcc.Slider(0, 100, 1, marks=None,
                                                   tooltip={"placement": "bottom",
                                                            "always_visible": True}
                                                   ),
                                        style={'marginTop': 25, 'textAlign': 'center', 'width': "100%",
                                               }
                                    )
                                ],
                                style={'marginTop': 25, 'textAlign': 'center', 'width': "100%",
                                       }
                            ),
                            html.Div(
                                [
                                    html.H6("Dosing Frequency: Seconds "),
                                    html.Div(
                                        dcc.Slider(min=0,
                                                   max=10,
                                                   step=0.1,
                                                   marks=None,
                                                   tooltip={"placement": "bottom",
                                                            "always_visible": True}
                                                   ),
                                        style={'marginTop': 25, 'textAlign': 'center', 'width': "100%",
                                               }
                                    )
                                ],
                                style={'marginTop': 25, 'textAlign': 'center', 'width': "100%",
                                       }
                            ),
                            dbc.Button(
                                "Submit", id="submit-2", className="ms-auto", n_clicks=0
                            )
                        ]
                    ),
                ]
            )
        ]
    )


@app.callback(
    [
     Output('usage-stats', 'figure')],
    [Input('my-date-picker-range', 'start_date'),
     Input('my-date-picker-range', 'end_date'),
     Input('logme', 'n_clicks')]
)
def updateLogs(d1, d2, clicks):
    if d1 is None:
        data = pd.read_csv(r'Data\user_logs.csv')
        data['Last_Access'] = [pd.Timestamp(i) for i in data['Last_Access'].tolist()]
        data.sort_values(by='Last_Access', ascending=False, inplace=True)
        t = f"Usage Statistics upto {d2}"
    elif d1 is not None and clicks:
        l = pd.read_csv(r'Data\user_logs.csv')
        l['Last_Access'] = [pd.Timestamp(i) for i in l['Last_Access'].tolist()]
        l['date'] = [d.date() for d in l['Last_Access'].tolist()]
        print(l['date'].to_list()[5], type(l['date'].to_list()[5]))
        data = l[(l['date'] <= pd.Timestamp(d2).date()) & (l['date'] > pd.Timestamp(d1).date())].sort_values(
            by='Last_Access',
            ascending=False)
        t = f"Usage Statistics from {d1} to {d2}"
    cols = [
        {"name": i, "id": i} for i in data.columns
    ]
    n = pd.DataFrame()
    n['Users'] = [u.split('@')[0] for u in data['User'].unique()]
    n['Counts'] = [data['User'].tolist().count(u) for u in data['User'].unique()]
    n.sort_values(by='Counts', inplace=True, ascending=False)
    use = px.bar(n, x='Users', y='Counts', color='Users', title=t)
    return [use]


@app.callback(
    Output('powerON', 'color'),
    Input('powerON', 'on')
)
def powerON(n):
    ctrl.powerPump(n)
    if n:
        color = '#63ff5e'
    if not n:
        color = '#e6110e'
    return color




app.layout = html.Div(
    style={'background': 'white', 'width': '100%', 'height': '100%'},
    id="big-app-container",
    children=[
        build_banner(),
    ]
)


@app.callback(
    output=[
        Output("big-app-container", "children"),
    ],
    inputs=[
        Input("home", "n_clicks"),
        Input("assets", "n_clicks"),
        Input("controls", "n_clicks"),
    ],
)
def getPages(h, a, c):
    if h > 0:
        return [[build_banner(), home()]]
    elif a > 0:
        return [[build_banner(), assets()]]
    elif c > 0:
        return [[build_banner(), control()]]


if __name__ == "__main__":
    app.run(debug=False)
