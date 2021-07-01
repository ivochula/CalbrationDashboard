# import the libraries----------------------------------------------------
import datetime
import re
from datetime import timedelta

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import pandas as pd
import plotly.graph_objs as go
from dash.dependencies import Output, Input

# read, clean, and filter the data----------------------------------------

df = pd.read_excel('Dados_demo.xlsx')
df = df.fillna('Sem_valores')

# horario atual
time_now = datetime.datetime.now() 

# Limpar os dados dos pontos de calibração e de medição

for i in df.index:
    df.iloc[i,2] = re.sub("\,", "/", df.iloc[i,2])
    df.iloc[i,2] = re.sub("\ ", "", df.iloc[i,2])
    df.iloc[i,3] = re.sub("\,", "/", df.iloc[i,3])
    df.iloc[i,3] = re.sub("\ ", "", df.iloc[i,3])

# Função para separar os valores de uma String e converter para lista de valores Float

def separate(lista):
    x = re.split("\/", lista)
    x = [ float(x) for x in x ]

    return x

# Função para verificar se a calibração ainda está em dia

def validade(data, validade):
    calib_date = data  # Data da calibração
    next_calib = int(validade * 365)  # Valor do tempo para próxima calibração
    now = datetime.datetime.now()  # horario atual
    out = calib_date + timedelta(days=next_calib) # soma à data da calibração a quantidade de dias para a próxima calibração

    return out

# Copia do Dataframe Original

dff = df.copy()

# Lista de Opções para Alertas

alerta = [
 {'label': 'Already Expired', 'value': 0},
 {'label': 'Expire in 1 Month', 'value': 30},
 {'label': 'Expire in 2 Months', 'value': 60},
 {'label': 'Expire in 3 Months', 'value': 90},
 {'label': 'Expire in 6 Months', 'value': 180}]

# Aplicar a função às colunas de indice 2 e 3

dff['Measurement'] = list(map(separate, dff.iloc[:,2]))
dff['Standard Calibration Point'] = list(map(separate, dff.iloc[:,3])) 

# Aplicar funções de Datetime para saber a Validade dos certificados de calibração

df['Validade'] = list(map(validade, df.iloc[:,5], df.iloc[:,6])) # cria coluna com validade de cada certificado
df['Calibration Date'] = pd.DatetimeIndex(df['Calibration Date']).strftime("%Y-%m-%d")  # conv. para formato yyyy-mm-dd
df['Agora'] = datetime.datetime.now().strftime("%Y-%m-%d")
dff['Validade'] = pd.DatetimeIndex(df['Validade']).strftime("%Y-%m-%d")

# Criar nova coluna com a comparação em Booleano da validade
# TRUE - Fora da Validade

df['Validade'] = pd.DatetimeIndex(df['Validade'])
df['DateColumn_A'] = pd.to_datetime(df['Validade'])
df['DateColumn_B'] = pd.to_datetime(df['Agora'])
dff['Comparacao'] = df.DateColumn_A < df.DateColumn_B
df['Comparacao'] = df.DateColumn_A < df.DateColumn_B
# df2 = df.drop_duplicates(subset=['Certificate']) # Subset com os numeros unicos de certificados

df['Comparacao_30'] = df.DateColumn_A < (df.DateColumn_B + datetime.timedelta(days=30))
df['Comparacao_60'] = df.DateColumn_A < (df.DateColumn_B + datetime.timedelta(days=60))
df['Comparacao_90'] = df.DateColumn_A < (df.DateColumn_B + datetime.timedelta(days=90))
df['Comparacao_180'] = df.DateColumn_A < (df.DateColumn_B + datetime.timedelta(days=180))

# app Inicialização--------------------------------------------------------------

app = dash.Dash(__name__, suppress_callback_exceptions=True,
                external_stylesheets=[dbc.themes.SPACELAB])

# Criação de Card informativo

card_expirado = dbc.Card(
    [
        dbc.CardHeader(html.H4("Expired Certificate Number(s)", className = "card-title"), 
                                className = 'bg-primary text-white',),
        dbc.CardBody(
            [         
                dbc.ListGroup(
                    [
                        dcc.Dropdown(id='alertas', options=alerta, value= 0, clearable=False),
                        dbc.ListGroupItem(id='expire'), 
                    ],
                ),
            ], className = 'bg-info',
        ),
    ],
)


