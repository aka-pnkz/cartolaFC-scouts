# utils/score_mitada.py
import pandas as pd
import numpy as np
from utils.scouts import calcular_score_scout, calcular_custo_beneficio
from utils.confrontos import get_forca_confronto, get_clubes_em_casa

POSICAO_MAP = {1: "Goleiro", 2: "Lateral", 3: "Zagueiro", 4: "Meia", 5: "Atacante", 6: "Técnico"}

STATUS_LABEL = {
    1: "🟢 Provável",
    2: "🔴 Dúvida",
    3: "⚫ Suspenso",
    5: "🟡 Contundido",
    6: "⚪ Nulo",
    7: "🟢 Provável",
}

def calcular_score_mitada(atleta: dict, jogos_min: int = 3) -> float:
    """
    Score Mitada = combinação ponderada de:
    - Média ponderada (40%)
    - Custo-benefício (20%)
    - Variação (15%)
    - Scout score (15%)
    - Bônus de mando (10%)
    """
    media       = atleta.get("media_num", 0) or 0
    variacao    = atleta.get("variacao_num", 0) or 0
    preco       = atleta.get("preco_num", 1) or 1
    jogos       = atleta.get("jogos_num", 0) or 0
    clube_id    = atleta.get("clube_id", 0)
    status      = atleta.get("status_id", 0)

    if jogos < jogos_min or status not in [1, 7]:
        return 0.0

    cb          = calcular_custo_beneficio(atleta)
    scout_score = calcular_score_scout(atleta)
    clubes_casa = get_clubes_em_casa()
    bonus_mando = 1.0 if clube_id in clubes_casa else 0.0

    score = (
        media       * 0.40 +
        cb          * 0.20 +
        variacao    * 0.15 +
        (scout_score / max(jogos, 1)) * 0.15 +
        bonus_mando * 0.10
    )
    return round(max(score, 0), 3)

def enriquecer_dataframe(atletas_raw: list) -> pd.DataFrame:
    """
    Converte lista de atletas da API em DataFrame enriquecido
    com Score Mitada, custo-benefício, confronto e status label.
    """
    rows = []
    for a in atletas_raw:
        clube_id  = a.get("clube_id", 0)
        pos_id    = a.get("posicao_id", 0)
        status_id = a.get("status_id", 0)
        preco     = a.get("preco_num", 0) or 0
        media     = a.get("media_num", 0) or 0
        variacao  = a.get("variacao_num", 0) or 0
        jogos     = a.get("jogos_num", 0) or 0

        clubes_casa = get_clubes_em_casa()
        eh_mandante = clube_id in clubes_casa

        # Tenta buscar dados do confronto (casa ou fora)
        confronto   = get_forca_confronto(clube_id, eh_mandante)
        if not confronto:
            confronto = get_forca_confronto(clube_id, not eh_mandante)

        score_mitada = calcular_score_mitada(a)
        cb           = calcular_custo_beneficio(a)

        rows.append({
            "atleta_id":      a.get("atleta_id"),
            "Nome":           a.get("apelido", a.get("nome", "?")),
            "Clube":          a.get("clube", {}).get("abreviacao", str(clube_id)) if isinstance(a.get("clube"), dict) else str(clube_id),
            "clube_id":       clube_id,
            "Posição":        POSICAO_MAP.get(pos_id, "?"),
            "posicao_id":     pos_id,
            "Status":         STATUS_LABEL.get(status_id, "❓"),
            "status_id":      status_id,
            "Preço (C$)":     preco,
            "preco_num":      preco,
            "Média":          media,
            "media_num":      media,
            "Variação":       variacao,
            "variacao_num":   variacao,
            "Jogos":          jogos,
            "jogos_num":      jogos,
            "CB Ratio":       cb,
            "cb_ratio":       cb,
            "Score Mitada":   score_mitada,
            "Mando":          "🏠" if eh_mandante else "✈️",
            "Adversário":     confronto.
