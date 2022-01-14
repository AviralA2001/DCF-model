import requests
from bs4 import BeautifulSoup as bs
import html5lib
import re
import statistics
import pandas as pd
import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc




def calc_values(name, coc, roce_post, growth_high, t_growth, f_period, h_period):
    intrinsic_pe = 0
    url = "https://www.screener.in/company/" + name + "/"
    print(url)
    x = requests.get(url)
    soup = bs(x.text, "html.parser")
    p_f = soup.find_all('li', class_="flex flex-space-between")
    for i in p_f:
        if (i.text.find('Stock P/E') != -1):
            stock_pe = float(i.text.replace("Stock P/E", "").strip())
        elif (i.text.find('Market Cap') != -1):
            market_cap = float(
                i.text.replace("Market Cap", "").replace("\n", "").replace("Cr.", "").replace("₹", "").replace(",",
                                                                                                               "").strip())

    n_p = soup.find_all('section', id="profit-loss")
    for j in n_p:
        net_sales = j.find('tr', class_="stripe").text.replace(',', "").split()
        net_sales_c = float(net_sales[-2])
        net_sales_3 = (pow((net_sales_c / float(net_sales[-5])), (1 / 3)) - 1) * 100
        net_sales_5 = (pow((net_sales_c / float(net_sales[-7])), (1 / 5)) - 1) * 100
        net_sales_10 = (pow((net_sales_c / float(net_sales[-12])), (1 / 10)) - 1) * 100
        k = j.find_all('tr', class_="strong")
        for l in k:
            if (l.text.find('Net Profit') != -1):
                net_profit = float(l.text.split()[-2].replace(',', ''))
                net_profit_3 = (pow((net_profit / float(l.text.split()[-5].replace(',', ''))), (1 / 3)) - 1) * 100
                net_profit_5 = (pow((net_profit / float(l.text.split()[-7].replace(',', ''))), (1 / 5)) - 1) * 100
                net_profit_10 = (pow((net_profit / float(l.text.split()[-12].replace(',', ''))), (1 / 10)) - 1) * 100
            if (l.text.find('Operating Profit') != -1):
                opr_profit = float(l.text.split()[-2].replace(',', ''))

    print(opr_profit)

    fy20_pe = market_cap / net_profit

    f_r = soup.find_all('section', id="ratios")
    for m in f_r:
        n = m.find_all('tr')
        for o in n:
            if o.text.find("ROCE %") != -1:
                roce_list = o.text.replace("%", "").split()[8:13]
    for p in roce_list:
        p = float(p)
    roce = statistics.median(roce_list)

    cagr = soup.find_all('section', id="quarters")
    for q in cagr:
        net_sales_q = q.find('tr', class_="stripe").text.replace(",", "").split()
        net_sales_q1 = float(net_sales_q[-1]) + float(net_sales_q[-2]) + float(net_sales_q[-3]) + float(net_sales_q[-4])
        net_sales_q2 = float(net_sales_q[-5]) + float(net_sales_q[-6]) + float(net_sales_q[-7]) + float(net_sales_q[-8])
        cagr_sales = ((net_sales_q1 / net_sales_q2) - 1) * 100
        r = q.find_all('tr', class_="strong")
        for s in r:
            if (s.text.find('Net Profit') != -1):
                net_profit_q = s.text.replace(",", "").split()
                net_profit_q1 = float(net_profit_q[-1]) + float(net_profit_q[-2]) + float(net_profit_q[-3]) + float(
                    net_profit_q[-4])
                net_profit_q2 = float(net_profit_q[-5]) + float(net_profit_q[-6]) + float(net_profit_q[-7]) + float(
                    net_profit_q[-8])
                cagr_profit = ((net_profit_q1 / net_profit_q2) - 1) * 100

    s_a = soup.find_all('section', id="balance-sheet")
    for j in s_a:
        if j.text.find("Total Assets") != -1:
            capital = float(j.text.split()[-2].replace(',', ''))
        net_sales = j.find('tr', class_="stripe").text.replace(',', "").split()

    cagr_sales_list = ["Sales Growth", net_sales_10, net_sales_5, net_sales_3, cagr_sales]
    cagr_profit_list = ["Profit Growth", net_profit_10, net_profit_5, net_profit_3, cagr_profit]
    cagr_info = ['', '10 Years', '5 Years', '3 Years', 'TTM']
    df_cagr = pd.DataFrame([cagr_sales_list, cagr_profit_list], columns=cagr_info)

    info = ['earnings growth rate', 'nopat', 'capital employed', 'investment', 'fcf', 'discount factor', 'discount fcf']
    tax_rate = 25

    total = f_period + h_period
    gr_decline = (growth_high - t_growth) / f_period
    ri_rate_1 = 40
    ri_rate_2 = 10

    nopat = opr_profit * (1 - (tax_rate / 100))
    print(nopat)
    inv = nopat * (ri_rate_1 / 100)
    fcf = nopat - inv
    dis_fac = 1
    dic_fcf = dis_fac * fcf

    info_1 = ['', nopat, capital, inv, fcf, dis_fac, dic_fcf]
    index = range(0, f_period + h_period + 1)
    db = pd.DataFrame([info_1], columns=info, index=index)
    for i in range(1, h_period + 1):
        db.loc[i, 'earnings growth rate'] = growth_high
        db.loc[i, 'nopat'] = db.loc[i - 1, 'nopat'] * (1 + (db.loc[i, 'earnings growth rate'] / 100))
        db.loc[i, 'investment'] = db.loc[i, 'nopat'] * (ri_rate_1 / 100)
        db.loc[i, 'capital employed'] = db.loc[i - 1, 'capital employed'] + db.loc[i - 1, 'investment']
        db.loc[i, 'fcf'] = db.loc[i, 'nopat'] - db.loc[i, 'investment']
        db.loc[i, 'discount factor'] = 1 / pow(1 + (coc / 100), i)
        db.loc[i, 'discount fcf'] = db.loc[i, 'discount factor'] * db.loc[i, 'fcf']

    for i in range(h_period + 1, total + 1):
        db.loc[i, 'earnings growth rate'] = growth_high - gr_decline * (i - h_period)
        db.loc[i, 'nopat'] = db.loc[i - 1, 'nopat'] * (1 + (db.loc[i, 'earnings growth rate'] / 100))
        db.loc[i, 'investment'] = (db.loc[i, 'earnings growth rate'] * db.loc[i, 'nopat']) / ((roce_post))
        db.loc[i, 'capital employed'] = db.loc[i - 1, 'capital employed'] + db.loc[i - 1, 'investment']
        db.loc[i, 'fcf'] = db.loc[i, 'nopat'] - db.loc[i, 'investment']
        db.loc[i, 'discount factor'] = 1 / pow(1 + (coc / 100), i)
        db.loc[i, 'discount fcf'] = db.loc[i, 'discount factor'] * db.loc[i, 'fcf']

    terminal_nopat = db.loc[total, 'nopat'] * (1 + (t_growth / 100)) / ((coc - t_growth) / 100)
    terminal_investment = ((t_growth / 100) * terminal_nopat) / ((roce_post / 100))
    terminal_fcf = terminal_nopat - terminal_investment
    terminal_df = db.loc[total, 'discount factor']
    terminal_dfcf = terminal_fcf * terminal_df
    db.loc[total + 1] = [t_growth, terminal_nopat, "", terminal_investment, terminal_fcf, terminal_df, terminal_dfcf]
    print(db)
    intrinsic_value = sum(db['discount fcf'])
    intrinsic_pe = intrinsic_value / db.loc[0, 'nopat']
    print(intrinsic_value)  # /db.loc[0,'nopat'])
    print(intrinsic_pe)
    overvaluation = (stock_pe / intrinsic_pe) - 1
    overvaluation = overvaluation * 100
    return (name, stock_pe, fy20_pe, roce, intrinsic_pe, overvaluation, df_cagr)

