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

####### Assets #####
assets = db.getData("PoC_SP_CustomerData", "AccountId")
m = []
for ac in assets.Account.unique():
    sites = assets[assets['Account'] == ac].Plant.unique().tolist()
    pumps = assets[assets['Account'] == ac].Pump.unique().tolist()
    m.append({
        'Account': ac,
        'Sites': len(sites),
        'Pumps': len(pumps)
    })
summary = pd.DataFrame.from_dict(m)

Alarms = db.getData("PoC_SP_Alarm", "Event_code")
Codes = Alarms['Event_code'].tolist()
Al = Alarms['Event_description'].tolist()
AlarmDict = {}
for i in range(len(Codes)):
    AlarmDict.update({Codes[i]: Al[i]})

####### Users #####
users = {
    'mmuthumani@buckman.com': 'pass@123',
    'ramachandran@buckman.com': 'password',
    'mscatolin@buckman.com': 'password123'
}
####### Users #####

####### LogData #####
logs = []
speed_change = []
submit_counter = []


####### LogData #####

####### Generic Functions #####
def genTextCard(id, title, text, text2, color2, color1='black', width="10rem"):
    return dbc.Card(
        dbc.CardBody(
            id=id,
            children=[
                html.H4(title, className="card-title"),
                html.P(
                    html.H5(text, style={'color': color1}),
                    className="card-text",
                ),
                html.P(
                    html.H5(text2, style={'color': color2}),
                    className="card-text",
                )
            ]
        ),
        style={"width": width, 'display': 'inline-block'},
    )


def genPumpStatus(site, pump):
    status = db.getPowerStatus(site, pump)
    speed, time = db.getSpeedTime(site, pump)
    alarm = db.getAlarmStatus(site, pump)
    description = AlarmDict[alarm]
    if speed is None:
        speed = 0
    if time is None:
        time = datetime.now().time()
    if status is None:
        color = 'red'
        text = 'Disabled'
    elif status == 0:
        color = 'green'
        text = 'Running'
    elif status == 1:
        color = 'red'
        text = 'OFF!'
    if alarm == 0:
        color1 = 'green'
    else:
        color1 = 'red'
    return dbc.Card(
        dbc.CardBody(
            id=pump,
            children=[
                html.H6(pump, className="card-title"),
                daq.Indicator(
                    label=text,
                    color=color,
                    labelPosition='right'
                ),
                html.P(
                    html.H6(f'flow = {speed} l/h', style={'color': 'blue'}),
                    className="card-text",
                ),
                html.P(
                    html.H6(f'Alarm = {alarm}', style={'color': color1}),
                    className="card-text",
                ),
                dbc.CardFooter(f"Updated {time}")
            ]
        ),
        style={"width": "10rem", 'display': 'inline-block'},
    )


def genTable(id, df):
    return dash_table.DataTable(
        id=id,
        data=df.to_dict('records'),
        columns=[{"name": i, "id": i} for i in df.columns],
        style_cell={'textAlign': 'center'},
        filter_action="native",
        sort_action="native",
        sort_mode="multi",
        page_size=5
    )


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