card_certificado = dbc.Card(
    [
        dbc.CardHeader(html.H4("Chosen Certificate", className = "card-title"), 
                                className = 'bg-primary text-white',),
        dbc.CardBody(
            [         
                dbc.ListGroup(
                    [
                        dbc.ListGroupItem(id='numero_cert'),
                        dbc.ListGroupItem(id='sit_calib'), 
                        dbc.ListGroupItem(id='prox_calib'),
                    ],
                ),
            ], className = 'bg-info',
        ),
    ],
)

card_total = dbc.Card(
    [
        dbc.CardHeader(html.H4("Overview", className = "card-title"), className = 'bg-primary text-white',),
        dbc.CardBody(
            [         
                dbc.ListGroup(
                    [
                        dbc.ListGroupItem("Total Number of Certificates: {}".format(len(df['Certificate'].unique()))),
                        dbc.ListGroupItem("Expired Certificates: {}".format(df['Comparacao'].sum())),
                    ],
                ),
            ], className = 'bg-info',
        ),
    ],
)

#app DataTable--------------------------------------------------------------

app.layout = dbc.Container([

    dbc.Row([
        dbc.Col(html.H1(html.H1('Operacional Dashboard - Calibration Certificates'), 
                        className="text-center font-weight-bold, mb-4"))
        ]),
    
    dbc.Row([
        dbc.Col(    
            dash_table.DataTable(
        id='datatable-interactivity',
        columns=[{"name": i, "id": i} for i in df.iloc[:,:7].columns],
        data=df.to_dict('records'),
        editable=False,             # allow editing of data inside all cells
        filter_action="native",     # allow filtering of data by user ('native') or not ('none')
        sort_action="none",         # enables data to be sorted per-column by user or not ('none')
        sort_mode="single",         # sort across 'multi' or 'single' columns
        column_selectable="single", # allow users to select 'multi' or 'single' columns
        row_selectable="single",    # allow users to select 'multi' or 'single' rows
        row_deletable=False,        # choose if user can delete a row (True) or not (False)
        selected_columns=[],        # ids of columns that user selects
        selected_rows=[],           # indices of rows that user selects
        page_action="native",       # all data is passed to the table up-front or not ('none')
        page_current=0,             # page number that user is on
        page_size=6,                # number of rows visible per page
        style_cell={                # ensure adequate header width when text is shorter than cell's text
            'minWidth': 95, 'maxWidth': 95, 'width': 95
        },

        tooltip_delay=0,
        tooltip_duration=None,

        tooltip_header={
        'Certificate': 'Calibration Certificate',
        'Parameters': 'Parameters',
        'Measurement': 'Values measured by client\'s equipment',
        'Standard Calibration Point': 'Made by Standard calibrated equipment',
        'Acceptance Criteria': 'Informed by client',
        'Calibration Date': 'yyyy-mm-dd',
        'Calibration Duration': 'In Years',
        },

        style_cell_conditional=[   # Alinha as colunas de Certificados e Parâmetros à esquerda, restantes à direita
            {
                'if': {'column_id': c},
                'textAlign': 'left'
            } for c in ['Certificate', 'Parameters']
        ],
        style_data={                # overflow cells' content into multiple lines
            'whiteSpace': 'normal',
            'height': 'auto'
        },
        style_data_conditional=[
        {
            'if': {'row_index': 'odd'},
            'backgroundColor': 'rgb(248, 248, 248)'
        },
        {
            'if': {
                'filter_query': '{Validade} < {Agora}', # comparing columns to each other
                'column_id': 'Calibration Date'
            },
            'backgroundColor': 'rgba(255, 0, 0, 0.34)',
            'fontWeight': 'bold'
        },
        ],
        style_header={
        'backgroundColor': 'white',
        'fontWeight': 'bold'
        }
    ),
    ),
    ]),

    # app Grafico
    dbc.Row([
        dbc.Col([card_certificado, card_expirado, card_total], width = {'size':4}, style={'marginTop':'0rem'}),
        dbc.Col(dcc.Graph(id='grafico'), width = {'size':8},
    ),  
    ]),

], fluid=True)

# Callback - app interactivity section------------------------------------

# Callback Grafico

