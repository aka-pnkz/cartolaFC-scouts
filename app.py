# app.py
import streamlit as st
import pandas as pd
import requests
from utils.api import fetch_mercado, fetch_ligas_status
from utils.score_mitada import enriquecer_df
from utils.confrontos import get_confrontos_df
from utils.alertas import gerar_alertas, resumo_alertas

st.set_page_config(
    page_title="Cartola FC Analyzer 2026",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS Dark Theme ────────────────────────────────────────────────
st.markdown("""
<style>
body, .stApp { background-color: #0e1117; color: #fafafa; }
.metric-card {
    background: #1c1f26; border-radius: 10px;
    padding: 16px; text-align: center;
    border: 1px solid #2d3139; margin: 4px;
}
.metric-card h3 { font-size: 2rem; margin: 0; }
.metric-card p  { color: #888; margin: 0; font-size: 0.85rem; }
.alerta-danger  { background:#3d1010; border-left:4px solid #e63946;
                  padding:8px 12px; border-radius:6px; margin:4px 0; }
.alerta-warning { background:#3d2e10; border-left:4px solid #f4a261;
                  padding:8px 12px; border-radius:6px; margin:4px 0; }
.alerta-info    { background:#0d2137; border-left:4px solid #2196f3;
                  padding:8px 12px; border-radius:6px; margin:4px 0; }
table { width:100% !important; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://s.glbimg.com/es/sde/f/2024/02/19/cartola-fc.png", width=160)
    st.markdown("## ⚽ Cartola FC Analyzer")
    st.markdown("**Rodada 10 — Temporada 2026**")
    st.divider()

    orcamento = st.number_input(
        "💰 Orçamento (C$)", min_value=0.0, max_value=200.0,
        value=122.28, step=0.01, format="%.2f"
    )
    formacao = st.selectbox(
        "📐 Formação", ["4-3-3","4-4-2","3-5-2","3-4-3","4-5-1","5-3-2","5-4-1"],
        index=0
    )
    modo = st.selectbox(
        "🎯 Modo", ["equilibrado","agressivo","defensivo","valorizacao"],
        format_func=lambda x: {
            "equilibrado": "⚖️ Equilibrado",
            "agressivo":   "🔥 Agressivo",
            "defensivo":   "🛡️ Defensivo",
            "valorizacao": "📈 Valorização",
        }[x]
    )
    apenas_provaveis = st.checkbox("✅ Apenas Prováveis", value=True)
    variacao_pos     = st.checkbox("📈 Variação Positiva", value=True)
    min_jogos        = st.slider("🎮 Mínimo de Jogos", 0, 10, 3)

    st.divider()
    if st.button("🔄 Atualizar Dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.caption("Dados: api.cartola.globo.com")

# ── Carrega dados ─────────────────────────────────────────────────
@st.cache_data(ttl=300)
def carregar_dados():
    data = fetch_mercado()
    atletas_raw = list(data.get("atletas", {}).values())
    clubes_raw  = data.get("clubes", {})
    # Injeta abreviação do clube
    for a in atletas_raw:
        cid = str(a.get("clube_id", ""))
        a["_clube_abrev"] = clubes_raw.get(cid, {}).get("abreviacao", cid)
    return atletas_raw

atletas_raw = carregar_dados()
df_full     = enriquecer_df(atletas_raw)

# ── Filtros ───────────────────────────────────────────────────────
df = df_full.copy()
if apenas_provaveis:
    df = df[df["status_id"].isin([1, 7])]
if variacao_pos:
    df = df[df["variacao_num"] >= 0]
if min_jogos > 0:
    df = df[df["jogos_num"] >= min_jogos]

# ── Header ────────────────────────────────────────────────────────
st.markdown("# ⚽ Cartola FC Analyzer — Rodada 10")
st.markdown(f"**Mercado:** {'🟢 Aberto' if True else '🔴 Fechado'} &nbsp;|&nbsp; "
            f"**Jogadores filtrados:** {len(df)} &nbsp;|&nbsp; "
            f"**Orçamento:** C$ {orcamento:.2f}")
st.divider()

# ── KPIs ──────────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)
kpis = [
    (col1, "🏆 Top Score Mitada", f"{df['Score Mitada'].max():.3f}" if not df.empty else "N/A"),
    (col2, "📊 Maior Média",      f"{df['Média'].max():.1f} pts"    if not df.empty else "N/A"),
    (col3, "💰 Mais Barato",      f"C$ {df['Preço'].min():.2f}"     if not df.empty else "N/A"),
    (col4, "📈 Maior Variação",   f"C$ {df['Variação'].max():+.2f}" if not df.empty else "N/A"),
    (col5, "✅ Prováveis",        str(len(df[df["status_id"].isin([1,7])]))),
]
for col, label, valor in kpis:
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <p>{label}</p>
            <h3>{valor}</h3>
        </div>""", unsafe_allow_html=True)

st.divider()

# ── Tabs principais ───────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🏠 Confrontos R10",
    "🏅 Top por Posição",
    "⚠️ Alertas",
    "📋 Mercado Completo",
])

