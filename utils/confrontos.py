# utils/confrontos.py
import pandas as pd

PARTIDAS_R10 = [
    {"mandante_id": 276, "visitante_id": 283, "mandante": "São Paulo",    "visitante": "Cruzeiro",     "local": "Morumbis",              "data": "04/04 18:30", "pos_casa": 4,  "pos_vis": 17},
    {"mandante_id": 294, "visitante_id": 266, "mandante": "Coritiba",     "visitante": "Fluminense",   "local": "Couto Pereira",         "data": "04/04 20:30", "pos_casa": 7,  "pos_vis": 2},
    {"mandante_id": 267, "visitante_id": 263, "mandante": "Vasco",        "visitante": "Botafogo",     "local": "São Januário",          "data": "04/04 21:00", "pos_casa": 8,  "pos_vis": 15},
    {"mandante_id": 315, "visitante_id": 287, "mandante": "Chapecoense",  "visitante": "Vitória",      "local": "Arena Condá",           "data": "05/04 16:00", "pos_casa": 18, "pos_vis": 12},
    {"mandante_id": 262, "visitante_id": 277, "mandante": "Flamengo",     "visitante": "Santos",       "local": "Maracanã",              "data": "05/04 17:30", "pos_casa": 6,  "pos_vis": 13},
    {"mandante_id": 282, "visitante_id": 293, "mandante": "Atlético-MG",  "visitante": "Athletico-PR", "local": "Arena MRV",             "data": "05/04 17:30", "pos_casa": 9,  "pos_vis": 5},
    {"mandante_id": 264, "visitante_id": 285, "mandante": "Corinthians",  "visitante": "Internacional","local": "Neo Química Arena",     "data": "05/04 19:30", "pos_casa": 14, "pos_vis": 16},
    {"mandante_id": 265, "visitante_id": 275, "mandante": "Bahia",        "visitante": "Palmeiras",    "local": "Fonte Nova",            "data": "05/04 19:30", "pos_casa": 3,  "pos_vis": 1},
    {"mandante_id": 2305,"visitante_id": 280, "mandante": "Mirassol",     "visitante": "Bragantino",   "local": "Maião",                 "data": "05/04 20:00", "pos_casa": 19, "pos_vis": 11},
    {"mandante_id": 284, "visitante_id": 364, "mandante": "Grêmio",       "visitante": "Remo",         "local": "Arena do Grêmio",       "data": "05/04 20:30", "pos_casa": 10, "pos_vis": 20},
]

APROVEITAMENTO_R10 = {
    276: ["v","v","d","d","e"],   # São Paulo (mandante)
    283: ["d","e","d","e","v"],   # Cruzeiro (visitante)
    294: ["d","e","e","e","d"],   # Coritiba (mandante)
    266: ["v","v","d","v","v"],   # Fluminense (visitante)
    267: ["v","e","v","v","e"],   # Vasco (mandante)
    263: ["d","d","v","d","v"],   # Botafogo (visitante)
    315: ["d","e","e","d","d"],   # Chapecoense (mandante)
    287: ["e","d","d","d","v"],   # Vitória (visitante)
    262: ["v","v","v","e","d"],   # Flamengo (mandante)
    277: ["e","e","d","e","v"],   # Santos (visitante)
    282: ["v","d","v","d","v"],   # Atlético-MG (mandante)
    293: ["d","v","v","v","d"],   # Athletico-PR (visitante)
    264: ["d","e","e","e","d"],   # Corinthians (mandante)
    285: ["d","d","v","v","e"],   # Internacional (visitante)
    265: ["e","v","v","d","v"],   # Bahia (mandante)
    275: ["d","v","v","v","v"],   # Palmeiras (visitante)
    2305:["e","d","d","d","d"],   # Mirassol (mandante)
    280: ["d","v","v","v","d"],   # Bragantino (visitante)
    284: ["e","e","v","d","d"],   # Grêmio (mandante)
    364: ["d","d","d","v","d"],   # Remo (visitante)
}

def calcular_aproveitamento_pct(resultados: list) -> float:
    """Converte lista de resultados em % de aproveitamento."""
    pontos = {"v": 3, "e": 1, "d": 0}
    total = sum(pontos.get(r, 0) for r in resultados)
    maximo = len(resultados) * 3
    return round((total / maximo) * 100, 1) if maximo > 0 else 0.0

def get_forca_confronto(clube_id: int, eh_mandante: bool) -> dict:
    """Retorna dados de força do confronto para um clube."""
    for p in PARTIDAS_R10:
        if eh_mandante and p["mandante_id"] == clube_id:
            aprov_casa  = calcular_aproveitamento_pct(APROVEITAMENTO_R10.get(clube_id, []))
            aprov_vis   = calcular_aproveitamento_pct(APROVEITAMENTO_R10.get(p["visitante_id"], []))
            vantagem    = aprov_casa - aprov_vis
            return {
                "adversario":    p["visitante"],
                "mando":         "🏠 Casa",
                "local":         p["local"],
                "data":          p["data"],
                "aprov_proprio": aprov_casa,
                "aprov_adv":     aprov_vis,
                "vantagem":      round(vantagem, 1),
                "fav":           "✅ Favorito" if vantagem > 10 else ("⚠️ Equilibrado" if vantagem > -10 else "❌ Desfavorito"),
                "pos_casa":      p["pos_casa"],
                "pos_vis":       p["pos_vis"],
            }
        if not eh_mandante and p["visitante_id"] == clube_id:
            aprov_vis  = calcular_aproveitamento_pct(APROVEITAMENTO_R10.get(clube_id, []))
            aprov_casa = calcular_aproveitamento_pct(APROVEITAMENTO_R10.get(p["mandante_id"], []))
            vantagem   = aprov_vis - aprov_casa
            return {
                "adversario":    p["mandante"],
                "mando":         "✈️ Fora",
                "local":         p["local"],
                "data":          p["data"],
                "aprov_proprio": aprov_vis,
                "aprov_adv":     aprov_casa,
                "vantagem":      round(vantagem, 1),
                "fav":           "✅ Favorito" if vantagem > 10 else ("⚠️ Equilibrado" if vantagem > -10 else "❌ Desfavorito"),
                "pos_casa":      p["pos_casa"],
                "pos_vis":       p["pos_vis"],
            }
    return {}

def get_clubes_em_casa() -> list:
    return [p["mandante_id"] for p in PARTIDAS_R10]

def get_confrontos_df() -> pd.DataFrame:
    """Retorna DataFrame com todos os confrontos da rodada."""
    rows = []
    for p in PARTIDAS_R10:
        aprov_casa = calcular_aproveitamento_pct(APROVEITAMENTO_R10.get(p["mandante_id"], []))
        aprov_vis  = calcular_aproveitamento_pct(APROVEITAMENTO_R10.get(p["visitante_id"], []))
        rows.append({
            "Data/Hora":     p["data"],
            "Mandante":      p["mandante"],
            "Pos. Casa":     p["pos_casa"],
            "Visitante":     p["visitante"],
            "Pos. Fora":     p["pos_vis"],
            "Local":         p["local"],
            "Aprov. Casa %": aprov_casa,
            "Aprov. Fora %": aprov_vis,
            "Equilíbrio":    "⚖️" if abs(aprov_casa - aprov_vis) <= 15 else ("🏠✅" if aprov_casa > aprov_vis else "✈️✅"),
        })
    return pd.DataFrame(rows)