@app.callback(
    [Output(component_id='grafico', component_property='figure'),
    Output(component_id='numero_cert', component_property='children'),
    Output(component_id='prox_calib', component_property='children'),
    Output(component_id='sit_calib', component_property='children')],
    Input(component_id='datatable-interactivity', component_property='selected_rows'))
    
def update_graph(selected_rows):

    # Caso exista uma linha selecionada realiza 'if', caso não realiza 'else'
    if len(selected_rows) > 0:
        x = dff.iloc[selected_rows[0], 3] # Valores de pontos padrão
        y = dff.iloc[selected_rows[0], 2] # Valores das medições efetuadas pelo equipamento do cliente
        val = dff.iloc[selected_rows[0], 4] # Valor do critério de aceitação
        legenda = dff.iloc[selected_rows[0], 1] # Informação sobre qual o parametro fisico a colocar na legenda do gráfico
        numero_cert = dff.iloc[selected_rows[0], 0] # Indicação sobre o numero do certificado
        prox_calib = dff.iloc[selected_rows[0], 7] # Informação calculada com a data da prox. calibração
        sit_calib = dff.iloc[selected_rows[0], 8] # informação em binário sobre situação da validade da calibração
    else:
        x = dff.iloc[0, 3] # Valores de pontos padrão
        y = dff.iloc[0, 2] # Valores das medições efetuadas pelo equipamento do cliente
        val = dff.iloc[0, 4] # Valor do critério de aceitação
        legenda = dff.iloc[0, 1] # Informação sobre qual o parametro fisico a colocar na legenda do gráfico
        numero_cert = dff.iloc[0, 0] # Indicação sobre o numero do certificado
        prox_calib = dff.iloc[0, 7] # Informação calculada com a data da prox. calibração
        sit_calib = dff.iloc[0, 8] # informação em binário sobre situação da validade da calibração


    # Conferir a validade do certificado / informação em binário
    if sit_calib:
        sit_calib = 'Expired'
    else:
        sit_calib = 'Valid'
    
    # Valores para a linha do critério de aceitação
    x_rev = x[::-1]
    x_upper = [ i+val for i in x]
    x_lower =  [ i-val for i in x]
    x_lower = x_lower[::-1]

    # Plotar o gráfico com as 2 linhas de calibração e critério de aceitação
    fig = go.Figure()

    fig.add_trace(go.Scatter(x = x, y = x, name = 'Calibration Standard', connectgaps=True))

    fig.add_trace(go.Scatter(x = x, y = y, name='Equipment Measurement', connectgaps=True))

    fig.update_layout(autosize=False, width=1000, height=700,
                    margin=dict(l=0, r=0, b=100, t=100, pad=4),
                    )

    fig.update_layout(title={'text': "Comparing Measurement",
                        'y':0.94,
                        'x':0.41,
                        })
    fig.update_xaxes(title_text= legenda)
    fig.update_layout(title_font_size=36)

    fig.add_trace(go.Scatter(x=x+x_rev, y=x_upper+x_lower,
                            fill='toself',
                            fillcolor='rgba(0,176,246,0.2)',
                            line_color='rgba(255,255,255,0)',
                            showlegend=False,
                            name='Acceptance Criteria',))

    # Deixar a informação resumida para entregar ao 'return'
    numero_cert = 'Identification: {}'.format(numero_cert)
    prox_calib = 'Next calibration date: {}'.format(prox_calib)
    sit_calib = 'Validity: {}'.format(sit_calib)

    return fig, numero_cert, prox_calib, sit_calib,

# Segundo Callback para Verificar a validade dos certificados no futuro próximo

@app.callback(
    dash.dependencies.Output('expire', 'children'),
    dash.dependencies.Input('alertas', 'value'))

def update_output(value):

    if value == 0:
        valor = 'Comparacao'
    elif value == 30:
        valor = 'Comparacao_30'
    elif value == 60:
        valor = 'Comparacao_60'
    elif value == 90:
        valor = 'Comparacao_90'
    else:
        valor = 'Comparacao_180'

    cert_print = []

    for i in range(0,len(df)):
        if df.loc[i,valor]:
            cert_print.append(df.iloc[i,0])

    return '{}'.format(cert_print)

# APP RUN

if __name__ == '__main__':
    app.run_server(debug=False)



