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

####### Users #####
users = {
    'mmuthumani@buckman.com': 'pass@123',
    'ramachandran@buckman.com': 'password',
    'mscatolin@buckman.com': 'password123'
}
####### Users #####

####### LogData #####
logs = []


####### LogData #####

####### Generic Functions #####
def genTextCard(id, title, text,text2, color2, color1='black'):
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
        style={"width": "10rem", 'display': 'inline-block'},
    )


def genPumpStatus(site, pump):
    status = db.getPowerStatus(site, pump)
    speed, time = db.getSpeedTime(site, pump)
    if status is None:
        color = 'red'
        text = 'Disabled'
    elif status == 0:
        color = 'green'
        text = 'Running'
    elif status == 1:
        color = 'red'
        text = 'OFF!'
    return dbc.Card(
        dbc.CardBody(
            id=id,
            children=[
                html.H4(pump, className="card-title"),
                daq.Indicator(
                    label=text,
                    color=color,
                    labelPosition='right'
                ),
                html.P(
                    html.H5(f'flow = {speed}l/h', style={'color': 'black'}),
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
        sort_mode="multi"
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
                                         style={'marginLeft': 10}),]
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
                    html.Div(id='customer-expansion'),
                    html.Div(id='site-profit')
                ]
            ),
            html.Div(
                id='body-right',
                style={'marginTop': 5, 'marginBottom': 0, 'marginRight': 5,
                       'font-size': 12,
                       'color': 'black',
                       'width': '45%',
                       'display': 'inline-block'},
            ),
        ]
    )


@app.callback(
    Output('customer-expansion', 'children'),
    Input('customer-sum', 'active_cell')
)
def updateSiteData(active):
    if active['column_id'] == 'Account':
        df = assets[['Account', 'Plant', 'Pump']].groupby(['Account', 'Plant']).count().reset_index()
        row = active['row']
        customer = summary['Account'].tolist()[row]
        df = df[df['Account'] == customer][['Plant', 'Pump']]
        children = [
            html.H3("Site Information",
                    style={'marginLeft': 10, 'marginTop':10}),
            genTable('site-data', df)
        ]
        return children


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
                        style={'marginLeft': 10, 'marginTop':10})
            ]
            for c in chemicals:
                plan_list = list(cost[[i for i in cost.columns.tolist() if c.lower() in i.lower()]].iloc[0])
                # print(plan_list)
                planned = plan_list[0]*plan_list[1]
                actual = df[c].tolist()[0]*plan_list[1]
                if planned >= actual:
                    color = 'green'
                else:
                    color = 'red'
                if planned < 1000:
                    text1 = '$'+str(planned)
                else:
                    text1 = '$' + str(round(planned/1000, 2))+'k'
                if actual < 1000:
                    text2 = '$'+str(actual)
                else:
                    text2 = '$' + str(round(actual / 1000, 2)) + 'k'
                card = genTextCard(c,c,text1,text2, color)
                children.append(card)
        else:
            children=[None]
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
            df = assets[['Account', 'ChemD', 'ChemE', 'ChemB', 'ChemA', 'ChemC']].groupby(['Account']).sum().reset_index()
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
                planned = plan_list[0]*plan_list[1]
                actual = df[c].tolist()[0]*plan_list[1]
                if planned >= actual:
                    color = 'green'
                else:
                    color = 'red'
                if planned < 1000:
                    text1 = '$'+str(planned)
                else:
                    text1 = '$' + str(round(planned/1000, 2))+'k'
                if actual < 1000:
                    text2 = '$'+str(actual)
                else:
                    text2 = '$' + str(round(actual / 1000, 2)) + 'k'
                card = genTextCard(c, c, text1, text2, color)
                children.append(card)
        elif c is not None and s is not None:
            filtered = assets[['Account', 'Plant', 'Pump']].groupby(['Account', 'Plant']).count().reset_index()
        return children


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

if __name__ == "__main__":
    app.run(debug=True)
