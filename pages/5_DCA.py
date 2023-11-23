from urllib.error import URLError

import altair as alt
import pandas as pd

import streamlit as st
import mysql.connector
from mysql.connector import Error
import plotly.express as px


@st.cache_data
def get_risk_data():
    conn = mysql.connector.connect(host=st.secrets["HOST"], 
                            user=st.secrets["USER"], 
                            password=st.secrets["PASSWORD"], 
                            database=st.secrets["DATABASE"])
    cursor = conn.cursor()

    cursor.execute("select * from analytics.ml_risk_metrics_historic mrmh order by date_time")
    column_names = [desc[0] for desc in cursor.description]
    result: tuple = cursor.fetchall()

    cursor.close()
    conn.close()
    df = pd.DataFrame(result,columns=column_names)
    return df

#===============SIDEBAR===============
sidebar = st.sidebar
sidebar.header('Sección de Filtros')

select_moneda = sidebar.selectbox('Elija el nivel educativo',
                              options = ["BTC", "ETH"])
#=====================================

st.set_page_config(page_title="Mi Dashboard",
                   page_icon=":busts_in_silhouette:")

risk_df = get_risk_data()

st.header("DCA Strategy")

st.write("""
    Estrategia DCA aplicado a criptomonedas como Bitcoin y Ethereum
""")

fig = px.line(risk_df[risk_df.symbol.str.contains(select_moneda)], x="date_time", y="risk_price", title="Risk Graph")

st.write(risk_df)