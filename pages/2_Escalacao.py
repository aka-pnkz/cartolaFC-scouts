# pages/2_Escalacao.py
import streamlit as st
import pandas as pd
from utils.api import fetch_mercado
from utils.score_mitada import enriquecer_df
from utils.exportacao import exportar_excel, gerar_texto_escalacao
from utils.alertas import alertas_escalacao, resumo_alertas
from utils.comparador import gerar_radar_chart, tabela_comparativa

st.set_page_config(page_title="Escalação | Cartola Analyzer", layout="wide")

FORMACOES = {
    "4-3-3": {"Goleiro":1,"Lateral":2,"Zagueiro":2,"Meia":3,"Atacante":3,"Técnico":1},
    "4-4-2": {"Goleiro":1,"Lateral":2,"Zagueiro":2,"Meia":4,"Atacante":2,"Técnico":1},
    "3-5-2": {"Goleiro":1,"Lateral":1,"Zagueiro":3,"Meia":4,"Atacante":2,"Técnico":1},
    "3-4-3": {"Goleiro":1,"Lateral":1,"Zagueiro":3,"Meia":3,"Atacante":3,"Técnico":1},
    "4-5-1": {"Goleiro":1,"Lateral":2,"Zagueiro":2,"Meia":5,"Atacante":1,"Técnico":1},
    "5-3-2": {"Goleiro":1,"Lateral":2,"Zagueiro":3,"Meia":3,"Atacante":2,"Técnico":1},
    "5-4-1": {"
