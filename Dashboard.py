######## Imports ########
import dash
from dash.dependencies import Input, Output, State
from dash import dash_table
from dash import dcc
from dash import html
import pandas as pd
import dash_daq as daq
import plotly.express as px
import plotly.graph_objects as go
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
import warnings

warnings.filterwarnings("ignore")

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from dbServices import dbServices as db
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
X1 = deque(maxlen=20)
Y1 = deque(maxlen=20)
X2 = deque(maxlen=20)
Y2 = deque(maxlen=20)
X3 = deque(maxlen=20)
Y3 = deque(maxlen=20)

####### Assets #####
assets = db.getData("PoC_SP_Assets", "RecordID")

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
                              style={'textAlign': 'left', 'marginLeft': 10}
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
                        html.Div([dbc.Button("Logs", id="log", n_clicks=0)], style={'marginBottom': 5}),
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
    history = db.getData('PoC_SP_UserLogs', 'RecordID')
    if len(history['RecordID'].tolist()) == 0:
        record = 0
    else:
        record = history['RecordID'].tolist()[0]
    history['Last_Access'] = [pd.to_datetime(d) for d in history['Last_Access']]
    loglist = history.to_dict('records')
    existing = [i['RecordID'] for i in logs]
    for r in loglist:
        if r['RecordID'] not in existing:
            logs.append(r)
    if s and u in list(users.keys()) and p == users[u]:
        text = html.H6(u)
        new_record = {'RecordID': record + 1, 'User': u, 'Last_Access': str(datetime.now())}
        logs.append(new_record)
        db.writeValues(new_record, 'PoC_SP_UserLogs')
        return False, True, text


def home():
    return html.Div(
        style={'textAlign': 'center'},
        children=[
            html.Div(
                style={'marginTop': 15, 'width': "40%",
                       'display': 'inline-block', 'textAlign': 'center', 'marginRight': 40, 'verticalAlign': 'top'},
                children=[
                    html.Div(
                        [
                            dcc.Dropdown(
                                id='site-2',
                                multi=False,
                                style={'height': 15},
                                placeholder='Select Site',
                                options=assets['Location'].unique(),
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
                                id='pump-2',
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
                    )
                ]
            ),
            html.Div(
                style={'textAlign': 'center'},
                children=[
                    html.Div([
                        html.Div(
                            children=
                            [
                                dbc.Card(
                                    dbc.CardBody(
                                        id='power-status',
                                    ),
                                    style={"width": "18rem"},
                                )
                            ], style={'display': 'inline-block', 'marginLeft': 15}
                        ),
                        html.Div(
                            children=
                            [
                                dbc.Card(
                                    dbc.CardBody(id='dosing-pressure',
                                                 ),
                                    style={"width": "18rem"},
                                )
                            ], style={'display': 'inline-block', 'marginLeft': 15}
                        ),
                        html.Div(
                            children=
                            [
                                dbc.Card(
                                    dbc.CardBody(id='flow-rate-act',
                                                 ),
                                    style={"width": "18rem"},
                                )
                            ], style={'display': 'inline-block', 'marginLeft': 15}
                        )
                    ], style={'marginTop': 15, 'textAlign': 'center'}
                    ),
                ]
            ),
            html.Div(
                style={'marginTop': 15, 'textAllign': 'left'},
                children=[
                    html.Div
                        (
                        [
                            html.Div(
                                id='met1',
                                style={'marginLeft': 2, 'marginRight': 2,
                                       'display': 'inline-block'},
                                children=[dcc.Graph(id='speed2')]
                            ),
                            html.Div(
                                id='met2',
                                style={'marginLeft': 2, 'marginRight': 2,
                                       'display': 'inline-block'},
                                children=[dcc.Graph(id='head1')]
                            )
                        ],
                        style= {'width':'50%', 'display': 'inline-block'}
                    ),
                    html.Div(
                        id='met3',
                        style={'marginLeft': 2, 'marginRight': 2, 'width': '35%',
                               'display': 'inline-block'},
                        children=[dcc.Graph(id='motortemp')]
                    ),
                ]
            )
        ]
    )


@app.callback(
    [Output('power-status', 'children'),
     Output('dosing-pressure', 'children'),
     Output('flow-rate-act', 'children'),
     Output('speed2', 'figure'),
     Output('head1', 'figure')],
    [Input('site-2', 'value'),
     Input('pump-2', 'value'),
     Input("interval-component", "n_intervals")]
)
def retCounts(site, pump, interval):
    if interval < 20000:
        if site is None and pump is None:
            return "Make Selection", "Make Selection", "Make Selection"
        elif site is not None and pump is None:
            return "Select a Pump", "Select a Pump", "Select a Pump"
        elif site and pump:
            df = db.getData("PoC_SP_Metrics", "RecordID")
            df = df[(df['site'] == site) & (df['pumpID'] == pump)].head(1)
            h = df['104'].tolist()[0]
            if int(h) == 1:
                disp_h = [
                    html.H4("Pump Status", className="card-title"),
                    html.P(
                        html.H1("Disabled", style={'color': 'red'}),
                        className="card-text",
                    ),
                ]
            elif int(h) == 0:
                disp_h = [
                    html.H4("Pump Status", className="card-title"),
                    html.P(
                        html.H1("Enabled", style={'color': '#33cc33'}),
                        className="card-text",
                    ),
                ]
            pressure = float(df['312'].tolist()[0]) / 1000
            disp_m = [
                html.H4("Total Volume (l)", className="card-title"),
                html.P(
                    html.H1(int(pressure), style={'color': 'Purple'}),
                    className="card-text",
                ),
            ]
            flowRate = int(df['208'].tolist()[0]) / 10000
            disp_l = [
                html.H4("Flow Rate (l/h)", className="card-title"),
                html.P(
                    html.H1(float(flowRate), style={'color': 'blue'}),
                    className="card-text",
                ),
            ]
            speed = flowRate
            t = df['Timestamp'].tolist()[0]
            X1.append(t)
            Y1.append(speed)
            data = go.Scatter(
                x=list(X1),
                y=list(Y1),
                name='Scatter',
                mode='lines+markers'
            )
            flowFig = {'data': [data], 'layout': go.Layout(xaxis=dict(range=[min(X1), max(X1)]),
                                                           yaxis=dict(range=[min(Y1), max(Y1)]),
                                                           title="Pump Speed Live", )}
            Y2.append(pressure)
            data2 = go.Scatter(
                x=list(X1),
                y=list(Y2),
                name='Scatter',
                mode='lines+markers'
            )
            flowFig2 = {'data': [data2], 'layout': go.Layout(xaxis=dict(range=[min(X1), max(X1)]),
                                                           yaxis=dict(range=[min(Y2), max(Y2)]),
                                                           title="Total Volume Live", )}
            return disp_h, disp_m, disp_l, flowFig, flowFig2


@app.callback(
    Output('pump-2', 'options'),
    Input('site-2', 'value'),
)
def getpump(location):
    pump = assets[assets['Location'] == location]
    r = pump['PumpName'].unique().tolist()
    return [{'label': i, 'value': i} for i in r]


def history():
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
                        id='usage-g', style={'marginTop': 25},
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
                id='logs',
                style={'marginTop': 15, 'width': "60%",
                       'display': 'inline-block', 'textAlign': 'center', 'marginRight': 40, 'verticalAlign': 'top'},
            )
        ]
    )


