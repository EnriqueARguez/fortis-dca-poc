from urllib.error import URLError
import altair as alt
import pandas as pd
import streamlit as st
import mysql.connector
from mysql.connector import Error
import plotly.express as px

@st.cache_data
def get_risk_data(moneda):
    conn = mysql.connector.connect(host=st.secrets["HOST"], 
                            user=st.secrets["USER"], 
                            password=st.secrets["PASSWORD"], 
                            database=st.secrets["DATABASE"])
    cursor = conn.cursor()
    cursor.execute(f"""select * from analytics.ml_risk_metrics_historic 
                   where symbol like '%{moneda}%'
                   order by date_time""")
    column_names = [desc[0] for desc in cursor.description]
    result: tuple = cursor.fetchall()
    cursor.close()
    conn.close()
    df = pd.DataFrame(result,columns=column_names)
    return df

@st.cache_data
def get_mlmodel_data(moneda):
    conn = mysql.connector.connect(host=st.secrets["HOST"], 
                            user=st.secrets["USER"], 
                            password=st.secrets["PASSWORD"], 
                            database=st.secrets["DATABASE"])
    cursor = conn.cursor()
    cursor.execute(f"""select * from analytics.ml_risk_metrics
                   where ticker like '%{moneda}%'
                   order by 1, 2""")
    column_names = [desc[0] for desc in cursor.description]
    result: tuple = cursor.fetchall()
    cursor.close()
    conn.close()
    df = pd.DataFrame(result,columns=column_names)
    return df

@st.cache_data
def get_sell_matrix():
    conn = mysql.connector.connect(host=st.secrets["HOST"], 
                            user=st.secrets["USER"], 
                            password=st.secrets["PASSWORD"], 
                            database=st.secrets["DATABASE"])
    cursor = conn.cursor()
    cursor.execute("select * from analytics.matriz_ventas")
    column_names = [desc[0] for desc in cursor.description]
    result: tuple = cursor.fetchall()
    cursor.close()
    conn.close()
    df = pd.DataFrame(result,columns=column_names)
    return df

@st.cache_data
def get_buy_matrix():
    conn = mysql.connector.connect(host=st.secrets["HOST"], 
                            user=st.secrets["USER"], 
                            password=st.secrets["PASSWORD"], 
                            database=st.secrets["DATABASE"])
    cursor = conn.cursor()
    cursor.execute("select * from analytics.matriz_compras")
    column_names = [desc[0] for desc in cursor.description]
    result: tuple = cursor.fetchall()
    cursor.close()
    conn.close()
    df = pd.DataFrame(result,columns=column_names)
    return df

@st.cache_data
def calculate_sell_dca(data : pd.DataFrame, matrix : pd.DataFrame, amount : float):
    r04 = data[data['risk'] >= 0.4]['price'].min()
    r05 = data[data['risk'] >= 0.5]['price'].min()
    r06 = data[data['risk'] >= 0.6]['price'].min()
    r07 = data[data['risk'] >= 0.7]['price'].min()
    r08 = data[data['risk'] >= 0.8]['price'].min()
    r09 = data[data['risk'] >= 0.9]['price'].min()
    matrix['r04'] *= r04 * amount
    matrix['r05'] *= r05 * amount
    matrix['r06'] *= r06 * amount
    matrix['r07'] *= r07 * amount
    matrix['r08'] *= r08 * amount
    matrix['r09'] *= r09 * amount
    matrix['rt'] = matrix.iloc[:,1:].sum(axis=1)
    return matrix

@st.cache_data
def calculate_buy_dca(matrix : pd.DataFrame, amount : float, dist1 : float, dist2 : float, dist3 : float):
    matrix['r00'] *= amount * dist1
    matrix['r01'] *= amount * dist1
    matrix['r02'] *= amount * dist2
    matrix['r03'] *= amount * dist2
    matrix['r04'] *= amount * dist3
    matrix['r05'] *= amount * dist3
    matrix['r06'] *= amount * dist3
    matrix['r07'] *= amount * dist3
    return matrix

#===============SIDEBAR===============
sidebar = st.sidebar
sidebar.header('Sección de Filtros')

select_moneda = sidebar.selectbox('Elija la criptomoneda',
                                    options = ["BTC", "ETH"])
# select_perfil = sidebar.selectbox('Elija el nivel educativo',
#                                     options = ["conservador", "moderado", "agresivo", "super_agresivo", "hodler", "yolo"])
sidebar.markdown('##')
# select_amount = sidebar.slider(f'Cantidad de {select_moneda}', 0.0, 100.0, 15.0)
select_amount = sidebar.text_input(f'Introduzca la cantidad de {select_moneda} a implementar con DCA', key = 'select_amount', value = '1.0')
sidebar.markdown('##')
select_amount2 = sidebar.text_input(f'Introduzca la cantidad de USD a implementar con DCA', key = 'select_amount2', value = '1000')
#=====================================

risk_df = get_risk_data(select_moneda)
mldata_df = get_mlmodel_data(select_moneda)
sell_matrix = get_sell_matrix()
buy_matrix = get_buy_matrix()

st.header("DCA Strategy")

st.write("""
    Estrategia DCA aplicado a criptomonedas como Bitcoin y Ethereum.
""")

fig = px.line(risk_df, x="date_time", y="risk_price", title="Risk Graph")
st.plotly_chart(fig)
show_data = st.checkbox('Mostrar tabla')

if show_data:
    st.write(risk_df[['date_time', 'symbol', 'close', 'risk_price']])

st.markdown('___')

st.header('Matriz DCA Venta')

st.write(f"""
    A continuación se muestra la matriz de venta DCA para\
    la cantidad a vender de {0 if select_amount == '' else select_amount} {select_moneda}.
""")

dca_sell_df = calculate_sell_dca(mldata_df, sell_matrix, float(0 if select_amount == '' else select_amount))
dca_sell_df.columns = ['perfil_riesgo', 'banda_40pct', 'banda_50pct', 'banda_60pct', 'banda_70pct', 'banda_80pct', 'banda_90pct', 'ganancia_total']

st.write(dca_sell_df)

st.markdown('##')
st.header('Matriz DCA Compra')

st.write(f"""
    A continuación se muestra la matriz de venta DCA para\
    la cantidad a comprar de {0 if select_amount2 == '' else select_amount2} USD.
""")

# st.write("""Distribuciones de dinero en las bandas de riesgo:""")
col1, col2, col3 = st.columns(3)
with col1:
    select_dist1 = st.text_input('Distribución bandas bajas', key = 'select_dist1', value = '0.1')

with col2:
    select_dist2 = st.text_input('Distribución bandas medias', key = 'select_dist2', value = '0.7')

with col3:
    select_dist3 = st.text_input('Distribución bandas altas', key = 'select_dist3', value = '0.2')
st.write('Nota: La suma debe ser igual a 1.')

dca_buy_df = calculate_buy_dca(buy_matrix, float(0 if select_amount2 == '' else select_amount2), float(0 if select_dist1 == '' else select_dist1), float(0 if select_dist2 == '' else select_dist2), float(0 if select_dist3 == '' else select_dist3))
dca_buy_df.columns = ['perfil_riesgo', 'banda_0pct', 'banda_10pct', 'banda_20pct', 'banda_30pct', 'banda_40pct', 'banda_50pct', 'banda_60pct', 'banda_70pct']

st.write(dca_buy_df)