import requests
import streamlit as st
from datetime import datetime, timedelta

BASE_URL = "https://api.cartola.globo.com"

def get_headers():
    return {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Referer": "https://cartola.globo.com/"
    }

@st.cache_data(ttl=300)
def fetch_mercado():
    try:
        r = requests.get(f"{BASE_URL}/atletas/mercado", headers=get_headers(), timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Erro ao buscar mercado: {e}")
        return {}

@st.cache_data(ttl=300)
def fetch_partidas(rodada):
    try:
        r = requests.get(f"{BASE_URL}/partidas/{rodada}", headers=get_headers(), timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Erro ao buscar partidas: {e}")
        return {}

@st.cache_data(ttl=600)
def fetch_ligas_status():
    try:
        r = requests.get(f"{BASE_URL}/mercado/status", headers=get_headers(), timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {}

@st.cache_data(ttl=600)
def fetch_pontuacao_rodada(rodada):
    try:
        r = requests.get(f"{BASE_URL}/atletas/pontuados/{rodada}", headers=get_headers(), timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {}

@st.cache_data(ttl=3600)
def fetch_historico_atleta(atleta_id):
    try:
        r = requests.get(f"{BASE_URL}/atleta/{atleta_id}/pontuacoes", headers=get_headers(), timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return []

def get_rodada_atual():
    status = fetch_ligas_status()
    return status.get("rodada_atual", 10)

def get_mercado_fechado():
    status = fetch_ligas_status()
    return status.get("mercado_status", 1) != 1