roce_post = 50
coc = 13
growth_high = 20
t_growth = 5
f_period = 15
h_period = 10
name = "NESTLEIND"

roc_dict = {}
for i in range(10, 101, 5):
    if i % 10 == 0:
        roc_dict[i] = str(i)
    else:
        roc_dict[i] = ""

coc_dict = {}
for i in range(80, 170, 5):
    if i % 10 == 0:
        coc_dict[int(i / 10)] = str(int(i / 10))
    else:
        coc_dict[(i / 10)] = ""

growth_high_dict = {}
for i in range(8, 20, 1):
    if i % 2 == 0:
        growth_high_dict[i] = str(i)
    else:
        growth_high_dict[i] = ""

h_period_dict = {}
for i in range(10, 25, 1):
    if i % 2 == 0 or i == 25:
        h_period_dict[i] = str(i)
    #     elif i ==25:
    #         h_period_dict[i] = str(i)
    else:
        h_period_dict[i] = ""

f_period_dict = {}
for i in range(5, 20, 5):
    f_period_dict[i] = str(i)

t_growth_dict = {}
for i in range(0, 75, 5):
    if i % 10 == 0 or i == 75:
        t_growth_dict[int(i / 10)] = str(int(i / 10))
    else:
        t_growth_dict[(i / 10)] = ""

