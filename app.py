import streamlit as st
import pandas as pd
import requests
import datetime
from datetime import datetime, timezone

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MITAR-BOT PRO | Live Status", page_icon="⏰", layout="wide")

# --- CAMADA DE DADOS ---
def get_live_data():
    # Removendo cache para garantir dados de status em tempo real no fechamento
    mercado = requests.get("https://api.cartola.globo.com/atletas/mercado").json()
    partidas = requests.get("https://api.cartola.globo.com/partidas").json()
    status_mercado = requests.get("https://api.cartola.globo.com/mercado/status").json()
    return mercado, partidas, status_mercado

# --- UI DE FECHAMENTO (SIDEBAR) ---
def show_market_status(status_raw):
    st.sidebar.markdown("---")
    st.sidebar.subheader("⏳ Status do Mercado")
    
    # Extrair data de fechamento do JSON
    # Exemplo: status_raw['fechamento'] = {'dia': 4, 'mes': 4, 'ano': 2026, 'hora': 18, 'minuto': 0}
    f = status_raw['fechamento']
    data_fechamento = datetime(f['ano'], f['mes'], f['dia'], f['hora'], f['minuto'], tzinfo=timezone.utc)
    agora = datetime.now(timezone.utc)
    
    restante = data_fechamento - agora
    
    if restante.total_seconds() > 0:
        horas, rem = divmod(restante.seconds, 3600)
        minutos, _ = divmod(rem, 60)
        st.sidebar.error(f"Mercado fecha em: {restante.days}d {horas}h {minutos}min")
    else:
        st.sidebar.warning("🚫 MERCADO FECHADO!")

# --- APP PRINCIPAL ---
def main():
    st.title("⚽ MITAR-BOT PRO | Live Monitor")
    
    # Botão de Atualização Manual
    if st.sidebar.button("🔄 Atualizar Dados Agora"):
        st.cache_data.clear()
        st.rerun()

    mercado, partidas_raw, status_mercado = get_live_data()
    show_market_status(status_mercado)

    # ... (Lógica de processamento anterior aqui) ...
    # Supondo que 'time_ideal' foi gerado pela lógica anterior
    
    st.header("🏆 Seu Time Ideal")
    
    # --- NOVO: CHECK DE INTEGRIDADE ---
    # Simulando um check se algum jogador mudou de status
    status_critico = False
    for _, player in time_ideal.iterrows():
        if player['status_id'] != 7: # 7 = Provável
            st.error(f"🚨 ALERTA: {player['apelido']} não é mais PROVÁVEL! Status atual: {player['status_id']}")
            status_critico = True
    
    if not status_critico:
        st.success("✅ Todos os jogadores sugeridos estão confirmados como Prováveis.")

    # Exibir a Tabela Pro
    st.dataframe(time_ideal[['foto', 'apelido', 'clube_nome', 'status_id', 'score_mitada']],
                 column_config={
                     "foto": st.column_config.ImageColumn("Atleta"),
                     "status_id": st.column_config.NumberColumn("Status", help="7 = Provável")
                 }, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()
