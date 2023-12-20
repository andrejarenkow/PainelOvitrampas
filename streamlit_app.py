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
import geopandas as gpd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
 
# Configurações da página
st.set_page_config(
    page_title="Ovitrampas",
    page_icon="	:bug:",
    layout="wide",
    initial_sidebar_state='collapsed'
) 
col1, col2, col3 = st.columns([1,4,1])

col1.image('logo_cevs (1).png', width=200)
col2.header('Painel de Monitoramento de Aedes aegypti através de Ovitrampas')
col3.image('logo_estado (3).png', width=300)


 
 #criando as listas que serão os Datasets
@st.cache_data(ttl='2h')
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

  dict_mes = {1: '01 - Janeiro',
            2: '02 - Fevereiro',
            3: '03 - Março',
            4: '04 - Abril',
            5: '05 - Maio',
            6: '06 - Junho',
            7: '07 - Julho',
            8: '08 - Agosto',
            9: '09 - Setembro',
            10: '10 - Outubro',
            11: '11 - Novembro', 
            12: '12 - Dezembro'}

  dados["ovitrap_id"] = dados["ovitrap_id"].astype(str).str.zfill(2)
  dados["week"] = dados["week"].astype(str).str.zfill(2)
  dados['week_year'] = dados["year"].astype(str) + '-W' + dados["week"]
  dados['mes'] = pd.to_datetime(dados['week_year']+'-1', format='%Y-W%W-%w').dt.month.replace(dict_mes)
  dados['mes_ano'] = dados["year"].astype(str) + '-'+ dados['mes']
  dados['week_year'] = dados["year"].astype(str) + '/' + dados["week"]
  dados['week_year'] = dados['week_year'].astype(str)
  return dados


 
dados = load_data()
dados['week_year'] = dados['week_year'].astype(str)

aba_painel, aba_sobre, aba_referencias, aba_grades = st.tabs(['Painel','Sobre', 'Documentos de Referência', 'Grades de sugestão'])

