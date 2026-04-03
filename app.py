import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MITAR-BOT PRO | Rodada 10", page_icon="🛡️", layout="wide")

# --- CAMADA DE DADOS ---
@st.cache_data(ttl=600)
def get_all_data():
    try:
        mercado = requests.get("https://api.cartola.globo.com/atletas/mercado").json()
        partidas = requests.get("https://api.cartola.globo.com/partidas").json()
        return mercado, partidas
    except:
        st.error("Erro na conexão com a API.")
        return None, None

# --- CAMADA DE INTELIGÊNCIA ---
def process_data(mercado_raw, partidas_raw):
    atletas = mercado_raw['atletas']
    clubes = mercado_raw['clubes']
    posicoes = mercado_raw['posicoes']
    df = pd.DataFrame(atletas)
    
    confrontos_map = {}
    for p in partidas_raw['partidas']:
        c_id, v_id = p['clube_casa_id'], p['clube_visitante_id']
        c_pos, v_pos = p['clube_casa_posicao'], p['clube_visitante_posicao']
        confrontos_map[c_id] = {'vs': clubes[str(v_id)]['nome'], 'vs_pos': v_pos, 'mando': '🏠'}
        confrontos_map[v_id] = {'vs': clubes[str(c_id)]['nome'], 'vs_pos': c_pos, 'mando': '✈️'}
    
    df['foto'] = df['foto'].str.replace('FORMATO', '140x140')
    df['clube_nome'] = df['clube_id'].apply(lambda x: clubes[str(x)]['nome'])
    df['pos_nome'] = df['posicao_id'].apply(lambda x: posicoes[str(x)]['abreviacao'].upper())
    df['adversario'] = df['clube_id'].apply(lambda x: confrontos_map.get(x, {}).get('vs', 'N/A'))
    df['adv_pos'] = df['clube_id'].apply(lambda x: confrontos_map.get(x, {}).get('vs_pos', 10))
    df['mando'] = df['clube_id'].apply(lambda x: confrontos_map.get(x, {}).get('mando', 'N/A'))
    
    # Extração de Scouts individuais para o Radar
    scouts_list = ['DS', 'G', 'A', 'DE', 'SG', 'FD', 'FF', 'FS']
    for s in scouts_list:
        df[s] = df['scout'].apply(lambda x: x.get(s, 0) if isinstance(x, dict) else 0)

    # Score de Mitada com Peso de Cedência
    def calc_score(row):
        score = (row['media_num'] * 1.5) + (row['G'] * 4) + (row['DS'] * 0.5)
        if row['mando'] == '🏠': score *= 1.1
        if row['adv_pos'] >= 17: score *= 1.2 # Bônus contra Z4
        return round(score, 2)

    df['score_mitada'] = df.apply(calc_score, axis=1)
    return df, partidas_raw['partidas']

# --- UI PRINCIPAL ---
def main():
    st.title("🛡️ MITAR-BOT PRO | Inteligência Analítica")
    
    mercado, partidas_raw = get_all_data()
    if not mercado: return

    df, partidas = process_data(mercado, partidas_raw)
    df_prov = df[df['status_id'] == 7]

    # --- SISTEMA DE ABAS ---
    tab1, tab2, tab3 = st.tabs(["📋 Escalação Ideal", "📊 Comparador Pro", "🏟️ Mapa de Cedentes"])

    with tab1:
        st.subheader("O Time Matemático para Mitar")
        saldo = st.sidebar.number_input("Saldo:", 122.28)
        # (Aqui entra a lógica de otimização anterior simplificada)
        time = df_prov.sort_values('score_mitada', ascending=False).head(11) # Simplificado p/ exemplo
        st.dataframe(time[['foto', 'pos_nome', 'apelido', 'clube_nome', 'adversario', 'score_mitada']],
                     column_config={"foto": st.column_config.ImageColumn("Foto")}, use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("Comparativo Head-to-Head")
        c1, c2 = st.columns(2)
        with c1:
            p1_name = st.selectbox("Escolha o Jogador 1:", df_prov['apelido'].unique(), index=0)
        with c2:
            p2_name = st.selectbox("Escolha o Jogador 2:", df_prov['apelido'].unique(), index=1)
        
        p1 = df_prov[df_prov['apelido'] == p1_name].iloc[0]
        p2 = df_prov[df_prov['apelido'] == p2_name].iloc[0]

        # Gráfico Radar
        categories = ['Gols', 'Assists', 'Desarmes', 'Finalizações', 'Faltas Sofridas']
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=[p1['G'], p1['A'], p1['DS'], p1['FD']+p1['FF'], p1['FS']], theta=categories, fill='toself', name=p1_name))
        fig.add_trace(go.Scatterpolar(r=[p2['G'], p2['A'], p2['DS'], p2['FD']+p2['FF'], p2['FS']], theta=categories, fill='toself', name=p2_name))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True)), showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("Radar de Fragilidade (Adversários)")
        df_cedentes = pd.DataFrame([
            {'Time': mercado['clubes'][str(p['clube_casa_id'])]['nome'], 'Posição': p['clube_casa_posicao'], 'Status': 'Cedente' if p['clube_casa_posicao'] > 15 else 'Estável'}
            for p in partidas_raw['partidas']
        ] + [
            {'Time': mercado['clubes'][str(p['clube_visitante_id'])]['nome'], 'Posição': p['clube_visitante_posicao'], 'Status': 'Cedente' if p['clube_visitante_posicao'] > 15 else 'Estável'}
            for p in partidas_raw['partidas']
        ])
        st.table(df_cedentes.sort_values('Posição', ascending=False).head(6))

if __name__ == "__main__": main()
