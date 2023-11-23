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

#===============SIDEBAR===============
sidebar = st.sidebar
sidebar.header('Sección de Filtros')

select_moneda = sidebar.selectbox('Elija el nivel educativo',
                                    options = ["BTC", "ETH"])
select_perfil = sidebar.selectbox('Elija el nivel educativo',
                                    options = ["conservador", "moderado", "agresivo", "super_agresivo", "hodler", "yolo"])
select_amount = sidebar.slider(f'Cantidad de {select_moneda}', 0.0, 100.0, 15.0)
#=====================================

risk_df = get_risk_data(select_moneda)
mldata_df = get_mlmodel_data(select_moneda)
sell_matrix = get_sell_matrix()

st.header("DCA Strategy")

st.write("""
    Estrategia DCA aplicado a criptomonedas como Bitcoin y Ethereum.
""")

fig = px.line(risk_df, x="date_time", y="risk_price", title="Risk Graph")
st.plotly_chart(fig)
show_data = st.checkbox('Mostrar tabla')

if show_data:
    st.write(risk_df[['datetime', 'symbol', 'close', 'risk_price']])

st.markdown('___')

st.header('Matriz DCA Venta')

st.write(f"""
    A continuación se muestra la matriz de venta DCA para\
    la cantidad a vender de {select_amount} {select_moneda}.
""")

dca_sell_df = calculate_sell_dca(mldata_df, sell_matrix, select_amount)
dca_sell_df.columns = ['perfil_riesgo', 'banda_40pct', 'banda_50pct', 'banda_60pct', 'banda_70pct', 'banda_80pct', 'banda_90pct']

st.write(dca_sell_df)