#### Main Display ###
def home():
    return html.Div(
        style={'textAlign': 'center'},
        children=[
            html.Div(id='Headers',
                     children=[
                         html.Div(
                             style={'marginTop': 5, 'marginBottom': 0, 'marginRight': 5,
                                    'font-size': 12,
                                    'color': 'black',
                                    'width': '45%',
                                    'display': 'inline-block'},
                             children=[
                                 html.H2("Customer Data",
                                         style={'marginLeft': 10}), ]
                         ),
                         html.Div(
                             style={'marginTop': 5, 'marginBottom': 0, 'marginRight': 5,
                                    'font-size': 12,
                                    'color': 'black',
                                    'width': '45%',
                                    'display': 'inline-block'},
                             children=[
                                 html.H2("At A Glance",
                                         style={'marginLeft': 10}), ]
                         )
                     ]),
            html.Div(
                id='body-left',
                style={'marginTop': 5, 'marginBottom': 0, 'marginRight': 5,
                       'font-size': 12,
                       'color': 'black',
                       'width': '45%',
                       'display': 'inline-block'},
                children=[
                    html.H6('Select a customer'),
                    dash_table.DataTable(
                        id='customer-sum',
                        data=summary.to_dict('records'),
                        columns=[{"name": i, "id": i} for i in summary.columns],
                        style_cell={'textAlign': 'center'},
                        filter_action="native",
                        sort_action="native",
                        sort_mode="multi",
                        page_size=5
                    ),
                    html.Div(id='customer-expansion',
                             children=[
                                 html.H3("Site Information",
                                         style={'marginLeft': 10, 'marginTop': 10}),
                                 dash_table.DataTable(
                                     id='site-data',
                                     style_cell={'textAlign': 'center'},
                                     filter_action="native",
                                     sort_action="native",
                                     sort_mode="multi"
                                 )
                             ]),
                    html.Div(id='site-profit')
                ]
            ),
            html.Div(
                id='body-right',
                style={'marginTop': 0, 'marginBottom': 0, 'marginRight': 0,
                       'font-size': 12,
                       'color': 'black',
                       'width': '45%',
                       'display': 'inline-block',
                       'verticalAlign': 'top'
                       },
            ),
        ]
    )


@app.callback(
    Output('site-data', 'data'),
    Output('site-data', 'columns'),
    Input('customer-sum', 'active_cell')
)
def updateSiteData(active):
    if active['column_id'] == 'Account':
        df = assets[['Account', 'Plant', 'Pump']].groupby(['Account', 'Plant']).count().reset_index()
        row = active['row']
        customer = summary['Account'].tolist()[row]
        df = df[df['Account'] == customer][['Plant', 'Pump']]
        data = df.to_dict('records')
        columns = [{"name": i, "id": i} for i in df.columns]
        return data, columns


@app.callback(
    Output('site-profit', 'children'),
    Input('customer-sum', 'active_cell'),
    Input('site-data', 'active_cell')
)
def updatePlantwise(c, s):
    if s['column_id'] == 'Plant':
        filtered = assets[['Account', 'Plant', 'Pump']].groupby(['Account', 'Plant']).count().reset_index()
        customer = summary['Account'].tolist()[c['row']]
        plants = filtered[filtered['Account'] == customer]
        plant = plants['Plant'].tolist()[s['row']]
        costs = db.getData('PoC_SP_Targets', 'ChemA_target')
        chemicals = [c for c in assets.columns.tolist() if 'chem' in c.lower()]
        if s is not None and c is not None:
            # print(customer)
            df = assets[['Plant', 'ChemD', 'ChemE', 'ChemB', 'ChemA', 'ChemC']].groupby(['Plant']).sum().reset_index()
            df = df[df['Plant'] == plant]
            # print(df)
            cost = costs.groupby(['Plant']).sum().reset_index()
            cost = cost[cost['Plant'] == plant]
            # print(cost)
            children = [
                html.H3("Planned vs Actual Chemical Expenditure",
                        style={'marginLeft': 10, 'marginTop': 10})
            ]
            for c in chemicals:
                plan_list = list(cost[[i for i in cost.columns.tolist() if c.lower() in i.lower()]].iloc[0])
                # print(plan_list)
                planned = plan_list[0] * plan_list[1]
                actual = df[c].tolist()[0] * plan_list[1]
                if planned >= actual:
                    color = 'green'
                else:
                    color = 'red'
                if planned < 1000:
                    text1 = '$' + str(planned)
                else:
                    text1 = '$' + str(round(planned / 1000, 2)) + 'k'
                if actual < 1000:
                    text2 = '$' + str(actual)
                else:
                    text2 = '$' + str(round(actual / 1000, 2)) + 'k'
                card = genTextCard(c, c, text1, text2, color)
                children.append(card)
        else:
            children = [None]
    return children


