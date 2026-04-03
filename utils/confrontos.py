# utils/confrontos.py
import pandas as pd

# Dados reais da Rodada 10 extraídos da API
PARTIDAS_R10 = [
    {
        "mandante_id": 276, "visitante_id": 283,
        "mandante": "São Paulo", "visitante": "Cruzeiro",
        "local": "Morumbis", "data": "04/04 18:30",
        "pos_casa": 4, "pos_vis": 17,
        "aprov_casa": ["v","v","d","d","e"],
        "aprov_vis":  ["d","e","d","e","v"],
    },
    {
        "mandante_id": 294, "visitante_id": 266,
        "mandante": "Coritiba", "visitante": "Fluminense",
        "local": "Couto Pereira", "data": "04/04 20:30",
        "pos_casa": 7, "pos_vis": 2,
        "aprov_casa": ["d","e","e","e","d"],
        "aprov_vis":  ["v","v","d","v","v"],
    },
    {
        "mandante_id": 267, "visitante_id": 263,
        "mandante": "Vasco", "visitante": "Botafogo",
        "local": "São Januário", "data": "04/04 21:00",
        "pos_casa": 8, "pos_vis": 15,
        "aprov_casa": ["v","e","v","v","e"],
        "aprov_vis":  ["d","d","v","d","v"],
    },
    {
        "mandante_id": 315, "visitante_id": 287,
        "mandante": "Chapecoense", "visitante": "Vitória",
        "local": "Arena Condá", "data": "05/04 16:00",
        "pos_casa": 18, "pos_vis": 12,
        "aprov_casa": ["d","e","e","d","d"],
        "aprov_vis":  ["e","d","d","d","v"],
    },
    {
        "mandante_id": 262, "visitante_id": 277,
        "mandante": "Flamengo", "visitante": "Santos",
        "local": "Maracanã", "data": "05/04 17:30",
        "pos_casa": 6, "pos_vis": 13,
        "aprov_casa": ["v","v","v","e","d"],
        "aprov_vis":  ["e","e","d","e","v"],
    },
    {
        "mandante_id": 282, "visitante_id": 293,
        "mandante": "Atlético-MG", "visitante": "Athletico-PR",
        "local": "Arena MRV", "data": "05/04 17:30",
        "pos_casa": 9, "pos_vis": 5,
        "aprov_casa": ["v","d","v","d","v"],
        "aprov_vis":  ["d","v","v","v","d"],
    },
    {
        "mandante_id": 264, "visitante_id": 285,
        "mandante": "Corinthians", "visitante": "Internacional",
        "local": "Neo Química Arena", "data": "05/04 19:30",
        "pos_casa": 14, "pos_vis": 16,
        "aprov_casa": ["d","e","e","e","d"],
        "aprov_vis":  ["d","d","v","v","e"],
    },
    {
        "mandante_id": 265, "visitante_id": 275,
        "mandante": "Bahia", "visitante": "Palmeiras",
        "local": "Fonte Nova", "data": "05/04 19:30",
        "pos_casa": 3, "pos_vis": 1,
        "aprov_casa": ["e","v","v","d","v"],
        "aprov_vis":  ["d","v","v","v","v"],
    },
    {
        "mandante_id": 2305, "visitante_id": 280,
        "mandante": "Mirassol", "visitante": "Bragantino",
        "local": "Maião", "data": "05/04 20:00",
        "pos_casa": 19, "pos_vis": 11,
        "aprov_casa": ["e","d","d","d","d"],
        "aprov_vis":  ["d","v","v","v","d"],
    },
    {
        "mandante_id": 284, "visitante_id": 364,
        "mandante": "Grêmio", "visitante": "Remo",
        "local": "Arena do Grêmio", "data": "05/04 20:30",
        "pos_casa": 10, "pos_vis": 20,
        "aprov_casa": ["e","e","v","d","d"],
        "aprov_vis":  ["d","d","d","v","d"],
    },
]

def _aprov_pct(resultados: list) -> float:
    pts = {"v": 3, "e": 1, "d": 0}
    total = sum(pts.get(r, 0) for r in resultados)
    return round((total / (len(resultados) * 3)) * 100, 1) if resultados else 0.0

def get_clubes_em_casa() -> list:
    return [p["mandante_id"] for p in PARTIDAS_R10]

def get_info_clube(clube_id: int) -> dict:
    """Retorna informações do confronto para o clube."""
    for p in PARTIDAS_R10:
        if p["mandante_id"] == clube_id:
            aprov_casa = _aprov_pct(p["aprov_casa"])
            aprov_vis  = _aprov_pct(p["aprov_vis"])
            diff = aprov_casa - aprov_vis
            return {
                "adversario": p["visitante"],
                "mando": "🏠 Casa",
                "local": p["local"],
                "data": p["data"],
                "aprov_proprio": aprov_casa,
                "aprov_adv": aprov_vis,
                "diff": diff,
                "fav": "✅ Favorito" if diff > 10 else ("⚠️ Equilíbrio" if diff >= -10 else "❌ Desfavorito"),
            }
        if p["visitante_id"] == clube_id:
            aprov_vis  = _aprov_pct(p["aprov_vis"])
            aprov_casa = _aprov_pct(p["aprov_casa"])
            diff = aprov_vis - aprov_casa
            return {
                "adversario": p["mandante"],
                "mando": "✈️ Fora",
                "local": p["local"],
                "data": p["data"],
                "aprov_proprio": aprov_vis,
                "aprov_adv": aprov_casa,
                "diff": diff,
                "fav": "✅ Favorito" if diff > 10 else ("⚠️ Equilíbrio" if diff >= -10 else "❌ Desfavorito"),
            }
    return {"adversario": "?", "mando": "?", "local": "?", "data": "?",
            "aprov_proprio": 0, "aprov_adv": 0, "diff": 0, "fav": "?"}

def get_confrontos_df() -> pd.DataFrame:
    rows = []
    for p in PARTIDAS_R10:
        ac = _aprov_pct(p["aprov_casa"])
        av = _aprov_pct(p["aprov_vis"])
        diff = ac - av
        rows.append({
            "Data":           p["data"],
            "Mandante":       p["mandante"],
            "Pos.Casa":       p["pos_casa"],
            "Visitante":      p["visitante"],
            "Pos.Fora":       p["pos_vis"],
            "Local":          p["local"],
            "Aprov.Casa%":    ac,
            "Aprov.Fora%":    av,
            "Vantagem":       round(diff, 1),
            "Resultado":      "🏠✅" if diff > 10 else ("✈️✅" if diff < -10 else "⚖️"),
        })
    return pd.DataFrame(rows)