with aba_painel:
 
 filtros, metricas, novas_metricas = st.columns([3,4,2])
 
 with filtros:
  container = st.container(border=True)
  with container:
   st.subheader('Filtros')
   col1, col2 = st.columns(2)
   
   with col1:
    #Criando filtros
    ano = st.selectbox('Selecione o ano', options=sorted(dados['year'].unique()), index=1)
    lista_municipios = sorted(dados[(dados['year']==ano)]['municipality'].unique())
    lista_municipios.append('Todos')
    municipio = st.selectbox('Selecione o município', options=lista_municipios, index=len(lista_municipios)-1)
   
    if municipio != 'Todos':
     mes = st.selectbox('Selecione o mês', options=sorted(dados[(dados['municipality']==municipio)&(dados['year']==ano)]['mes'].unique()))
     semana_epidemiologica = dados[(dados['municipality']==municipio)&(dados['year']==ano)&(dados['mes']==mes)]['week'].values[0]
     st.write(f'Semana epidemiológica {semana_epidemiologica}')
  
    else:
     mes = st.selectbox('Selecione o mês', options=sorted(dados[(dados['year']==ano)]['mes'].unique()))
     #semana_epidemiologica = dados[(dados['municipality']==municipio)&(dados['year']==ano)&(dados['mes']==mes)]['week'].values[0]
     #st.write(f'Semana epidemiológica {semana_epidemiologica}')
  with col2:
   st.write('Faixas de ovitrampas')
   lista_filtro_faixa = []
   filtro_faixa_0 = st.toggle('Nenhuma', value  = True)
   if filtro_faixa_0:
    lista_filtro_faixa.append('lightgray')
   
   filtro_faixa_1_a_50 = st.toggle('1 a 50', value  = True)
   if filtro_faixa_1_a_50:
    lista_filtro_faixa.append('limegreen')
    
   filtro_faixa_50_a_100 = st.toggle('51 a 100', value  = True)
   if filtro_faixa_50_a_100:
    lista_filtro_faixa.append('gold')  
    
   filtro_faixa_100_a_200 = st.toggle('101 a 200', value  = True)
   if filtro_faixa_100_a_200:
    lista_filtro_faixa.append('orange')
    
   filtro_faixa_200_ou_mais =st.toggle('Mais de 200', value  = True)
   if filtro_faixa_200_ou_mais:
    lista_filtro_faixa.append('red')


 
 
 #novas_metricass, col3 = st.columns([7,5])
 
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
 

 
 if municipio == 'Todos':
  dados_grafico = dados.copy()
 
 else:
  dados_grafico = dados[dados['municipality']==municipio]
 
 dados_ipo = dados_grafico.groupby('mes_ano').apply(get_ipo).reset_index()
 dados_ipo['Métrica'] = 'IPO'
 dados_ido = dados_grafico.groupby('mes_ano').apply(get_ido).reset_index()
 dados_ido['Métrica'] = 'IDO'
 dados_imo = dados_grafico.groupby('mes_ano').apply(get_imo).reset_index()
 dados_imo['Métrica'] = 'IMO'
 
 # Create figure with secondary y-axis
 fig = make_subplots(specs=[[{"secondary_y": True}]])
 
 # Add traces
 fig.add_trace(
     go.Scatter(x=dados_ipo['mes_ano'].astype(str), y=dados_ipo[0], name="IPO"),
     secondary_y=False,
 )
 
 fig.add_trace(
     go.Scatter(x=dados_ido['mes_ano'].astype(str), y=dados_ido[0], name="IDO"),
     secondary_y=True,
 )
 
 fig.add_trace(
     go.Scatter(x=dados_imo['mes_ano'].astype(str), y=dados_imo[0], name="IMO"),
     secondary_y=True,
 )
 
 # Add figure title
 fig.update_layout(
     title_text=f"Série Histórica de IDO, IPO, IMO - {municipio}"
 )
 
 # Set x-axis title
 fig.update_xaxes(title_text="Data", tickangle=-90)
 
 # Set y-axes titles
 fig.update_yaxes(title_text="IPO", secondary_y=False, tickformat=".2%", range=[0, 1])
 fig.update_yaxes(title_text="IDO - IMO", secondary_y=True, range=[0, 200])
 
 
 
 #Criação do mapa
 #definição das cores
 if municipio != 'Todos': 
  dados_mapa_geral['cor'] = pd.cut(dados_mapa_geral['eggs'], bins=[-1,0,50,100,200,10000], labels=[ 'lightgray',#zero
                                                                                                      'limegreen', # 1 a 50
                                                                                                      'gold', #50 a 100
                                                                                                      'orange', #100 a 200
                                                                                                      'red' #mais de 200
                                                                                                         ])

  dados_mapa_geral = dados_mapa_geral[dados_mapa_geral['cor'].isin(lista_filtro_faixa)]
  attr = ('Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community')
  tiles = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
  
  
  m = folium.Map(location=[dados_mapa_geral.latitude.mean(), dados_mapa_geral.longitude.mean()],
                 zoom_start=13,
                 tiles=tiles, attr=attr,
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
  
  
  with metricas:
   tab1, tab2 = st.tabs(['Mapa de intensidade','Mapa de calor'])
   with tab1:
    # call to render Folium map in Streamlit
    st.subheader('Mapa de intensidade')
    st_data = folium_static(m, height=500)
 
   with tab2:
    st.subheader('Mapa de calor')
    map_plotly_fig_calor = px.density_mapbox(dados_mapa_geral, lat="latitude", lon="longitude", z="eggs", mapbox_style="satellite-streets",
                   color_continuous_scale='Reds', zoom=13, center=dict(lat=dados_mapa_geral['latitude'].mean(), lon=dados_mapa_geral['longitude'].mean()), height=600, radius=75)
    map_plotly_fig_calor.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)',
                                 margin=go.layout.Margin(l=10, r=10, t=10, b=10),
                               mapbox_accesstoken= 'pk.eyJ1IjoiYW5kcmUtamFyZW5rb3ciLCJhIjoiY2xkdzZ2eDdxMDRmMzN1bnV6MnlpNnNweSJ9.4_9fi6bcTxgy5mGaTmE4Pw',
                              )
 
    st.plotly_chart(map_plotly_fig_calor, use_container_width=True)
    
 
 else:
  dados_mapa_todos = pd.pivot_table(dados_mapa_geral, index=['latitude','longitude','municipality'],values='eggs', aggfunc='mean').reset_index()
 
  with metricas:
   # call to render Folium map in Streamlit
   tab1, tab2 = st.tabs(['Mapa com pontos','Mapa de calor'])
   with tab1:
    st.write('Mapa com pontos de todo estado do RS')
    map_plotly_fig_calor = px.scatter_mapbox(dados_mapa_todos, lat="latitude", lon="longitude", mapbox_style="open-street-map", color_continuous_scale='Reds',
                    zoom=5, center=dict(lat=-30.456877333125696, lon= -53.01906610604057), height=600, size_max=500)
    #map_plotly_fig_calor = ff.create_hexbin_mapbox(data_frame=dados_mapa_geral, lat='latitude', lon='longitude', nx_hexagon=100, opacity=1, color='eggs',
    #                                               mapbox_style="satellite-streets",color_continuous_scale='Reds',  labels={"color": "Número de ovos"})
    map_plotly_fig_calor.update_layout( margin=go.layout.Margin(l=10, r=10, t=10, b=10),paper_bgcolor='rgba(0,0,0,0)',
                               mapbox_accesstoken= 'pk.eyJ1IjoiYW5kcmUtamFyZW5rb3ciLCJhIjoiY2xkdzZ2eDdxMDRmMzN1bnV6MnlpNnNweSJ9.4_9fi6bcTxgy5mGaTmE4Pw',
                              )
    #map_plotly_fig_calor.update_traces(cluster=dict(enabled=True))
 
    st.plotly_chart(map_plotly_fig_calor, use_container_width=True)
    
   with tab2:
    
    st.write('Mapa de calor de todo estado do RS')
    map_plotly_fig = px.density_mapbox(dados_mapa_todos, lat="latitude", lon="longitude", z="eggs", mapbox_style="satellite-streets",
                   color_continuous_scale='Reds', zoom=5, center=dict(lat=-30.456877333125696, lon= -53.01906610604057), height=600, radius=20)
 
    map_plotly_fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)',margin=go.layout.Margin(l=10, r=10, t=10, b=10),
                               mapbox_accesstoken= 'pk.eyJ1IjoiYW5kcmUtamFyZW5rb3ciLCJhIjoiY2xkdzZ2eDdxMDRmMzN1bnV6MnlpNnNweSJ9.4_9fi6bcTxgy5mGaTmE4Pw',
                              )
    st.plotly_chart(map_plotly_fig, use_container_width=True)
 
  
 
 #tabela com as ovitrampas
 with filtros:
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
    
 
 
 with novas_metricas:
   st.metric('Total de ovos coletados', value = dados_mapa_geral['eggs'].sum())
   st.metric('IPO - Índice de Positividade de Ovos', value = str((get_ipo(dados_mapa_geral)*100).round(1))+'%')

   st.metric('Ovitrampas inspecionadas', value = dados_mapa_geral['ovitrap_id'].count())
   st.metric('IDO - Índice de Densidade de Ovos', value = (get_ido(dados_mapa_geral)).round(1))

   st.metric('Municípios com ovitrampas', value = len(dados['municipality'].unique()))
   st.metric('IMO - Índice de Média de Ovos', value = (get_imo(dados_mapa_geral)).round(1))

