import pandas as pd
import numpy as np

POSICOES = {
    1: "Goleiro",
    2: "Lateral",
    3: "Zagueiro",
    4: "Meia",
    5: "Atacante",
    6: "Técnico"
}

SCOUTS_POSITIVOS = {
    "G": 8.0,   # Gol
    "A": 5.0,   # Assistência
    "FD": 1.2,  # Finalização defendida
    "FF": 0.8,  # Finalização fora
    "FS": 0.5,  # Falta sofrida
    "GS": 0.0,  # Gol sofrido (neutro para atacantes)
    "DE": 3.0,  # Defesa difícil
    "SG": 5.0,  # Sem gol sofrido
    "CV": 3.0,  # Chute a gol defesa
    "GC": 0.0,  # Gol contra (para calcular)
    "PP": 0.0,  # Pênalti perdido
    "PS": 0.0,  # Pênalti sofrido
    "I": 0.5,   # Interceptação
    "RB": 1.5,  # Roubada de bola
    "FC": -0.3, # Falta cometida
    "CA": -1.0, # Cartão amarelo
    "CV2": -3.0,# Cartão vermelho
    "DD": 3.0,  # Defesa difícil
    "DP": 7.0,  # Defesa de pênalti
    "PE": -0.1, # Passe errado
}

SCOUTS_NEGATIVOS = ["FC", "CA", "CV2", "GS", "GC", "PP", "PE"]

SCOUTS_PESOS_POSICAO = {
    1: {"G": 10, "DE": 4, "SG": 6, "GS": -3, "DP": 8, "DD": 4, "FC": -0.5, "CA": -2},
    2: {"A": 6, "RB": 2, "I": 1, "FS": 0.5, "FC": -0.5, "CA": -1.5, "G": 8, "SG": 4},
    3: {"RB": 2, "I": 1.5, "SG": 4, "FC": -0.5, "CA": -1.5, "G": 8, "A": 4, "DE": 2},
    4: {"A": 7, "G": 8, "FD": 1.5, "FF": 1, "FS": 0.8, "RB": 1.5, "I": 1, "FC": -0.5, "CA": -1.5},
    5: {"G": 10, "A": 6, "FD": 1.5, "FF": 1, "FS": 1, "FC": -0.5, "CA": -1.5},
    6: {"G": 6, "A": 4, "SG": 3, "FC": -0.3, "CA": -1}
}

def calcular_score_scout(atleta):
    """Calcula score de scouts ponderado por posição."""
    pos_id = atleta.get("posicao_id", 4)
    scouts = atleta.get("scout", {}) or {}
    pesos = SCOUTS_PESOS_POSICAO.get(pos_id, SCOUTS_PESOS_POSICAO[4])
    
    score = 0
    for scout, peso in pesos.items():
        valor = scouts.get(scout, 0) or 0
        score += valor * peso
    return round(score, 2)

def calcular_pontuacao_estimada(atleta):
    """Estima pontuação baseada em scouts e média."""
    media = atleta.get("media_num", 0) or 0
    score_scout = calcular_score_scout(atleta)
    variacao = atleta.get("variacao_num", 0) or 0
    jogos = atleta.get("jogos_num", 0) or 1
    
    # Ponderação: 50% média, 30% tendência scout, 20% variação
    estimativa = (media * 0.5) + (score_scout / max(jogos, 1) * 0.3) + (variacao * 0.2)
    return round(max(estimativa, 0), 2)

def get_scout_display(atleta):
    """Retorna scouts formatados para exibição."""
    scouts = atleta.get("scout", {}) or {}
    pos_id = atleta.get("posicao_id", 4)
    
    principais = []
    if pos_id == 1:  # Goleiro
        chaves = ["G", "DE", "DD", "SG", "GS", "DP", "FC", "CA"]
    elif pos_id in [2, 3]:  # Defensores
        chaves = ["G", "A", "RB", "I", "SG", "FC", "CA", "DE"]
    elif pos_id == 4:  # Meia
        chaves = ["G", "A", "FD", "FF", "FS", "RB", "I", "FC", "CA"]
    else:  # Atacante e Técnico
        chaves = ["G", "A", "FD", "FF", "FS", "FC", "CA"]
    
    for k in chaves:
        v = scouts.get(k, 0) or 0
        if v != 0:
            emoji = "✅" if k not in SCOUTS_NEGATIVOS else "❌"
            principais.append(f"{emoji}{k}:{v}")
    
    return " | ".join(principais) if principais else "Sem scouts"

def calcular_custo_beneficio(atleta):
    """Calcula relação custo-benefício."""
    media = atleta.get("media_num", 0) or 0
    preco = atleta.get("preco_num", 1) or 1
    if preco == 0:
        return 0
    return round(media / preco, 3)
