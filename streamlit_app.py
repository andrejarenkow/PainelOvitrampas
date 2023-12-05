#Importação das bibliotecas 
import requests
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium, folium_static
import streamlit as st
import time
from altair import Chart
import plotly.figure_factory as ff
 
# Configurações da página
st.set_page_config(
    page_title="Ovitrampas",
    page_icon="	:bug:",
    layout="wide",
    initial_sidebar_state='collapsed'
) 
col1, col2, col3 = st.columns([1,4,1])

col1.image('logo_cevs (1).png', width=200)
col2.title('Painel de Monitoramento de Aedes aegypti através de Ovitrampas')
col3.image('logo_estado (3).png', width=300)


 
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

  dados["ovitrap_id"] = dados["ovitrap_id"].astype(str).str.zfill(2)
  dados["week"] = dados["week"].astype(str).str.zfill(2)
  dados['week_year'] = dados["year"].astype(str) + '/' + dados["week"] 
  dados['week_year'] = dados['week_year'].astype(str)
  return dados


 
dados = load_data()
dados['week_year'] = dados['week_year'].astype(str)

filtros, metricas = st.columns([2,3])

with filtros:

 col1, col2, col3 = st.columns(3)
 
 with col1:
  #Criando filtros
  ano = st.selectbox('Selecione o ano', options=sorted(dados['year'].unique()), index=1)
 
 with col2:
  lista_municipios = sorted(dados[(dados['year']==ano)]['municipality'].unique())
  lista_municipios.append('Todos')
  municipio = st.selectbox('Selecione o município', options=lista_municipios, index=len(lista_municipios)-1)
 
 with col3:
  semana_epidemiologica = st.selectbox('Selecione a semana epidemiológica', options=sorted(dados[(dados['municipality']==municipio)&(dados['year']==ano)]['week'].unique()))
 


col2, col3 = st.columns([5,5])


 

#Criar novo dataframe com os valores médios de cada ovitrampa
if municipio == 'Todos':
 dados_mapa_geral = dados.copy()

else:
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

if municipio == 'Todos':
 dados_grafico = dados.copy()

else:
 dados_grafico = dados[dados['municipality']==municipio]

dados_ipo = dados_grafico.groupby('week_year').apply(get_ipo).reset_index()
dados_ipo['Métrica'] = 'IPO'
dados_ido = dados_grafico.groupby('week_year').apply(get_ido).reset_index()
dados_ido['Métrica'] = 'IDO'
dados_imo = dados_grafico.groupby('week_year').apply(get_imo).reset_index()
dados_imo['Métrica'] = 'IMO'

# Create figure with secondary y-axis
fig = make_subplots(specs=[[{"secondary_y": True}]])

# Add traces
fig.add_trace(
    go.Scatter(x=dados_ipo['week_year'].astype(str), y=dados_ipo[0], name="IPO"),
    secondary_y=False,
)

fig.add_trace(
    go.Scatter(x=dados_ido['week_year'].astype(str), y=dados_ido[0], name="IDO"),
    secondary_y=True,
)

fig.add_trace(
    go.Scatter(x=dados_imo['week_year'].astype(str), y=dados_imo[0], name="IMO"),
    secondary_y=True,
)

# Add figure title
fig.update_layout(
    title_text=f"Série Histórica de IDO, IPO, IMO - {municipio}"
)

# Set x-axis title
fig.update_xaxes(title_text="Semana Epidemiológica", tickangle=90)

# Set y-axes titles
fig.update_yaxes(title_text="IPO", secondary_y=False, tickformat=".2%", range=[0, 1])
fig.update_yaxes(title_text="IDO - IMO", secondary_y=True, range=[0, 100])



#Criação do mapa
#definição das cores
if municipio != 'Todos': 
 dados_mapa_geral['cor'] = pd.cut(dados_mapa_geral['eggs'], bins=[-1,0,50,100,200,10000], labels=[ 'lightgray',#zero
                                                                                                     'limegreen', # 1 a 50
                                                                                                     'gold', #50 a 100
                                                                                                     'orange', #100 a 200
                                                                                                     'red' #mais de 200
                                                                                                        ])
 
 attr = ('Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community')
 tiles = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
 
 
 m = folium.Map(location=[dados_mapa_geral.latitude.mean(), dados_mapa_geral.longitude.mean()],
                zoom_start=13,
                tiles=tiles, attr=attr
                )
 
 folium.GeoJson('https://raw.githubusercontent.com/andrejarenkow/geodata/main/municipios_rs_CRS/RS_Municipios_2021.json',
     style_function=lambda feature: {
         "fillColor": "rgba(0,0,0,0)",
         "color": "white",
         "weight": 0.5,
     },).add_to(m)
 
 for linha in dados_mapa_geral.itertuples():
 
     ovi_chart = dados[(dados['municipality']==linha.municipality)&(dados['ovitrap_id']==linha.ovitrap_id)]
 
     scatter = (
       Chart(ovi_chart, width=200, height=100, title='Histórico')
       .mark_bar()
       .encode(
         x=dict(field="week_year", title='Semana Epidemiológica'),
         y=dict(field="eggs", title='Quantidade Ovos', type='quantitative')))
     label_grafico = scatter.mark_text(align='center', baseline='bottom').encode(text='eggs')
     vega_lite = folium.VegaLite(
       (scatter+label_grafico),
       width='100%',
       height='100%',
       )
     
       #popup = folium.Popup()
     marker = folium.Circle(
         location=[linha.latitude, linha.longitude],
         popup = folium.Popup().add_child(vega_lite),
         tooltip= 'Armadilha %s - Ovos %s' % (linha.ovitrap_id, linha.eggs),
         radius=150,
         color=linha.cor,
         fill=True,
         fill_color=linha.cor
                     )
       
       #vega_lite.add_to(popup)
       #popup.add_to(marker)
     marker.add_to(m)
 
 
 with col2:
  tab1, tab2 = st.tabs(['Mapa de intensidade','Mapa de calor'])
  with tab1:
   # call to render Folium map in Streamlit
   st.subheader('Mapa de intensidade')
   st_data = folium_static(m)

  with tab2:
   st.subheader('Mapa de calor')
   map_plotly_fig_calor = ff.create_hexbin_mapbox(data_frame=dados_mapa_geral, lat='latitude', lon='longitude', nx_hexagon=25, opacity=0.9, color='eggs',
                                                  mapbox_style="satellite-streets",color_continuous_scale='Reds', show_original_data=True,
                                                 original_data_marker=dict(size=4, opacity=0.8, color="black"), labels={"color": "Número de ovos"})
   map_plotly_fig_calor.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)',
                                margin=go.layout.Margin(l=10, r=10, t=10, b=10),
                              mapbox_accesstoken= 'pk.eyJ1IjoiYW5kcmUtamFyZW5rb3ciLCJhIjoiY2xkdzZ2eDdxMDRmMzN1bnV6MnlpNnNweSJ9.4_9fi6bcTxgy5mGaTmE4Pw',
                             )

   st.plotly_chart(map_plotly_fig_calor, use_container_width=True)
   

