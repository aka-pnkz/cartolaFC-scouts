import pandas as pd
from itertools import combinations
from utils.scouts import calcular_pontuacao_estimada, calcular_custo_beneficio

FORMACOES_VALIDAS = {
    "4-3-3": {"Goleiro": 1, "Lateral": 2, "Zagueiro": 2, "Meia": 3, "Atacante": 3, "Técnico": 1},
    "4-4-2": {"Goleiro": 1, "Lateral": 2, "Zagueiro": 2, "Meia": 4, "Atacante": 2, "Técnico": 1},
    "3-5-2": {"Goleiro": 1, "Lateral": 1, "Zagueiro": 3, "Meia": 4, "Atacante": 2, "Técnico": 1},
    "3-4-3": {"Goleiro": 1, "Lateral": 1, "Zagueiro": 3, "Meia": 3, "Atacante": 3, "Técnico": 1},
    "4-5-1": {"Goleiro": 1, "Lateral": 2, "Zagueiro": 2, "Meia": 5, "Atacante": 1, "Técnico": 1},
    "5-3-2": {"Goleiro": 1, "Lateral": 2, "Zagueiro": 3, "Meia": 3, "Atacante": 2, "Técnico": 1},
    "5-4-1": {"Goleiro": 1, "Lateral": 2, "Zagueiro": 3, "Meia": 4, "Atacante": 1, "Técnico": 1},
}

POSICAO_MAP = {1: "Goleiro", 2: "Lateral", 3: "Zagueiro", 4: "Meia", 5: "Atacante", 6: "Técnico"}

def filtrar_jogadores(df, status_filter=None, variacao_positiva=True, min_jogos=3):
    """Filtra jogadores por critérios básicos."""
    if df.empty:
        return df
    
    mask = pd.Series([True] * len(df), index=df.index)
    
    if status_filter:
        mask = mask & (df["status_id"].isin(status_filter))
    
    if variacao_positiva:
        mask = mask & (df["variacao_num"] >= 0)
    
    if min_jogos > 0:
        mask = mask & (df["jogos_num"] >= min_jogos)
    
    return df[mask].copy()

def otimizar_escalacao(df, formacao, orcamento, modo="equilibrado", clubes_confronto=None):
    """
    Otimiza escalação dentro do orçamento para a formação dada.
    Modos: equilibrado, agressivo, defensivo, valorizacao
    """
    if df.empty:
        return pd.DataFrame()
    
    schema = FORMACOES_VALIDAS.get(formacao)
    if not schema:
        return pd.DataFrame()
    
    # Define métrica de ordenação por modo
    if modo == "agressivo":
        df = df.copy()
        df["score_mode"] = df["media_num"] * 1.3 + df["variacao_num"] * 0.5
    elif modo == "defensivo":
        df = df.copy()
        df["score_mode"] = df["media_num"] * 1.0 - df["variacao_num"].abs() * 0.3
    elif modo == "valorizacao":
        df = df.copy()
        df["score_mode"] = df["variacao_num"] * 2 + df.get("cb_ratio", 0) * 0.5
    else:  # equilibrado
        df = df.copy()
        df["score_mode"] = df["media_num"] + df["variacao_num"] * 0.3 + df.get("cb_ratio", 0) * 0.2
    
    # Filtra por clubes em confronto (se informado)
    if clubes_confronto:
        df_filtrado = df[df["clube_id"].isin(clubes_confronto)]
        if len(df_filtrado) < 5:
            df_filtrado = df
    else:
        df_filtrado = df
    
    escalacao = []
    total_preco = 0.0
    
    for posicao_nome, qtd in schema.items():
        pos_id = {v: k for k, v in POSICAO_MAP.items()}.get(posicao_nome)
        if pos_id is None:
            continue
        
        candidatos = df_filtrado[df_filtrado["posicao_id"] == pos_id].sort_values(
            "score_mode", ascending=False
        ).copy()
        
        selecionados = []
        for _, jogador in candidatos.iterrows():
            preco = jogador.get("preco_num", 0) or 0
            if total_preco + preco <= orcamento and len(selecionados) < qtd:
                selecionados.append(jogador)
                total_preco += preco
            if len(selecionados) == qtd:
                break
        
        # Se não encontrou jogadores suficientes, pega os mais baratos
        if len(selecionados) < qtd:
            faltam = qtd - len(selecionados)
            ids_selecionados = [j["atleta_id"] for j in selecionados]
            restantes = candidatos[~candidatos["atleta_id"].isin(ids_selecion