# ── TAB 1: Confrontos ─────────────────────────────────────────────
with tab1:
    st.subheader("📅 Confrontos da Rodada 10")
    df_conf = get_confrontos_df()
    st.dataframe(df_conf, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("### 🔍 Análise por Clube")
    clubes_lista = sorted(df["Adversário"].dropna().unique().tolist())
    clube_sel    = st.selectbox("Selecione um clube", sorted(df["Nome"].dropna().unique().tolist())[:20])
    if clube_sel:
        row = df[df["Nome"] == clube_sel]
        if not row.empty:
            r = row.iloc[0]
            c1, c2, c3 = st.columns(3)
            c1.metric("Mando",     r.get("Mando","?"))
            c2.metric("Adversário",r.get("Adversário","?"))
            c3.metric("Favorito",  r.get("Favorito","?"))
            c1.metric("Aprov.%",   f"{r.get('Aprov.%',0):.1f}%")
            c2.metric("AprovAdv.%",f"{r.get('AprovAdv.%',0):.1f}%")
            c3.metric("Data",      r.get("Data Jogo","?"))

# ── TAB 2: Top por Posição ────────────────────────────────────────
with tab2:
    st.subheader("🏅 Melhores por Posição — Score Mitada")
    posicoes = ["Goleiro","Lateral","Zagueiro","Meia","Atacante","Técnico"]
    cols_show = ["Nome","Status","Preço","Média","Variação","CB",
                 "Score Mitada","Mando","Adversário","Favorito","Scouts"]

    for pos in posicoes:
        subset = df[df["Posição"] == pos].copy()
        if subset.empty:
            continue
        subset = subset.sort_values("Score Mitada", ascending=False).head(8)
        cols_ok = [c for c in cols_show if c in subset.columns]

        emoji = {"Goleiro":"🧤","Lateral":"🛡️","Zagueiro":"🛡️",
                 "Meia":"🎯","Atacante":"⚡","Técnico":"📋"}.get(pos,"")
        with st.expander(f"{emoji} {pos} — Top {len(subset)}", expanded=(pos=="Atacante")):
            st.dataframe(
                subset[cols_ok].reset_index(drop=True),
                use_container_width=True, hide_index=True,
            )

# ── TAB 3: Alertas ────────────────────────────────────────────────
with tab3:
    st.subheader("⚠️ Dashboard de Alertas")

    alertas = gerar_alertas(df)
    res     = resumo_alertas(alertas)

    a1, a2, a3, a4 = st.columns(4)
    a1.metric("🔴 Danger",  res["danger"])
    a2.metric("🟡 Warning", res["warning"])
    a3.metric("🔵 Info",    res["info"])
    a4.metric("📊 Total",   res["total"])
    st.divider()

    filtro_nivel = st.multiselect(
        "Filtrar por nível",
        ["danger","warning","info"],
        default=["danger","warning"],
    )
    filtro_tipo = st.multiselect(
        "Filtrar por tipo",
        sorted(set(a["tipo"] for a in alertas)),
        default=[],
    )

    for alerta in alertas:
        if alerta["nivel"] not in filtro_nivel:
            continue
        if filtro_tipo and alerta["tipo"] not in filtro_tipo:
            continue
        css_class = f"alerta-{alerta['nivel']}"
        st.markdown(
            f'<div class="{css_class}">'
            f'<strong>[{alerta["tipo"]}] {alerta["jogador"]}</strong>'
            f' — {alerta["mensagem"]}'
            f'</div>',
            unsafe_allow_html=True
        )

# ── TAB 4: Mercado Completo ───────────────────────────────────────
with tab4:
    st.subheader("📋 Mercado Completo — Filtros Avançados")

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        pos_filtro = st.multiselect("Posição", ["Goleiro","Lateral","Zagueiro","Meia","Atacante","Técnico"])
    with col_f2:
        preco_max  = st.slider("Preço máximo (C$)", 0.0, 50.0, float(orcamento), 0.5)
    with col_f3:
        mando_fil  = st.multiselect("Mando", ["🏠 Casa","✈️ Fora"])

    df_mercado = df.copy()
    if pos_filtro:
        df_mercado = df_mercado[df_mercado["Posição"].isin(pos_filtro)]
    df_mercado = df_mercado[df_mercado["Preço"] <= preco_max]
    if mando_fil:
        df_mercado = df_mercado[df_mercado["Mando"].isin(mando_fil)]

    cols_mercado = ["Nome","Posição","Status","Preço","Média","Variação",
                    "CB","Score Mitada","Mando","Adversário","Favorito","Jogos","Scouts"]
    cols_ok = [c for c in cols_mercado if c in df_mercado.columns]

    st.dataframe(
        df_mercado[cols_ok].reset_index(drop=True),
        use_container_width=True, hide_index=True,
    )
    st.caption(f"Exibindo {len(df_mercado)} jogadores")