@app.callback(
    [Output('logs', 'children'),
     Output('usage-stats', 'figure')],
    [Input('my-date-picker-range', 'start_date'),
     Input('my-date-picker-range', 'end_date'),
     Input('logme', 'n_clicks')]
)
def updateLogs(d1, d2, clicks):
    print(len(logs))
    data = pd.DataFrame.from_dict(logs)
    if d1 is None:
        # data = db.getData("PoC_SP_UserLogs", "RecordID")
        data['Last_Access'] = [pd.to_datetime(i) for i in data['Last_Access'].tolist()]
        data.sort_values(by='Last_Access', ascending=False, inplace=True)
        t = f"Usage Statistics upto {d2}"
    elif d1 is not None and clicks:
        l = data
        l['Last_Access'] = [pd.to_datetime(i) for i in l['Last_Access'].tolist()]
        l['date'] = [d.date() for d in l['Last_Access'].tolist()]
        data = l[(l['date'] <= pd.Timestamp(d2).date()) & (l['date'] > pd.Timestamp(d1).date())].sort_values(
            by='Last_Access',
            ascending=False)
        t = f"Usage Statistics from {d1} to {d2}"
    cols = [
        {"name": i, "id": i} for i in data.columns
    ]
    rows = data.to_dict('records')
    table = [
        dash_table.DataTable(
            id='data-table',
            columns=cols,
            style_cell={
                'textAlign': 'center',
                'font_size': '15px'
            },
            data=rows,
            editable=False,
            filter_action="native",
            sort_action="native",
            sort_mode="multi",
            page_action="native",
            page_current=0,
            page_size=20,
        )
    ]
    n = pd.DataFrame()
    n['Users'] = [u.split('@')[0] for u in data['User'].unique()]
    n['Counts'] = [data['User'].tolist().count(u) for u in data['User'].unique()]
    n.sort_values(by='Counts', inplace=True, ascending=False)
    use = px.bar(n, x='Users', y='Counts', color='Users', title=t)
    return table, use


