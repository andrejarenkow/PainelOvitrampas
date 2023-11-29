#Importação das bibliotecas 
import requests
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
import streamlit as st
import time

 
# Configurações da página
st.set_page_config(
    page_title="Ovitrampas",
    page_icon="	:bug:",
    layout="wide",
    initial_sidebar_state='collapsed'
) 
col1, col2, col3 = st.columns([2,12,1])

col1.image('https://www.letravivaleiloes.com.br/custom/imagens/logo.png', width=200)
col2.title('Painel de Monitoramento de Aedes aegypti através de Ovitrampas')
col1.image('https://www.letravivaleiloes.com.br/custom/imagens/logo.png', width=200)


 
 #criando as listas que serão os Datasets
@st.cache_data()
def load_data():
  # URL do endpoint da API
  page=1
  url = f"https://contaovos.dengue.mat.br/pt-br/api/lastcounting?key=ivtcarjsyxyfwyetfmfpdbmutmutbkhdsqumspoyriqrr&page={page}"
  
  # Cria um DataFrame Pandas vazio para armazenar os dados
  dados = pd.DataFrame()
  
  
  response = requests.get(url)
  data = response.json()
  df = pd.DataFrame(data)
  dados = pd.concat([dados, df])
  
  # Loop até a resposta estar vazia
  while len(df) != 0:
  
        # Incrementa o número da página no payload
        page += 1
        url = f"https://contaovos.dengue.mat.br/pt-br/api/lastcounting?key=ivtcarjsyxyfwyetfmfpdbmutmutbkhdsqumspoyriqrr&page={page}"
  
  
        # Envia uma solicitação POST para o endpoint da API
        response = requests.get(url)
  
        # Obtém a resposta JSON da API
        data = response.json()
  
        # Converte a resposta JSON em um DataFrame Pandas
        df = pd.DataFrame(data)
  
        # Concatena o novo DataFrame ao DataFrame existente
        dados = pd.concat([dados, df])
  
        # Imprime o número da página atual
        print(page)
  
  return dados


 
dados = load_data()





col1, col2 = st.columns([1,5])

with col1:
 #Criando filtros
 ano = st.selectbox('Selecione o ano', options=sorted(dados['year'].unique()))
 municipio = st.selectbox('Selecione o município', options=sorted(dados[(dados['year']==ano)]['municipality'].unique()))
 semana_epidemiologica = st.selectbox('Selecione a semana epidemoilógica', options=sorted(dados[(dados['municipality']==municipio)]['week'].unique()))
 

#Criar novo dataframe com os valores médios de cada ovitrampa

filtro = (dados['municipality']==municipio)&(dados['week']==semana_epidemiologica)&(dados['year']==ano)
dados_mapa_geral = pd.pivot_table(dados[filtro], index=['latitude','longitude', 'municipality', 'ovitrap_id'], values='eggs', aggfunc='mean').reset_index()

#IPO IDO IMO
#IDO - Índice Densidade de Ovos
def get_ido(df):
    ido = (df[df['eggs']>0]['eggs'].mean())

    return ido
#IPO - Índice de Positividade de Ovos
def get_ipo(df):
    ipo = ((df['eggs']>0).sum()/len(df)).round(4)

    return ipo

#IMO - Índice Médio de Ovos
def get_imo(df):
    imo = df['eggs'].mean()

    return imo

import plotly.graph_objects as go
from plotly.subplots import make_subplots


dados_ipo = dados.groupby('week').apply(get_ipo).reset_index()
dados_ipo['Métrica'] = 'IPO'
dados_ido = dados.groupby('week').apply(get_ido).reset_index()
dados_ido['Métrica'] = 'IDO'

dados_imo = dados.groupby('week').apply(get_imo).reset_index()
dados_imo['Métrica'] = 'IMO'

# Create figure with secondary y-axis
fig = make_subplots(specs=[[{"secondary_y": True}]])

# Add traces
fig.add_trace(
    go.Scatter(x=dados_ipo['week'], y=dados_ipo[0], name="IPO"),
    secondary_y=False,
)

fig.add_trace(
    go.Scatter(x=dados_ido['week'], y=dados_ido[0], name="IDO"),
    secondary_y=True,
)

fig.add_trace(
    go.Scatter(x=dados_imo['week'], y=dados_imo[0], name="IMO"),
    secondary_y=True,
)

# Add figure title
fig.update_layout(
    title_text="IDO, IPO, IMO"
)

# Set x-axis title
fig.update_xaxes(title_text="xaxis title")

# Set y-axes titles
fig.update_yaxes(title_text="IPO", secondary_y=False, tickformat=".2%")
fig.update_yaxes(title_text="IDO", secondary_y=True)

# Plot!
st.plotly_chart(fig, use_container_width=True)

#Criação do mapa
#definição das cores
dados_mapa_geral['cor'] = pd.cut(dados_mapa_geral['eggs'], bins=[-1,0,50,100,200,10000], labels=[ 'lightgray',#zero
                                                                                                    'limegreen', # 1 a 50
                                                                                                    'gold', #50 a 100
                                                                                                    'orange', #100 a 200
                                                                                                    'red' #mais de 200
                                                                                                       ])

attr = ('Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
)
tiles = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'


m = folium.Map(location=[dados_mapa_geral.latitude.mean(), dados_mapa_geral.longitude.mean()],
               zoom_start=9,
               tiles=tiles, attr=attr
               )

folium.GeoJson('https://raw.githubusercontent.com/andrejarenkow/geodata/main/municipios_rs_CRS/RS_Municipios_2021.json',
    style_function=lambda feature: {
        "fillColor": "rgba(0,0,0,0)",
        "color": "white",
        "weight": 0.5,
    },).add_to(m)

for linha in dados_mapa_geral.itertuples():
  folium.Circle(
      location=[linha.latitude, linha.longitude],
      popup='Município %s - Armadilha %s - Ovos %s' % (linha.municipality, linha.ovitrap_id, linha.eggs),
      radius=150,
      color=linha.cor,
      fill=True,
      fill_color=linha.cor
                   ).add_to(m)


with col2:
 # call to render Folium map in Streamlit
 st_data = st_folium(m, width=725)

#
st.dataframe(dados)


css='''
[data-testid="stMetric"] {

    margin: auto;
    background-color: #EEEEEE;
    border: 2px solid #CCCCCC;
    border-radius: 15px;
}

[data-testid="stMetric"] > div {
    width: fit-content;
    margin: auto;
}

[data-testid="stMetricLabel"] {
    width: fit-content;
    margin: auto;
}

[data-testid="StyledLinkIconContainer"] > div {
    width: fit-content;
    margin: auto;
}

'''
st.markdown(f'<style>{css}</style>',unsafe_allow_html=True)
