import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="MITAR-BOT 2026 | Analisador Cartola FC",
    page_icon="⚽",
    layout="wide"
)

# --- ESTILIZAÇÃO CUSTOMIZADA ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- CAMADA DE DADOS (INGESTION) ---
@st.cache_data(ttl=600)
def get_all_data():
    try:
        mercado_url = "https://api.cartola.globo.com/atletas/mercado"
        partidas_url = "https://api.cartola.globo.com/partidas"
        
        mercado_res = requests.get(mercado_url).json()
        partidas_res = requests.get(partidas_url).json()
        
        return mercado_res, partidas_res
    except Exception as e:
        st.error(f"⚠️ Erro ao conectar com a API do Cartola: {e}")
        return None, None

# --- CAMADA DE INTELIGÊNCIA (SCOUTING & VALORIZAÇÃO) ---
def process_scouting(mercado_raw, partidas_raw):
    atletas = mercado_raw['atletas']
    clubes = mercado_raw['clubes']
    posicoes = mercado_raw['posicoes']
    df = pd.DataFrame(atletas)
    
    # Mapeamentos
    df['clube_nome'] = df['clube_id'].apply(lambda x: clubes[str(x)]['nome'])
    df['pos_nome'] = df['posicao_id'].apply(lambda x: posicoes[str(x)]['abreviacao'].upper())
    
    # Identificar Mandantes
    mandantes = [p['clube_casa_id'] for p in partidas_raw['partidas']]
    df['mando'] = df['clube_id'].apply(lambda x: "🏠 Casa" if x in mandantes else "✈️ Fora")
    
    # Extração de Scouts individuais
    def get_s(s_dict, key): return s_dict.get(key, 0) if isinstance(s_dict, dict) else 0
    
    df['DS'] = df['scout'].apply(lambda x: get_s(x, 'DS'))
    df['G'] = df['scout'].apply(lambda x: get_s(x, 'G'))
    df['A'] = df['scout'].apply(lambda x: get_s(x, 'A'))
    df['DE'] = df['scout'].apply(lambda x: get_s(x, 'DE'))
    df['SG'] = df['scout'].apply(lambda x: get_s(x, 'SG'))
    df['FD'] = df['scout'].apply(lambda x: get_s(x, 'FD'))
    df['FF'] = df['scout'].apply(lambda x: get_s(x, 'FF'))

    # Cálculo: Mínimo para Valorizar (Heurística Cartola)
    df['min_para_valorizar'] = (df['preco_num'] * 0.42).round(2)
    
    # Score Técnico por Posição (Pesos de Especialista)
    def calculate_tech_score(row):
        score = 0
        if row['pos_nome'] == 'GOL':
            score = (row['DE'] * 1.5) + (row['media_num'] * 2)
        elif row['pos_nome'] in ['LAT', 'ZAG']:
            score = (row['DS'] * 1.2) + (row['SG'] * 5.0) + (row['media_num'] * 1.5)
        elif row['pos_nome'] == 'MEI':
            score = (row['DS'] * 1.0) + (row['A'] * 5.0) + (row['media_num'] * 2)
        elif row['pos_nome'] == 'ATA':
            score = (row['G'] * 8.0) + (row['FD'] * 1.2) + (row['FF'] * 0.8) + (row['media_num'] * 2)
        elif row['pos_nome'] == 'TEC':
            score = (row['media_num'] * 3)
            
        if row['mando'] == "🏠 Casa": score *= 1.15 # Bônus mandante
        return round(score, 2)

    df['score_mitada'] = df.apply(calculate_tech_score, axis=1)
    return df, partidas_raw['partidas'], clubes