def control():
    return html.Div(
        style={'textAlign': 'center'},
        children=[
            html.Div(
                id='live-graphs',
                style={'marginTop': 15, 'width': "55%",
                       'display': 'inline-block', 'textAlign': 'center', 'marginRight': 40, 'verticalAlign': 'top'},
                children=[
                    html.Div(
                        id='live-view', style={'marginTop': 25},
                        children=[
                            html.Div(
                                [
                                    dcc.Graph(id='pump-speed1'),
                                ],
                                style={'marginBottom': 5}
                            ),
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
                                        options=assets['Location'].unique(),
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
                                        options=['Pump1', 'Pump2'],
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
                                        on=False
                                    )
                                ],
                                style={'marginTop': 15, 'textAlign': 'center'}
                            ),
                            html.Div(
                                [
                                    html.H6("Flow Rate (l/h) "),
                                    html.Div(
                                        daq.Knob(
                                            id='flow-rate',
                                            size=140,
                                            max=6.3,
                                            value=None,
                                            persistence=True,
                                            persisted_props=True,
                                        )
                                        ,
                                        style={'marginTop': 25, 'textAlign': 'center', 'width': "100%",
                                               }
                                    )
                                ],
                                style={'marginTop': 25, 'textAlign': 'center', 'width': "100%",
                                       }
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        daq.LEDDisplay(
                                            id='flow-rate-monitor',
                                            color="#FF5E5E"
                                        ),
                                        style={'marginTop': 25, 'textAlign': 'center', 'width': "100%",
                                               }
                                    )
                                ],
                                style={'marginTop': 25, 'textAlign': 'center', 'width': "100%",
                                       }
                            )
                        ]
                    ),
                ]
            )
        ]
    )


@app.callback(
    Output('pump-speed1', 'figure'),
    [Input('site-1', 'value'),
     Input('pump-1', 'value'),
     Input("interval-component", "n_intervals")]
)
def updatespeed(site, pump, interval):
    if interval < 20000 and site is not None and pump is not None:
        df = db.getData("PoC_SP_Metrics", "RecordID")
        df = df[(df['site'] == site) & (df['pumpID'] == pump)].head(1)
        t = df['Timestamp'].tolist()[0]
        speed = float(df['208'].tolist()[0]) / 10000
        X.append(t)
        Y.append(speed)
        data = go.Scatter(
            x=list(X),
            y=list(Y),
            name='Scatter',
            mode='lines+markers'
        )
        figure = {'data': [data], 'layout': go.Layout(xaxis=dict(range=[min(X), max(X)]),
                                                      yaxis=dict(range=[min(Y), max(Y)]),
                                                      title="Pump Speed Live",)}
        return figure


@app.callback(
    Output('pump-1', 'options'),
    Input('site-1', 'value'),
)
def getpump(location):
    pump = assets[assets['Location'] == location]
    r = pump['PumpName'].unique().tolist()
    return [{'label': i, 'value': i} for i in r]


@app.callback(
    Output('powerON', 'on'),
    Output('flow-rate', 'value'),
    Input('site-1', 'value'),
    Input('pump-1', 'value'),
)
def getStatus(site, pump):
    if site is not None and pump is not None:
        df = db.getData("PoC_SP_Metrics", "RecordID")
        df = df[(df['site'] == site) & (df['pumpID'] == pump)].head(1)
        print(df)
        speed = float(df['208'].tolist()[0]) / 10000
        on = int(df['104'].tolist()[0])
        print(on, speed)
        if on == 0:
            p = True
        elif on == 1:
            p = False
        return p, speed
    else:
        return False, 0


@app.callback(
    Output('powerON', 'color'),
    Input('powerON', 'on'),
    Input('site-1', 'value'),
    Input('pump-1', 'value')
)
def powerON(n, site, pump):
    if site is not None and pump is not None:
        ctrl.powerPump(site, pump, n)
    if n:
        color = '#63ff5e'
    if not n:
        color = '#e6110e'
    return color


@app.callback(
    Output('flow-rate-monitor', 'value'),
    Input('flow-rate', 'value'),
    Input('site-1', 'value'),
    Input('pump-1', 'value')
)
def update_output(value, site, pump, ):
    if site is not None and pump is not None:
        ctrl.pumpSpeed(site, pump, value)
    return [str(value)]


app.layout = html.Div(
    style={'background': 'white', 'width': '100%', 'height': '100%'},
    id="big-app-container",
    children=[
        build_banner(),
        dcc.Interval(
            id="interval-component",
            interval=1 * 1000,  # in milliseconds
            n_intervals=0,
            disabled=False,
        ),
        home()
    ]
)


@app.callback(
    output=[
        Output("big-app-container", "children"),
    ],
    inputs=[
        Input("home", "n_clicks"),
        Input("assets", "n_clicks"),
        Input("log", "n_clicks"),
        Input("controls", "n_clicks"),
    ],
)
def getPages(h, a, l, c):
    if h > 0:
        return [[build_banner(),
                 dcc.Interval(
                     id="interval-component",
                     interval=1 * 1000,  # in milliseconds
                     n_intervals=0,
                     disabled=False,
                 ),
                 home()]]
    elif l > 0:
        return [[build_banner(),
                 history()]]
    elif c > 0:
        return [[build_banner(),
                 dcc.Interval(
                     id="interval-component",
                     interval=1 * 1000,  # in milliseconds
                     n_intervals=0,
                     disabled=False,
                 ),
                 control()]]


if __name__ == "__main__":
    app.run(debug=True)