@app.callback(
    Output('body-right', 'children'),
    Input('customer-sum', 'active_cell'),
    Input('site-data', 'active_cell')
)
def updateCosts(c, s):
    if c['column_id'] == 'Account':
        customer = summary['Account'].tolist()[c['row']]
        costs = db.getData('PoC_SP_Targets', 'ChemA_target')
        # print(costs)
        chemicals = [c for c in assets.columns.tolist() if 'chem' in c.lower()]
        if c is not None and s is None:
            # print(customer)
            df = assets[['Account', 'ChemD', 'ChemE', 'ChemB', 'ChemA', 'ChemC']].groupby(
                ['Account']).sum().reset_index()
            df = df[df['Account'] == customer]
            # print(df)
            cost = costs.groupby(['Account']).sum().reset_index()
            cost = cost[cost['Account'] == customer]
            # print(cost)
            children = [
                html.H3("Planned vs Actual Chemical Expenditure")
            ]
            for c in chemicals:
                plan_list = list(cost[[i for i in cost.columns.tolist() if c.lower() in i.lower()]].iloc[0])
                # print(plan_list)
                planned = plan_list[0] * plan_list[1]
                actual = df[c].tolist()[0] * plan_list[1]
                if planned >= actual:
                    color = 'green'
                else:
                    color = 'red'
                if planned < 1000:
                    text1 = '$' + str(planned)
                else:
                    text1 = '$' + str(round(planned / 1000, 2)) + 'k'
                if actual < 1000:
                    text2 = '$' + str(actual)
                else:
                    text2 = '$' + str(round(actual / 1000, 2)) + 'k'
                card = genTextCard(c, c, text1, text2, color)
                children.append(card)
        elif c is not None and s is not None:
            df = assets[['Account', 'Plant', 'Pump']].groupby(['Account', 'Plant']).count().reset_index()
            filtered = assets[['Account', 'Plant', 'Pump']]
            if s['column_id'] == 'Plant':
                site = list(df[df['Account'] == customer]['Plant'])[s['row']]
                plantPumps = filtered[(filtered['Account'] == customer) & (filtered['Plant'] == site)]
                # print(plantPumps)
                children = [html.H3("Pump Status")]
                for pump in plantPumps['Pump'].tolist():
                    # print(genPumpStatus(site, pump))
                    children.append(genPumpStatus(site, pump))
        return children


