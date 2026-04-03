import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MITAR-BOT 2026 | Inteligência de Cedência", page_icon="🎯", layout="wide")

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

# --- CAMADA DE INTELIGÊNCIA (VARRENDO PARTIDAS) ---
def process_scouting(mercado_raw, partidas_raw):
    atletas = mercado_raw['atletas']
    clubes = mercado_raw['clubes']
    posicoes = mercado_raw['posicoes']
    df = pd.DataFrame(atletas)
    
    # 1. MAPEAMENTO DE CONFRONTOS (VARRENDO PARTIDAS)
    confrontos_map = {}
    for p in partidas_raw['partidas']:
        c_id, v_id = p['clube_casa_id'], p['clube_visitante_id']
        c_pos, v_pos = p['clube_casa_posicao'], p['clube_visitante_posicao']
        
        # Cada time mapeia seu adversário e a periculosidade dele
        confrontos_map[c_id] = {'vs': clubes[str(v_id)]['nome'], 'vs_pos': v_pos, 'mando': '🏠 Casa'}
        confrontos_map[v_id] = {'vs': clubes[str(c_id)]['nome'], 'vs_pos': c_pos, 'mando': '✈️ Fora'}
    
    # Aplicar Mapeamento
    df['clube_nome'] = df['clube_id'].apply(lambda x: clubes[str(x)]['nome'])
    df['pos_nome'] = df['posicao_id'].apply(lambda x: posicoes[str(x)]['abreviacao'].upper())
    df['adversario'] = df['clube_id'].apply(lambda x: confrontos_map.get(x, {}).get('vs', 'N/A'))
    df['adv_pos'] = df['clube_id'].apply(lambda x: confrontos_map.get(x, {}).get('vs_pos', 10))
    df['mando'] = df['clube_id'].apply(lambda x: confrontos_map.get(x, {}).get('mando', 'N/A'))
    
    # Extração de Scouts
    def get_s(s_dict, key): return s_dict.get(key, 0) if isinstance(s_dict, dict) else 0
    for s in ['DS', 'G', 'A', 'DE', 'SG', 'FD', 'FF']:
        df[s] = df['scout'].apply(lambda x: get_s(x, s))

    # Score Técnico com LOGICA DE CEDÊNCIA
    def calculate_tech_score(row):
        # Base de pontos por posição
        if row['pos_nome'] == 'GOL': score = (row['DE'] * 1.5) + (row['media_num'] * 2)
        elif row['pos_nome'] in ['LAT', 'ZAG']: score = (row['DS'] * 1.2) + (row['SG'] * 5.0) + (row['media_num'] * 1.5)
        elif row['pos_nome'] == 'MEI': score = (row['DS'] * 1.0) + (row['A'] * 5.0) + (row['media_num'] * 2)
        elif row['pos_nome'] == 'ATA': score = (row['G'] * 8.0) + (row['FD'] * 1.2) + (row['FF'] * 0.8) + (row['media_num'] * 2)
        else: score = row['media_num'] * 3
            
        # AJUSTE DE CONTEXTO (A varredura das partidas influencia aqui)
        if row['mando'] == "🏠 Casa": score *= 1.10 # +10% por jogar em casa
        
        # BÔNUS DE CEDÊNCIA: Adversário é fraco?
        if row['adv_pos'] >= 17: score *= 1.25 # +25% contra times do Z4
        elif row['adv_pos'] >= 12: score *= 1.10 # +10% contra times da parte de baixo
            
        return round(score, 2)

    df['score_mitada'] = df.apply(calculate_tech_score, axis=1)
    return df, partidas_raw['partidas']

# --- OTIMIZADOR ---
def optimize_team(df_pool, budget, formation):
    cfg = {"4-3-3": {'GOL': 1, 'LAT': 2, 'ZAG': 2, 'MEI': 3, 'ATA': 3, 'TEC': 1},
           "3-4-3": {'GOL': 1, 'LAT': 0, 'ZAG': 3, 'MEI': 4, 'ATA': 3, 'TEC': 1},
           "4-4-2": {'GOL': 1, 'LAT': 2, 'ZAG': 2, 'MEI': 4, 'ATA': 2, 'TEC': 1}}[formation]
    selected = []
    cost = 0
    for pos, qtd in cfg.items():
        top = df_pool[df_pool['pos_nome'] == pos].sort_values('score_mitada', ascending=False).head(qtd)
        for _, row in top.iterrows():
            selected.append(row)
            cost += row['preco_num']
    
    res_df = pd.DataFrame(selected)
    while cost > budget:
        res_df = res_df.sort_values('preco_num', ascending=False)
        for i in range(len(res_df)):
            idx = res_df.index[i]
            pos, price = res_df.loc[idx, 'pos_nome'], res_df.loc[idx, 'preco_num']
            sub = df_pool[(df_pool['pos_nome'] == pos) & (df_pool['preco_num'] < price) & (~df_pool['atleta_id'].isin(res_df['atleta_id']))].head(1)
            if not sub.empty:
                cost = cost - price + sub.iloc[0]['preco_num']
                res_df = pd.concat([res_df.drop(idx), sub])
                break
        else: break
    return res_df, round(cost, 2)

# --- UI ---
def main():
    st.title("🎯 MITAR-BOT 2026 | Inteligência de Cedência")
    saldo = st.sidebar.number_input("Cartoletas:", 122.28)
    form = st.sidebar.selectbox("Formação:", ["4-3-3", "3-4-3", "4-4-2"])
    
    mercado, partidas_raw = get_all_data()
    if mercado:
        df, partidas = process_scouting(mercado, partidas_raw)
        df_prov = df[df['status_id'] == 7]
        
        # 🏆 TIME SUGERIDO
        time, custo = optimize_team(df_prov, saldo, form)
        st.subheader(f"Escalação Ideal (Custo: C$ {custo})")
        st.dataframe(time[['pos_nome', 'apelido', 'clube_nome', 'adversario', 'mando', 'media_num', 'score_mitada']], 
                     use_container_width=True, hide_index=True)
        
        # 🎯 RADAR DE "SACOS DE PANCADA"
        st.markdown("---")
        st.subheader("🔥 Alvos da Rodada (Times que cedem pontos)")
        st.write("Jogadores que enfrentam esses times ganharam bônus no Score de Mitada.")
        cols = st.columns(4)
        z4_times = sorted(partidas_raw['partidas'], key=lambda x: max(x['clube_casa_posicao'], x['clube_visitante_posicao']), reverse=True)[:4]
        for i, p in enumerate(z4_times):
            pior_time = mercado['clubes'][str(p['clube_casa_id'])]['nome'] if p['clube_casa_posicao'] > p['clube_visitante_posicao'] else mercado['clubes'][str(p['clube_visitante_id'])]['nome']
            cols[i].metric("Saco de Pancada", pior_time, f"Pos: {max(p['clube_casa_posicao'], p['clube_visitante_posicao'])}")

if __name__ == "__main__": main()
