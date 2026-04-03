import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timezone

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="MITAR-BOT 2026 | Pro Dashboard",
    page_icon="⚽",
    layout="wide"
)

st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 22px; color: #1a73e8; }
    </style>
""", unsafe_allow_html=True)

# ============================================================
# CAMADA DE DADOS
# ============================================================
@st.cache_data(ttl=600)
def get_all_data():
    try:
        mercado  = requests.get("https://api.cartola.globo.com/atletas/mercado").json()
        partidas = requests.get("https://api.cartola.globo.com/partidas").json()
        status   = requests.get("https://api.cartola.globo.com/mercado/status").json()
        return mercado, partidas, status
    except Exception as e:
        st.error(f"Erro na API: {e}")
        return None, None, None

# ============================================================
# CAMADA DE INTELIGÊNCIA
# ============================================================
def process_data(mercado_raw, partidas_raw):
    atletas  = mercado_raw['atletas']
    clubes   = mercado_raw['clubes']
    posicoes = mercado_raw['posicoes']
    df = pd.DataFrame(atletas)

    # Mapeamento de Confrontos
    confrontos_map = {}
    for p in partidas_raw['partidas']:
        c_id  = p['clube_casa_id']
        v_id  = p['clube_visitante_id']
        c_pos = p['clube_casa_posicao']
        v_pos = p['clube_visitante_posicao']
        confrontos_map[c_id] = {'vs': clubes[str(v_id)]['nome'], 'vs_pos': v_pos, 'mando': '🏠 Casa'}
        confrontos_map[v_id] = {'vs': clubes[str(c_id)]['nome'], 'vs_pos': c_pos, 'mando': '✈️ Fora'}

    df['clube_nome'] = df['clube_id'].apply(lambda x: clubes[str(x)]['nome'])
    df['escudo']     = df['clube_id'].apply(lambda x: clubes[str(x)]['escudos']['60x60'])
    df['pos_nome']   = df['posicao_id'].apply(lambda x: posicoes[str(x)]['abreviacao'].upper())
    df['adversario'] = df['clube_id'].apply(lambda x: confrontos_map.get(x, {}).get('vs', 'N/A'))
    df['adv_pos']    = df['clube_id'].apply(lambda x: confrontos_map.get(x, {}).get('vs_pos', 10))
    df['mando']      = df['clube_id'].apply(lambda x: confrontos_map.get(x, {}).get('mando', 'N/A'))
    df['foto']       = df['foto'].str.replace('FORMATO', '140x140', regex=False)

    def get_s(s_dict, key):
        return s_dict.get(key, 0) if isinstance(s_dict, dict) else 0

    for s in ['DS', 'G', 'A', 'DE', 'SG', 'FD', 'FF', 'FS']:
        df[s] = df['scout'].apply(lambda x: get_s(x, s))

    df['meta_pontos'] = (df['preco_num'] * 0.45).round(2)

    def calc_score(row):
        if row['pos_nome'] == 'GOL':
            score = (row['DE'] * 1.5) + (row['media_num'] * 2)
        elif row['pos_nome'] in ['LAT', 'ZAG']:
            score = (row['DS'] * 1.2) + (row['SG'] * 5) + (row['media_num'] * 1.5)
        elif row['pos_nome'] == 'MEI':
            score = (row['DS'] * 1.0) + (row['A'] * 5) + (row['media_num'] * 2)
        elif row['pos_nome'] == 'ATA':
            score = (row['G'] * 8) + (row['FD'] * 1.2) + (row['FF'] * 0.8) + (row['media_num'] * 2)
        elif row['pos_nome'] == 'TEC':
            score = row['media_num'] * 3
        else:
            score = 0

        if row['mando'] == '🏠 Casa':
            score *= 1.10
        if row['adv_pos'] >= 17:
            score *= 1.25
        elif row['adv_pos'] >= 12:
            score *= 1.10

        return round(score, 2)

    df['score_mitada'] = df.apply(calc_score, axis=1)
    return df, partidas_raw['partidas']

# ============================================================
# OTIMIZADOR DE ESCALAÇÃO
# ============================================================
def optimize_team(df_pool, budget, formation):
    configs = {
        "4-3-3": {'GOL': 1, 'LAT': 2, 'ZAG': 2, 'MEI': 3, 'ATA': 3, 'TEC': 1},
        "3-4-3": {'GOL': 1, 'LAT': 0, 'ZAG': 3, 'MEI': 4, 'ATA': 3, 'TEC': 1},
        "4-4-2": {'GOL': 1, 'LAT': 2, 'ZAG': 2, 'MEI': 4, 'ATA': 2, 'TEC': 1}
    }
    config = configs.get(formation, configs["4-3-3"])
    selected = []
    cost = 0.0

    for pos, qtd in config.items():
        if qtd == 0:
            continue
        top = (df_pool[df_pool['pos_nome'] == pos]
               .sort_values('score_mitada', ascending=False)
               .head(qtd))
        for _, row in top.iterrows():
            selected.append(row)
            cost += row['preco_num']

    res_df = pd.DataFrame(selected).reset_index(drop=True)

    max_iter = 50
    iterations = 0
    while cost > budget and iterations < max_iter:
        iterations += 1
        res_df = res_df.sort_values('preco_num', ascending=False).reset_index(drop=True)
        swapped = False
        for i in range(len(res_df)):
            pos   = res_df.loc[i, 'pos_nome']
            price = res_df.loc[i, 'preco_num']

            sub = df_pool[
                (df_pool['pos_nome'] == pos) &
                (df_pool['preco_num'] < price) &
                (~df_pool['atleta_id'].isin(res_df['atleta_id']))
            ].sort_values('score_mitada', ascending=False).head(1)

            if not sub.empty:
                cost = cost - price + sub.iloc[0]['preco_num']
                res_df = res_df.drop(i).reset_index(drop=True)
                res_df = pd.concat([res_df, sub], ignore_index=True)
                swapped = True
                break

        if not swapped:
            break

    return res_df, round(cost, 2)

# ============================================================
# BANCO DE RESERVAS
# ============================================================
def get_bench(df_pool, time_ideal):
    reservas = []
    posicoes_no_time = time_ideal['pos_nome'].unique()
    for pos in ['GOL', 'LAT', 'ZAG', 'MEI', 'ATA']:
        if pos not in posicoes_no_time:
            continue
        min_p = time_ideal[time_ideal['pos_nome'] == pos]['preco_num'].min()
        res = df_pool[
            (df_pool['pos_nome'] == pos) &
            (~df_pool['atleta_id'].isin(time_ideal['atleta_id'])) &
            (df_pool['preco_num'] <= min_p)
        ].sort_values('score_mitada', ascending=False).head(1)
        if not res.empty:
            reservas.append(res.iloc[0])
    return pd.DataFrame(reservas).reset_index(drop=True)

# ============================================================
# STATUS DO MERCADO
# ============================================================
def show_market_status(status_raw):
    st.sidebar.markdown("---")
    st.sidebar.subheader("⏳ Mercado")
    try:
        f = status_raw.get('fechamento', {})
        data_fechamento = datetime(
            f.get('ano', 2026), f.get('mes', 4),
            f.get('dia', 5),   f.get('hora', 18),
            f.get('minuto', 0), tzinfo=timezone.utc
        )
        agora    = datetime.now(timezone.utc)
        restante = data_fechamento - agora
        if restante.total_seconds() > 0:
            horas, rem = divmod(int(restante.total_seconds()), 3600)
            minutos, _ = divmod(rem, 60)
            st.sidebar.success(f"✅ Aberto — Fecha em {horas}h {minutos}min")
        else:
            st.sidebar.error("🚫 MERCADO FECHADO")
    except:
        st.sidebar.info("Status indisponível.")

# ============================================================
# FUNÇÃO PRINCIPAL
# ============================================================
def main():

    # --- SIDEBAR ---
    st.sidebar.title("⚙️ MITAR-BOT CONFIG")
    saldo    = st.sidebar.number_input("💰 Saldo (Cartoletas):", value=122.28, step=1.0)
    formacao = st.sidebar.selectbox("🏟️ Formação:", ["4-3-3", "4-4-2", "3-4-3"])
    min_jog  = st.sidebar.slider("🏃 Mín. de Jogos:", 0, 10, 3)

    if st.sidebar.button("🔄 Atualizar Dados"):
        st.cache_data.clear()
        st.rerun()

    st.title("⚽ MITAR-BOT 2026 | Pro Dashboard")

    # --- DADOS ---
    mercado_raw, partidas_raw, status_raw = get_all_data()
    if not mercado_raw:
        st.stop()

    show_market_status(status_raw)

    df, partidas = process_data(mercado_raw, partidas_raw)
    df_prov = df[(df['status_id'] == 7) & (df['jogos_num'] >= min_jog)]

    time_ideal, custo_final = optimize_team(df_prov, saldo, formacao)
    capitao = time_ideal.sort_values('score_mitada', ascending=False).iloc[0]

    # --- ABAS ---
    tab1, tab2, tab3, tab4 = st.tabs([
        "🏆 Time Ideal",
        "📊 Comparador",
        "🏟️ Cedentes",
        "🚨 Monitor"
    ])

    # ========================
    # ABA 1: TIME IDEAL
    # ========================
    with tab1:
        ca, cb, cc = st.columns([1, 2, 2])
        with ca:
            st.image(capitao['foto'], width=120)
        with cb:
            st.subheader(f"💎 {capitao['apelido']}")
            st.write(f"**Clube:** {capitao['clube_nome']}")
            st.write(f"**vs** {capitao['adversario']} {capitao['mando']}")
            st.write(f"**Meta Valorizar:** {capitao['meta_pontos']} pts")
        with cc:
            st.metric("Média", f"{capitao['media_num']:.2f}")
            st.metric("Score Mitada", f"{capitao['score_mitada']}")
            st.metric("Preço", f"C$ {capitao['preco_num']:.2f}")

        st.markdown("---")
        saldo_restante = round(saldo - custo_final, 2)
        st.subheader(f"Escalação {formacao} — C$ {custo_final:.2f} | Sobra: C$ {saldo_restante}")

        st.dataframe(
            time_ideal[[
                'foto', 'pos_nome', 'apelido', 'escudo',
                'adversario', 'mando', 'media_num',
                'meta_pontos', 'score_mitada', 'preco_num'
            ]],
            column_config={
                "foto":         st.column_config.ImageColumn("Atleta"),
                "escudo":       st.column_config.ImageColumn("Clube"),
                "pos_nome":     "Pos",
                "apelido":      "Jogador",
                "adversario":   "Adversário",
                "mando":        "Mando",
                "media_num":    "Média",
                "meta_pontos":  "Meta Val.",
                "score_mitada": st.column_config.ProgressColumn("Score Mitada", min_value=0, max_value=100),
                "preco_num":    "C$"
            },
            use_container_width=True,
            hide_index=True
        )

        st.markdown("---")
        st.subheader("🔄 Banco de Reservas")
        bench = get_bench(df_prov, time_ideal)
        if not bench.empty:
            st.dataframe(
                bench[['pos_nome', 'apelido', 'clube_nome', 'preco_num', 'score_mitada']],
                column_config={
                    "pos_nome":     "Pos",
                    "apelido":      "Reserva",
                    "clube_nome":   "Clube",
                    "preco_num":    "C$",
                    "score_mitada": "Score"
                },
                use_container_width=True,
                hide_index=True
            )

    # ========================
    # ABA 2: COMPARADOR
    # ========================
    with tab2:
        st.subheader("📊 Comparador Head-to-Head")
        c1, c2 = st.columns(2)
        with c1:
            p1_nome