def control():
    return html.Div(
        [
            html.Div(
                children=[
                    html.Div(
                        children=[
                            dcc.Dropdown(
                                id='customer-select',
                                options=assets['Account'].unique(),
                                placeholder='Select a customer',
                                searchable=True,
                                style={'height': 15},
                            )
                        ],
                        style={'marginTop': 0, 'marginBottom': 10,
                               'font-size': 18,
                               'color': 'black',
                               'width': '25%',
                               'display': 'inline-block'}
                    ),
                    html.Div(
                        children=[
                            dcc.Dropdown(
                                id='site-select',
                                placeholder='Select a site',
                                searchable=True,
                                style={'height': 15},
                            )
                        ],
                        style={'marginTop': 0, 'marginBottom': 10,
                               'font-size': 18,
                               'color': 'black',
                               'width': '25%',
                               'display': 'inline-block'}
                    ),
                    html.H4("Pump Controls",
                            style={'width': '45%', 'display': 'inline-block',
                                   'marginLeft': 20, 'textAlign': 'center'})
                ]
            ),
            html.Div(
                id='controlBody',
                style={'textAlign': 'center'},
                children=[
                    html.Div(
                        id='asset-table',
                        style={'width': '40%', 'marginTop': 15, 'marginLeft': 5, 'display': 'inline-block',
                               'verticalAlign': 'top'}
                    ),
                    html.Div(
                        id='pump-controls',
                        style={'width': '45%', 'marginTop': 15, 'marginLeft': 20, 'display': 'inline-block',
                               'verticalAlign': 'top', 'textAlign': 'right'},
                        children=[
                            html.Div(
                                id='pump-identifier',
                                style={'textAlign': 'center'}
                            ),
                            html.Div(
                                [
                                    html.H6("Pump Power:"),
                                    daq.PowerButton(
                                        id='powerON'
                                    )
                                ],
                                style={'marginTop': 15, 'textAlign': 'center'}
                            ),
                            html.Div(
                                [
                                    html.H6("Flow Rate (l/h) "),
                                    html.Div
                                        (
                                        [
                                            html.Div(style={'marginTop': 25, 'textAlign': 'center', 'width': "33.33%",
                                                            'display': 'inline-block'}),
                                            html.Div(
                                                [
                                                    dbc.Input(
                                                        id='flow-value',
                                                        type='number',
                                                        min=0.01,
                                                        max=30,
                                                        step=0.01,
                                                        placeholder='Enter Flow Rate Change in l/h',
                                                        persistence=True,
                                                        style={'marginBottom': 5, 'textAlign': 'center'}
                                                    ),
                                                    dbc.Button("submit", id="submit-flow", n_clicks=0),
                                                ],
                                                style={'marginTop': 25, 'textAlign': 'center', 'width': "33.33%",
                                                       'display': 'inline-block'}
                                            ),
                                            html.Div(style={'marginTop': 25, 'textAlign': 'center', 'width': "33.33%",
                                                            'display': 'inline-block'}),
                                        ]
                                    ),
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
                            ),
                            html.Div(
                                id="alarms",
                                style={'marginTop': 25, 'textAlign': 'center', 'width': "100%"}
                            ),
                            html.Div(id='dummy')  # dummy for tests
                        ]
                    )
                ]
            )
        ]
    )


@app.callback(
    Output('site-select', 'options'),
    Input('customer-select', 'value'),
)
def getsites(location):
    sites = assets[assets['Account'] == location]
    r = sites['Plant'].unique().tolist()
    return [{'label': i, 'value': i} for i in r]


@app.callback(
    Output('asset-table', 'children'),
    Input('site-select', 'value'),
)
def updateSitePumps(plant):
    if plant:
        pumps = assets[assets['Plant'] == plant]['Pump'].tolist()
        # print(pumps)
        data = pd.DataFrame()
        data['Pump'] = pumps
        pumpStatus = []
        pumpSpeed = []
        lastUpdate = []
        for p in pumps:
            status = db.getPowerStatus(plant, p)
            # print(status)
            speed, time = db.getSpeedTime(plant, p)
            # print(speed, time)
            if speed is None:
                speed = 0
            if time is None:
                time = datetime.now().time()
            if status is None:
                text = 'Disabled'
            elif status == 0:
                text = 'Running'
            elif status == 1:
                text = 'OFF'
            pumpStatus.append(text)
            pumpSpeed.append(speed)
            lastUpdate.append(time)
        data['Status'] = pumpStatus
        data['FlowRate'] = pumpSpeed
        data['Last Updated'] = lastUpdate
        return genTable('pumps', data)


@app.callback(
    Output('pump-identifier', 'children'),
    Input('site-select', 'value'),
    Input('pumps', 'active_cell')
)
def dispPumpname(plant, pump):
    if plant:
        pumps = assets[assets['Plant'] == plant]['Pump'].tolist()
        if pump['column_id'] == 'Pump':
            pumpName = pumps[pump['row']]
            name = html.H3(pumpName)
        else:
            name = html.H3('Select Pump')
    else:
        name = html.H3('Select Plant')
    return name


@app.callback(
    Output('powerON', 'on'),
    Input('site-select', 'value'),
    Input('pumps', 'active_cell')
)
def powerStatus(site, cell):
    if site is not None:
        pumps = assets[assets['Plant'] == site]['Pump'].tolist()
        pump = pumps[cell['row']]
        power = db.getPowerStatus(site, pump)
        if power == 1:
            status = False
        elif power == 0:
            status = True
        elif power is None:
            status = False
    else:
        status = False
    return status


@app.callback(
    Output('powerON', 'color'),
    Input('powerON', 'on'),
    Input('customer-select', 'value'),
    Input('site-select', 'value'),
    Input('pumps', 'active_cell')
)
def powerON(n, customer, site, cell):
    pumps = assets[assets['Plant'] == site]['Pump'].tolist()
    pump = pumps[cell['row']]
    record = db.getRecordID('PoC_SP_Change')
    if record is None:
        record = 0
    else:
        record = record
    user = logs[-1]['User']
    speed, last = db.getSpeedTime(site, pump)
    if speed is None:
        speed = 0
    if site is not None and pump is not None:
        ctrl.powerPump(customer, site, pump, n)
        metrics = {
            'RecordID': record + 1,
            'UserName': user,
            'Site': site,
            'Pump': pump,
            'Power': str(n),
            'Speed': speed,
            'Timestamp': str(datetime.now())
        }
        db.writeValues(metrics, "PoC_SP_Change")
    if n:
        color = '#63ff5e'
    if not n:
        color = '#e6110e'
    return color


@app.callback(
    Output('flow-value', 'value'),
    Input('site-select', 'value'),
    Input('pumps', 'active_cell')
)
def getPumpSpeed(site, cell):
    pumps = assets[assets['Plant'] == site]['Pump'].tolist()
    pump = pumps[cell['row']]
    if site is not None and pump is not None:
        s, t = db.getSpeedTime(site, pump)
        return s
    else:
        return 0.1


# @app.callback(
#     Output('flow-rate-monitor', 'value'),
#     Input('flow-value', 'value'),
#     Input('submit-flow', 'n_clicks'),
# )
# def update_val(entry, submit):
#     if entry is not None and submit > 0:
#         return str(entry)
#     else:
#         return str(0)


@app.callback(
    Output('flow-rate-monitor', 'value'),
    Input('powerON', 'on'),
    Input('flow-value', 'value'),
    Input('customer-select', 'value'),
    Input('site-select', 'value'),
    Input('pumps', 'active_cell'),
    Input('submit-flow', 'n_clicks')
)
def update_output(on, value, customer, site, cell, submit):
    # print(submit, len(k))
    pumps = assets[assets['Plant'] == site]['Pump'].tolist()
    pump = pumps[cell['row']]
    record = db.getRecordID('PoC_SP_Change')
    if record is None:
        record = 0
    else:
        record = record
    user = logs[-1]['User']
    if on and site is not None and pump is not None and submit > len(submit_counter):
        submit_counter.append(submit)
        # print(k)
        ctrl.pumpSpeed(customer, site, pump, value)
        metrics = {
            'RecordID': record + 1,
            'UserName': user,
            'Site': site,
            'Pump': pump,
            'Power': str(on),
            'Speed': value,
            'Timestamp': str(datetime.now())
        }
        db.writeValues(metrics, "PoC_SP_Change")
    return [str(value)]


@app.callback(
    Output('alarms', 'children'),
    Input('site-select', 'value'),
    Input('pumps', 'active_cell'),
    Input("interval-component", "n_intervals")
)
def getAlarms(site, cell, interval):
    pumps = assets[assets['Plant'] == site]['Pump'].tolist()
    pump = pumps[cell['row']]
    if interval < 2000000:
        alarm = db.getAlarmStatus(site, pump)
        description = AlarmDict[alarm]
        card = genTextCard('Alarm', "Current Alarm", str(alarm), description, 'red', width="25rem")
        return card


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
    # print(len(logs))
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
        # Input("assets", "n_clicks"),
        Input("log", "n_clicks"),
        Input("controls", "n_clicks"),
    ],
)
def getPages(h, l, c):
    if h > 0:
        return [[build_banner(),
                 dcc.Interval(
                     id="interval-component",
                     interval=1 * 3000,  # in milliseconds
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
                     interval=1 * 3000,  # in milliseconds
                     n_intervals=0,
                     disabled=False,
                 ),
                 control()]]


if __name__ == "__main__":
    app.run(debug=True)
