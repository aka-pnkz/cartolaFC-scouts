# utils/score_mitada.py
import pandas as pd
from utils.confrontos import get_clubes_em_casa, get_info_clube

POSICAO_MAP  = {1:"Goleiro", 2:"Lateral", 3:"Zagueiro", 4:"Meia", 5:"Atacante", 6:"Técnico"}
STATUS_LABEL = {1:"🟢 Provável", 2:"🔴 Dúvida", 3:"⚫ Suspenso",
                5:"🟡 Contundido", 6:"⚪ Nulo", 7:"🟢 Provável"}

SCOUTS_POS = {
    1: {"G":8,"DE":3,"DD":3,"SG":5,"GS":-3,"DP":7,"FC":-0.5,"CA":-1.5},
    2: {"G":8,"A":5,"RB":1.5,"I":1,"FS":0.5,"SG":3,"FC":-0.5,"CA":-1.5},
    3: {"G":8,"A":4,"RB":1.5,"I":1,"SG":4,"FC":-0.5,"CA":-1.5,"DE":2},
    4: {"G":8,"A":7,"FD":1.2,"FF":0.8,"FS":0.8,"RB":1.5,"I":1,"FC":-0.5,"CA":-1.5},
    5: {"G":10,"A":6,"FD":1.2,"FF":0.8,"FS":0.8,"FC":-0.5,"CA":-1.5},
    6: {"G":6,"A":4,"SG":3,"FC":-0.3,"CA":-1},
}

def _scout_score(atleta: dict) -> float:
    scouts = atleta.get("scout", {}) or {}
    pesos  = SCOUTS_POS.get(atleta.get("posicao_id", 4), SCOUTS_POS[4])
    return round(sum((scouts.get(k, 0) or 0) * v for k, v in pesos.items()), 2)

def _cb(atleta: dict) -> float:
    media = atleta.get("media_num", 0) or 0
    preco = atleta.get("preco_num", 1) or 1
    return round(media / preco, 3) if preco else 0.0

def calcular_score_mitada(atleta: dict) -> float:
    """
    Score Mitada = ponderação de 5 fatores:
    Média(40%) + CB(20%) + Variação(15%) + Scouts/Jogos(15%) + Bônus Mando(10%)
    Retorna 0.0 se status não for Provável ou jogos < 3.
    """
    status = atleta.get("status_id", 0)
    jogos  = atleta.get("jogos_num", 0) or 0
    if status not in [1, 7] or jogos < 3:
        return 0.0

    media    = atleta.get("media_num", 0) or 0
    variacao = atleta.get("variacao_num", 0) or 0
    clube_id = atleta.get("clube_id", 0)
    cb       = _cb(atleta)
    sc       = _scout_score(atleta) / max(jogos, 1)
    mando    = 0.5 if clube_id in get_clubes_em_casa() else 0.0

    score = (media * 0.40 + cb * 0.20 + variacao * 0.15 + sc * 0.15 + mando * 0.10)
    return round(max(score, 0.0), 3)

def enriquecer_df(atletas_raw: list) -> pd.DataFrame:
    """Converte lista da API em DataFrame completo com Score Mitada."""
    rows = []
    clubes_casa = get_clubes_em_casa()
    for a in atletas_raw:
        clube_id  = a.get("clube_id", 0)
        pos_id    = a.get("posicao_id", 0)
        status_id = a.get("status_id", 0)
        preco     = a.get("preco_num", 0) or 0
        media     = a.get("media_num", 0) or 0
        variacao  = a.get("variacao_num", 0) or 0
        jogos     = a.get("jogos_num", 0) or 0

        eh_casa   = clube_id in clubes_casa
        conf      = get_info_clube(clube_id)
        sm        = calcular_score_mitada