# --- OTIMIZADOR DE ESCALAÇÃO ---
def optimize_team(df_pool, budget, formation):
    configs = {
        "4-3-3": {'GOL': 1, 'LAT': 2, 'ZAG': 2, 'MEI': 3, 'ATA': 3, 'TEC': 1},
        "3-4-3": {'GOL': 1, 'LAT': 0, 'ZAG': 3, 'MEI': 4, 'ATA': 3, 'TEC': 1},
        "4-4-2": {'GOL': 1, 'LAT': 2, 'ZAG': 2, 'MEI': 4, 'ATA': 2, 'TEC': 1}
    }
    config = configs[formation]
    
    selected = []
    current_cost = 0
    
    for pos, qtd in config.items():
        top_pos = df_pool[df_pool['pos_nome'] == pos].sort_values('score_mitada', ascending=False).head(qtd)
        for _, row in top_pos.iterrows():
            selected.append(row)
            current_cost += row['preco_num']
            
    selected_df = pd.DataFrame(selected)
    while current_cost > budget:
        selected_df = selected_df.sort_values('preco_num', ascending=False)
        for i in range(len(selected_df)):
            idx = selected_df.index[i]
            pos_to_swap = selected_df.loc[idx, 'pos_nome']
            price_to_beat = selected_df.loc[idx, 'preco_num']
            
            sub = df_pool[(df_pool['pos_nome'] == pos_to_swap) & 
                          (df_pool['preco_num'] < price_to_beat) &
                          (~df_pool['atleta_id'].isin(selected_df['atleta_id']))].head(1)
            
            if not sub.empty:
                current_cost -= price_to_beat
                current_cost += sub.iloc[0]['preco_num']
                selected_df = selected_df.drop(idx)
                selected_df = pd.concat([selected_df, sub])
                break
        else: break
            
    return selected_df, round(current_cost, 2)

# --- APP PRINCIPAL ---
def main():
    st.sidebar.title("🛠️ MITADA CONFIG")
    
    saldo_disp = st.sidebar.number_input("💰 Saldo Disponível:", value=122.28, step=1.0)
    escolha_formacao = st.sidebar.selectbox("🏟️ Formação:", ["4-3-3", "3-4-3", "4-4-2"])
    min_jogos = st.sidebar.slider("🏃 Mín. de Jogos:", 0, 10, 3)
    
    st.title("⚽ MITAR-BOT 2026")
    st.caption("Estatísticas Oficiais da API Cartola FC")

    mercado_raw, partidas_raw = get_all_data()
    
    if mercado_raw:
        df, partidas, clubes_map = process_scouting(mercado_raw, partidas_raw)
        df_prov = df[(df['status_id'] == 7) & (df['jogos_num'] >= min_jogos)]
        
        # --- SEÇÃO 1: TIME IDEAL ---
        st.header("🏆 Escalação Recomendada")
        time_ideal, custo_final = optimize_team(df_prov, saldo_disp, escolha_formacao)
        
        col_t1, col_t2 = st.columns([2, 1])
        
        with col_t1:
            st.dataframe(time_ideal[['pos_nome', 'apelido', 'clube_nome', 'mando', 'media_num', 'preco_num', 'score_mitada']], 
                         use_container_width=True, hide_index=True)
        
        with col_t2:
            st.metric("Custo Total", f"C$ {custo_final:.2f}", f"{saldo_disp - custo_final:.2f} sobra")
            capitao = time_ideal.sort_values('score_mitada', ascending=False).iloc[0]
            st.success(f"💎 **Capitão:** {capitao['apelido']}")

        # --- SEÇÃO 2: BANCO DE RESERVAS ---
        st.markdown("---")
        st.subheader("🔄 Banco de Reservas (Custo Mínimo)")
        
        reservas = []
        posicoes_no_time = time_ideal['pos_nome'].unique() # CORREÇÃO AQUI
        
        for pos in ['GOL', 'LAT', 'ZAG', 'MEI', 'ATA']:
            if pos in posicoes_no_time:
                min_p = time_ideal[time_ideal['pos_nome'] == pos]['preco_num'].min()
                res = df_prov[(df_prov['pos_nome'] == pos) & 
                              (~df_prov['atleta_id'].isin(time_ideal['atleta_id'])) &
                              (df_prov['preco_num'] <= min_p)].sort_values('score_mitada', ascending=False).head(1)
                if not res.empty: 
                    reservas.append(res.iloc[0])
        
        if reservas:
            st.table(pd.DataFrame(reservas)[['pos_nome', 'apelido', 'clube_nome', 'preco_num']])

        # --- SEÇÃO 3: ANÁLISES EXTRAS ---
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📈 Top Valorização")
            top_val = df_prov.sort_values('min_para_valorizar').head(5)
            st.dataframe(top_val[['apelido', 'preco_num', 'min_para_valorizar']], hide_index=True)
        with c2:
            st.subheader("🎯 Gráfico de Desempenho")
            fig = px.scatter(df_prov[df_prov['pos_nome'] == 'ATA'].head(15), x="media_num", y="score_mitada", text="apelido")
            st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
