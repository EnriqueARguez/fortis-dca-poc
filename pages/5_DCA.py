from urllib.error import URLError

import altair as alt
import pandas as pd

import streamlit as st
import mysql.connector
from mysql.connector import Error


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

risk_df = get_risk_data()

st.write("""
    Este es un ejemplo.
""")

st.write(risk_df)