with aba_sobre:
 st.header('O que são as ovitrampas?')
 coluna_texto, coluna_imagens = st.columns([2,3])
 with coluna_texto:
  st.markdown(
   """
 As ovitrampas são armadilhas que simulam um criadouro de Aedes aegypti utilizadas para detectar a presença e abundância do vetor por meio dos ovos depositados na mesma. 
 Consiste em um pote escuro com uma palheta de madeira (Eucatex®) presa na parede lateral com um clipe metálico. 
 Se adiciona 300 ml de água para atrair as fêmeas de Aedes spp. para realizar a postura dos ovos.  
 Se utiliza levedura de cerveja como atrativo, adicionado na água na concentração de 0,04%, para aumentar a atração das fêmeas de Aedes spp.
 
 
 A partir delas, pode-se calcular a densidade da população do mosquito naquele município e quais os locais de maior proliferação. 
 Com isso, a gestão pode providenciar outras estratégias mecânicas de combate à dengue, como mutirões de limpeza, educação em saúde, entre outras.
 
 
 Cada município irá instalar entre 50 a 100 armadilhas, que consiste em um vaso de planta sem furo e uma palheta de eucatex,
 onde é colocado levedo de cerveja afim de atrair a fêmea do mosquito a depositar os ovos no local. 
 A equipe retorna em cinco dias para recolher a armadilha e levá-la ao laboratório para fazer a contagem dos ovos.
   """
  )