else:
 dados_mapa_todos = pd.pivot_table(dados_mapa_geral, index=['latitude','longitude','municipality'],values='eggs', aggfunc='mean').reset_index()

 with col2:
  # call to render Folium map in Streamlit
  tab1, tab2 = st.tabs(['Mapa de calor','Mapa com pontos'])
  with tab1:
   st.write('Mapa de calor de todo estado do RS')
   #map_plotly_fig_calor = px.density_mapbox(dados_mapa_todos, lat="latitude", lon="longitude", z="eggs", mapbox_style="satellite-streets",
   #               color_continuous_scale='Reds', zoom=5, center=dict(lat=-30.456877333125696, lon= -53.01906610604057), height=600, radius=20)
   map_plotly_fig_calor = ff.create_hexbin_mapbox(data_frame=dados_mapa_geral, lat='latitude', lon='longitude', nx_hexagon=100, opacity=1, color='eggs',
                                                  mapbox_style="satellite-streets",color_continuous_scale='Reds',  labels={"color": "Número de ovos"})
   map_plotly_fig_calor.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)',
                                margin=go.layout.Margin(l=10, r=10, t=10, b=10),
                              mapbox_accesstoken= 'pk.eyJ1IjoiYW5kcmUtamFyZW5rb3ciLCJhIjoiY2xkdzZ2eDdxMDRmMzN1bnV6MnlpNnNweSJ9.4_9fi6bcTxgy5mGaTmE4Pw',
                             )

   st.plotly_chart(map_plotly_fig_calor, use_container_width=True)
   
  with tab2:
   st.write('Mapa com pontos de todo estado do RS')
   st.write('Mapa de calor de todo estado do RS')
   map_plotly_fig = px.density_mapbox(dados_mapa_todos, lat="latitude", lon="longitude", z="eggs", mapbox_style="satellite-streets",
                  color_continuous_scale='Reds', zoom=5, center=dict(lat=-30.456877333125696, lon= -53.01906610604057), height=600, radius=20)

   map_plotly_fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)',
                              mapbox_accesstoken= 'pk.eyJ1IjoiYW5kcmUtamFyZW5rb3ciLCJhIjoiY2xkdzZ2eDdxMDRmMzN1bnV6MnlpNnNweSJ9.4_9fi6bcTxgy5mGaTmE4Pw',
                             )
   st.plotly_chart(map_plotly_fig, use_container_width=True)

 

#tabela com as ovitrampas
with col3:
 dados_ovitrampas_municipio = pd.pivot_table(dados_grafico, index='ovitrap_id', columns='week_year', values='eggs', aggfunc='sum').fillna('-')
 dados_ovitrampas_municipio.index.names = ['Nº Ovitr']
 #st.dataframe(dados_ovitrampas_municipio, height=300, use_container_width=False,)

 # Plot!
 st.plotly_chart(fig, use_container_width=True)
 with st.expander('Explicação sobre as métricas'):

   st.latex(r'''
    Índice\:de\:Densidade\:de\:Ovos\:(IDO) =  \frac{Nº\:de\:ovos}{Nº\:de\:armadilhas\:positivas}
    ''')
   st.divider()
   st.latex(r'''
    Índice\:de\:Positividade\:de\:Ovitrampas\:(IPO) =  \frac{Nº\:de\:armadilhas\:positivas\times 100}{Nº\:de\:armadilhas\:examinadas}
    ''')
   st.divider()
   st.latex(r'''
    Índice\:Médio\:de\:Ovos\:(IMO) =  \frac{Nº\:de\:ovos}{Nº\:de\:armadilhas\:examinadas}
    ''')
   


with metricas:
 col1, col2, col3 = st.columns(3)
 with col1:
  st.metric('Total de ovos coletados', value = dados_mapa_geral['eggs'].sum())
  st.metric('IDO', value = (get_ido(dados_mapa_geral)).round(2))
 with col2:
  st.metric('Ovitrampas inspecionadas', value = dados_mapa_geral['ovitrap_id'].count())
  st.metric('IPO', value = str(get_ipo(dados_mapa_geral)*100)+'%')
 with col3:
  st.metric('Municípios com ovitrampas', value = len(dados['municipality'].unique()))
  st.metric('IMO', value = (get_imo(dados_mapa_geral)).round(2))




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