app = dash.Dash(__name__)
server = app.server

app.layout = dbc.Container([

    html.H1("Valuing consistent compounders!", style={'text-align': 'left'}),

    html.P("Hi there!", style={'text-align': 'left'}),
    html.P("This page will help you calculate intrinsic PE of consistent compounders through growth-RoCE DCF model.",
           style={'text-align': 'left'}),
    html.P(" \n We then compare this with current PE of the stock to calculate degree of overvaluation.",
           style={'text-align': 'left'}),

    dbc.CardGroup([
        dbc.Card(
            dbc.CardBody([
                html.P("First let's look at some past data on growth/RoCE to help you with your inputs:",
                       style={'font-family:courier': 'left'}),
                html.Div(id='output_container_symbol', children=[]),
                html.Br(),
                html.Div(id='output_container_st_pe', children=[]),
                html.Br(),
                html.Div(id='output_container_fy_20', children=[]),
                html.Br(),
                html.Div(id='output_container_roce', children=[]),
                html.Br(),
                html.P("Here are the past growth rates:", style={'font-family:courier': 'left'}),
                html.Div(id='output_container_cagr_1', children=[]),
                html.Br(),
                html.Div(id='output_container_cagr_2', children=[]),
                html.Br(),
                html.Div(id='output_container_cagr_3', children=[]),
                html.Br(),

                # dash_table.DataTable(
                #     id='loading-states-table', children=[],
                #     columns=[{
                #         "name": i, "id": i,
                #         'editable': True,
                #         'renamable': True,
                #         'column_editable': True,
                #     } for i in df_cagr.columns],
                #     data=df_cagr.to_dict('records'),
                #     editable=True
                # ),

                html.H4("Now play with inputs to see changes in intrinsic PE and overvaluation:",
                        style={'text-align': 'left'}),
                html.Div(id='output_container_in_pe', children=[]),
                html.Br(),
                html.Div(id='output_container_ov', children=[]),
                html.Br(),
            ]
            )
        ),
        dbc.Card(
            dbc.CardBody([
                html.Div([
                    "Input: ",
                    dcc.Input(id='url_link', value=name, type='text')
                ]),

                html.Div([
                    html.Div([html.Label('Cost of Capital(CoC) %')], id='my-div' + str(id),
                             style={'textAlign': 'center'}),
                    dcc.Slider(
                        id='coc',
                        min=8,
                        max=16,
                        step=0.5,
                        value=coc,
                        marks=coc_dict,
                        tooltip={"placement": "top", "always_visible": True},
                    ),

                ]),

                html.Div([
                    html.Div([html.Label('Return on capital employed (RoCE): %')], id='my-div-roce' + str(id),
                             style={'textAlign': 'center'}),
                    dcc.Slider(
                        id='roce',
                        min=10,
                        max=100,
                        step=5,
                        value=roce_post,
                        marks=roc_dict,
                        tooltip={"placement": "top", "always_visible": True},
                    ),

                ]),

                html.Div([
                    html.Div([html.Label('Growth during high growth period: %')], id='my-div-growth-high' + str(id),
                             style={'textAlign': 'center'}),
                    dcc.Slider(
                        id='growth_high',
                        min=8,
                        max=20,
                        step=2,
                        value=growth_high,
                        marks=growth_high_dict,
                        tooltip={"placement": "top", "always_visible": True},
                    ),

                ]),

                html.Div([
                    html.Div([html.Label('High growth period (years):')], id='my-div-h-period' + str(id),
                             style={'textAlign': 'center'}),
                    dcc.Slider(
                        id='h_period',
                        min=10,
                        max=25,
                        step=2,
                        value=h_period,
                        marks=h_period_dict,
                        tooltip={"placement": "top", "always_visible": True},
                    ),
                ]),

                html.Div([
                    html.Div([html.Label('Fade period (years):')], id='my-div-f-period' + str(id),
                             style={'textAlign': 'center'}),
                    dcc.Slider(
                        id='f_period',
                        min=5,
                        max=25,
                        step=5,
                        value=f_period,
                        marks=f_period_dict,
                        tooltip={"placement": "top", "always_visible": True},
                    ),
                ]),

                html.Div([
                    html.Div([html.Label('Terminal growth rate: %')], id='my-div-t-growth' + str(id),
                             style={'textAlign': 'center'}),
                    dcc.Slider(
                        id='t_growth',
                        min=0,
                        max=7.5,
                        step=0.5,
                        value=t_growth,
                        marks=t_growth_dict,
                        tooltip={"placement": "top", "always_visible": True},
                    ),
                ]),
            ],
            ),
            outline=True,
            style={"width": "30rem"},
        )
    ]
    )
]
)


