import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MITAR-BOT 2026 | Pro Dashboard", page_icon="📈", layout="wide")

# --- CSS PARA ESTILIZAÇÃO ---
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 24px; color: #00acee; }
    .stDataFrame { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

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
def process_scouting(mercado_raw, partidas_raw):
    atletas = mercado_raw['atletas']
    clubes = mercado_raw['clubes']
    posicoes = mercado_raw['posicoes']
    df = pd.DataFrame(atletas)
    
    # Mapeamento de Confrontos
    confrontos_map = {}
    for p in partidas_raw['partidas']:
        c_id, v_id = p['clube_casa_id'], p['clube_visitante_id']
        confrontos_map[c_id] = {'vs': clubes[str(v_id)]['nome'], 'vs_escudo': clubes[str(v_id)]['escudos']['30x30'], 'mando': '🏠'}
        confrontos_map[v_id] = {'vs': clubes[str(c_id)]['nome'], 'vs_escudo': clubes[str(c_id)]['escudos']['30x30'], 'mando': '✈️'}
    
    # Tratamento de Fotos e Escudos
    df['foto'] = df['foto'].str.replace('FORMATO', '140x140')
    df['escudo'] = df['clube_id'].apply(lambda x: clubes[str(x)]['escudos']['60x60'])
    df['clube_nome'] = df['clube_id'].apply(lambda x: clubes[str(x)]['nome'])
    df['pos_nome'] = df['posicao_id'].apply(lambda x: posicoes[str(x)]['abreviacao'].upper())
    df['adversario'] = df['clube_id'].apply(lambda x: confrontos_map.get(x, {}).get('vs', 'N/A'))
    df['mando'] = df['clube_id'].apply(lambda x: confrontos_map.get(x, {}).get('mando', 'N/A'))
    
    # Cálculo de Valorização (Heurística: Meta de 45% do preço)
    df['meta_pontos'] = (df['preco_num'] * 0.45).round(2)
    
    # Inteligência de Score
    def calc_score(row):
        score = (row['media_num'] * 2)
        if row['pos_nome'] == 'ATA': score += (row['scout'].get('G', 0) * 8)
        if row['mando'] == '🏠': score *= 1.15
        return round(score, 2)

    df['score_mitada'] = df.apply(calc_score, axis=1)
    return df

# --- OTIMIZADOR ---
def optimize_team(df_pool, budget, formation):
    cfg = {"4-3-3": {'GOL': 1, 'LAT': 2, 'ZAG': 2, 'MEI': 3, 'ATA': 3, 'TEC': 1},
           "3-4-3": {'GOL': 1, 'LAT': 0, 'ZAG': 3, 'MEI': 4, 'ATA': 3, 'TEC': 1}}[formation]
    selected = []
    cost = 0
    for pos, qtd in cfg.items():
        top = df_pool[df_pool['pos_nome'] == pos].sort_values('score_mitada', ascending=False).head(qtd)
        for _, row in top.iterrows():
            selected.append(row)
            cost += row['preco_num']
    
    res_df = pd.DataFrame(selected)
    # Algoritmo de ajuste de orçamento (simplificado para o exemplo)
    while cost > budget:
        res_df = res_df.sort_values('preco_num', ascending=False)
        idx = res_df.index[0]
        pos, price = res_df.loc[idx, 'pos_nome'], res_df.loc[idx, 'preco_num']
        sub = df_pool[(df_pool['pos_nome'] == pos) & (df_pool['preco_num'] < price) & (~df_pool['atleta_id'].isin(res_df['atleta_id']))].head(1)
        if not sub.empty:
            cost = cost - price + sub.iloc[0]['preco_num']
            res_df = pd.concat([res_df.drop(idx), sub])
        else: break
    return res_df, round(cost, 2)

# --- UI PRINCIPAL ---
def main():
    st.title("📈 MITAR-BOT PRO | Dashboard de Scouting")
    
    saldo = st.sidebar.slider("Orçamento Disponível", 80.0, 300.0, 122.28)
    form = st.sidebar.selectbox("Esquema Tático", ["4-3-3", "3-4-3"])
    
    mercado, partidas = get_all_data()
    if mercado:
        df = process_scouting(mercado, partidas)
        df_prov = df[df['status_id'] == 7]
        
        # 💎 DESTAQUE DO CAPITÃO
        time, custo = optimize_team(df_prov, saldo, form)
        cap = time.sort_values('score_mitada', ascending=False).iloc[0]
        
        with st.container():
            c1, c2, c3 = st.columns([1, 2, 2])
            with c1: st.image(cap['foto'], caption="Capitão Sugerido")
            with c2:
                st.subheader(f"💎 {cap['apelido']}")
                st.write(f"**Time:** {cap['clube_nome']} | **Média:** {cap['media_num']}")
                st.write(f"**Meta para Valorizar:** {cap['meta_pontos']} pts")
            with c3:
                st.metric("Score de Mitada", f"{cap['score_mitada']} pts", "Top 1% da Rodada")

        st.markdown("---")
        
        # 🏆 TABELA VISUAL DO TIME
        st.subheader(f"🏃 Escalação Ideal ({form}) - Custo C$ {custo}")
        
        st.dataframe(
            time[['foto', 'pos_nome', 'apelido', 'escudo', 'adversario', 'mando', 'media_num', 'meta_pontos', 'score_mitada']],
            column_config={
                "foto": st.column_config.ImageColumn("Foto"),
                "escudo": st.column_config.ImageColumn("Clube"),
                "score_mitada": st.column_config.ProgressColumn("Poder de Mitada", min_value=0, max_value=50),
                "media_num": "Média",
                "meta_pontos": "Meta Valoriz."
            },
            use_container_width=True,
            hide_index=True
        )

        # 📊 INSIGHTS DE VALORIZAÇÃO
        st.markdown("---")
        st.subheader("💰 Oportunidades de Valorização")
        st.write("Jogadores que precisam de pontuações baixas para aumentar o seu patrimônio.")
        top_val = df_prov.sort_values('meta_pontos').head(10)
        st.dataframe(top_val[['foto', 'apelido', 'clube_nome', 'preco_num', 'meta_pontos']], 
                     column_config={"foto": st.column_config.ImageColumn("Foto")}, 
                     hide_index=True, use_container_width=True)

if __name__ == "__main__": main()