with coluna_imagens:
 col1, col2 = st.columns(2)
 col1.image('WhatsApp Image 2023-10-02 at 14.27.35.jpeg', width=350, caption='Ovos de Aedes aegypti na palheta')
 col2.image('fiocruz_20210512_mauro_campello_00029 (2).jpg', width=350, caption='Ilustração digital de ovos de Aedes aegypti - Imagem Fundação Oswaldo Cruz')
 col1.image('fiocruz_20180220_raquel_portugal_01096.jpg', width=350, caption='Preparação de armadilha - Imagem Fundação Oswaldo Cruz')
 
 
with aba_referencias:
 col1, col2, col3 = st.columns([1,2,2])
 col2.write('Contagem de ovos de Aedes aegypti em ovitrampas')
 col2.video('https://www.youtube.com/watch?v=8OCSZHd47Zs')
 col3.write('Metodologia para coleta de ovos Aedes aegypti')
 col3.video('https://www.youtube.com/watch?v=aWBtdSYdXVQ')

 with col1:
  st.markdown(
"""
   * [Apostila Ovitrampas Fiocruz](https://drive.google.com/file/d/1uJ4USZbgjyqmNU7_iQQskx9wurUkFTqJ/view)
   * [Boletim Ovitrampas RS](https://drive.google.com/file/d/14j0kD-UNeF5uy-bBnYGLMjaB_ppxzTEL/view)
   * [Grade de Contagem de Ovos](https://drive.google.com/file/d/1ddBBGHmaZ7lvKuLSLtvizuzKaXSDQdd_/view)
   * [Modelo do Termo de Adesão às Ovitrampas](https://drive.google.com/file/d/1Jg7USwHiCFEahRD3gRH4ebBZ_vnQPepJ/view)
   * [Modelo de Etiquetas](https://drive.google.com/file/d/1f0zMulTh-FDsCf1XQDJ4NmM-utItBaC-/view)
   * [Nota Técnica Ministério da Saúde nº 33/2022](https://saude.rs.gov.br/upload/arquivos/202212/14131027-nota-tecnica-ms-n-33-2022-ovitrampas.pdf)
   * [POP Ovitrampas](https://drive.google.com/file/d/1ws9EFSnhx82CUgF-UVUjENQpvJ0t-t7b/view)
   * [Roteiro de adesão Ovitrampas para municípios](https://drive.google.com/file/d/1u6Xx9qXCZUP46OIlnwObNKWqjWtmdJTV/view)
   * [Termo de Autorização](https://drive.google.com/file/d/1WYCpH3gBqsW3IvrKsPlGJZ4EoYx_rJfV/view)
   * [Tutorial Aplicativo Minhas Coordenadas](https://drive.google.com/file/d/1WCCN59b5qxslM5GNQ975KZbTCmmGloWe/view)
"""   
  )
 
with aba_grades:
 # Carregue o GeoJSON com dados do tipo MultiLineString usando geopandas
 geojson_path = 'malhas_geojson/sao_leopoldo.geosjon'
 gdf = gpd.read_file(geojson_path)
 
 # Exploda o GeoDataFrame para garantir que cada parte do MultiLineString seja tratada separadamente
 gdf_exploded = gdf.explode(index_parts=True)
 
 # Crie colunas separadas para latitude e longitude
 gdf_exploded['latitude'] = gdf_exploded.geometry.apply(lambda geom: [coord[1] for coord in geom.coords])
 gdf_exploded['longitude'] = gdf_exploded.geometry.apply(lambda geom: [coord[0] for coord in geom.coords])
 
 # Converta os dados para o formato adequado para plotly.express
 gdf_plotly = gdf_exploded.explode('latitude').explode('longitude')
 
 # Use plotly.express para plotar linhas
 fig = px.line_mapbox(gdf_plotly,
                      lat='latitude', 
                      lon='longitude',
                      line_group='id',
                      mapbox_style="satellite-streets",
                      zoom=11,
                      height=600
                      )

 fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', margin=go.layout.Margin(l=10, r=10, t=10, b=10),
                               mapbox_accesstoken= 'pk.eyJ1IjoiYW5kcmUtamFyZW5rb3ciLCJhIjoiY2xkdzZ2eDdxMDRmMzN1bnV6MnlpNnNweSJ9.4_9fi6bcTxgy5mGaTmE4Pw',
                              )
 
 # Exiba o gráfico
 col1, col2 = st.columns(2)
 with col1:
  st.write('São Leopoldo')
  st.plotly_chart(fig, use_container_width=True)


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