@app.callback(
    [Output(component_id='output_container_symbol', component_property='children'),
     Output(component_id='output_container_st_pe', component_property='children'),
     Output(component_id='output_container_fy_20', component_property='children'),
     Output(component_id='output_container_roce', component_property='children'),
     Output(component_id='output_container_in_pe', component_property='children'),
     Output(component_id='output_container_ov', component_property='children'),
     Output(component_id='output_container_cagr_1', component_property='children'),
     Output(component_id='output_container_cagr_2', component_property='children'),
     Output(component_id='output_container_cagr_3', component_property='children'),],
    [Input(component_id='coc', component_property='value'),
     Input(component_id='roce', component_property='value'),
     Input(component_id='growth_high', component_property='value'),
     Input(component_id='h_period', component_property='value'),
     Input(component_id='f_period', component_property='value'),
     Input(component_id='t_growth', component_property='value'),
     Input(component_id='url_link', component_property='value'), ]
)
def update_output_div(coc, roce, growth_high, h_period, f_period, t_growth, url_link):
    name, stock_pe, fy20_pe, roce, intrinsic_pe, overvaluation, df_final = calc_values(url_link, coc, roce, growth_high,
                                                                                       t_growth, f_period, h_period)

    con1 = "Stock symbol: {}".format(name)
    con2 = "Current PE: {}".format(stock_pe)
    con3 = "FY20 PE: {:.2f}".format(fy20_pe)
    con6 = "5-yr median pre-tax RoCE: {} %".format(roce)
    con4 = "The calculated intrinsic PE is: {:.2f}".format(intrinsic_pe)
    con5 = "Degree of overvaluation: {:.2f}%".format(overvaluation)
    con7 = " Sales/Profit 10 Years  5 Years 3 Years  TTM"
    con8 = "{}  {:.2f}    {:.2f}  {:.2f}  {:2f}".format(df_final.loc[0,''],df_final.loc[0,'10 Years'],df_final.loc[0,'5 Years'],df_final.loc[0,'3 Years'],df_final.loc[0,'TTM'])
    con9 = "{}  {:.2f}    {:.2f}  {:.2f}  {:2f}".format(df_final.loc[1,''],df_final.loc[1,'10 Years'],df_final.loc[1,'5 Years'],df_final.loc[1,'3 Years'],df_final.loc[1,'TTM'])


    return con1, con2, con3, con6, con4, con5, con7,con8,con9

if __name__ == '__main__':
    app.run_server(debug=False)