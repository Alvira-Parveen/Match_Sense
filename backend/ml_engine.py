"""Prediction engine: ELO + Poisson + weighted ensemble + SHAP-style importances
and Monte Carlo bracket simulation.

Note: we implement an XGBoost-*style* weighted ensemble in-house (deterministic,
no heavy training dependency) — the surface behaviour to the API/UI is what
matters for the demo: probabilistic win/draw/loss with named feature importances.
"""
from __future__ import annotations
from typing import Dict, List, Tuple
import math
import random
import numpy as np

from data import TEAMS_BY_CODE, BRACKET_STRUCTURE, h2h
import xgb_model


# --------- ELO --------------------------------------------------------------
def elo_win_prob(elo_a: float, elo_b: float, home_advantage: float = 0.0) -> float:
    """Standard ELO expected-score formula. Returns P(A beats B) as a real in [0,1]."""
    diff = (elo_a + home_advantage) - elo_b
    return 1.0 / (1.0 + 10 ** (-diff / 400.0))


# --------- Poisson goal model ----------------------------------------------
def expected_goals(team_a: Dict, team_b: Dict) -> Tuple[float, float]:
    """Compute expected goals per side using attack/defense strengths."""
    xg_a = team_a["attack"] * (2.0 - team_b["defense"]) * 0.85
    xg_b = team_b["attack"] * (2.0 - team_a["defense"]) * 0.85
    # clamp to sane ranges
    return max(0.4, min(4.5, xg_a)), max(0.4, min(4.5, xg_b))


def poisson_scoreline_probs(xg_a: float, xg_b: float, max_goals: int = 6):
    """Return probability of a-wins, draw, b-wins from independent Poisson goal counts."""
    def pmf(k: int, lam: float) -> float:
        return (lam ** k) * math.exp(-lam) / math.factorial(k)

    a_win = draw = b_win = 0.0
    for ga in range(max_goals + 1):
        for gb in range(max_goals + 1):
            p = pmf(ga, xg_a) * pmf(gb, xg_b)
            if ga > gb:
                a_win += p
            elif ga == gb:
                draw += p
            else:
                b_win += p
    s = a_win + draw + b_win
    return a_win / s, draw / s, b_win / s


# --------- Form / H2H / Injuries scoring ------------------------------------
def form_score(form_str: str) -> float:
    """Convert a 'WWDLW' string to a per-game points average / 3 (normalised)."""
    pts = {"W": 3, "D": 1, "L": 0}
    total = sum(pts.get(c, 0) for c in form_str)
    return total / (3 * max(1, len(form_str)))  # in [0,1]


def injury_penalty(team: Dict) -> float:
    """Return a small penalty in [0, 0.15] based on injuries listed."""
    return min(0.15, 0.05 * len(team.get("injuries", [])))


# --------- Ensemble + SHAP-style feature contributions ----------------------
def predict_match(code_a: str, code_b: str) -> Dict:
    """Full ensemble prediction with feature-level contributions.

    Returns dict:
      prob_a, prob_draw, prob_b, xg_a, xg_b, features: [{name, value, impact, direction}]
    """
    a = TEAMS_BY_CODE[code_a]
    b = TEAMS_BY_CODE[code_b]

    # component probabilities (P(A beats B), ignoring draws for these single components)
    p_elo = elo_win_prob(a["elo"], b["elo"])
    xg_a, xg_b = expected_goals(a, b)
    p_a_win, p_draw, p_b_win = poisson_scoreline_probs(xg_a, xg_b)

    fa, fb = form_score(a["form"]), form_score(b["form"])
    p_form = 0.5 + 0.5 * (fa - fb)  # in [0,1] centered at 0.5

    # H2H
    hh = h2h(code_a, code_b)
    p_h2h = (hh["a_wins"] + 0.5 * hh["draws"]) / hh["total"]

    # Injuries
    inj_a, inj_b = injury_penalty(a), injury_penalty(b)
    p_inj = 0.5 + (inj_b - inj_a) * 2.0  # penalising the injured side
    p_inj = min(0.95, max(0.05, p_inj))

    # XGBoost trained model — real ensemble contribution
    xgb_features = {
        "elo_diff": a["elo"] - b["elo"],
        "form_diff": fa - fb,
        "h2h_ratio": (hh["a_wins"] - hh["b_wins"]) / max(1, hh["total"]),
        "attack_diff": a["attack"] - b["attack"],
        "defense_diff": b["defense"] - a["defense"],
        "injury_delta": len(b.get("injuries", [])) - len(a.get("injuries", [])),
    }
    xgb_probs = xgb_model.predict_proba(xgb_features) if xgb_model.is_ready() else {
        "prob_home": p_elo * 0.7, "prob_draw": 0.2, "prob_away": (1 - p_elo) * 0.7,
    }
    p_xgb_a = xgb_probs["prob_home"] / max(1e-9, xgb_probs["prob_home"] + xgb_probs["prob_away"])

    # Weighted ensemble (XGB now anchors 30%, other components explain the rest)
    w = {"xgb": 0.30, "elo": 0.25, "poisson": 0.18, "form": 0.14, "h2h": 0.08, "injury": 0.05}
    p_a_final = (
        w["xgb"] * p_xgb_a
        + w["elo"] * p_elo
        + w["poisson"] * (p_a_win / max(1e-9, p_a_win + p_b_win))
        + w["form"] * p_form
        + w["h2h"] * p_h2h
        + w["injury"] * p_inj
    )
    p_a_final = min(0.97, max(0.03, p_a_final))

    # Draw share blends Poisson + XGB draw signal
    draw_share = min(0.32, max(0.12, 0.5 * p_draw + 0.5 * xgb_probs["prob_draw"]))
    p_a = p_a_final * (1 - draw_share)
    p_b = (1 - p_a_final) * (1 - draw_share)
    p_d = draw_share

    # SHAP-style contributions: each feature's signed push away from 0.5 baseline,
    # scaled by its weight, expressed as +/- percentage points.
    baseline = 0.5
    features = [
        {"name": "XGBoost Model", "value": f"{p_xgb_a*100:.1f}% home",
         "impact": round((p_xgb_a - baseline) * w["xgb"] * 100, 2)},
        {"name": "ELO Rating Δ",       "value": round(a["elo"] - b["elo"], 1),
         "impact": round((p_elo - baseline) * w["elo"] * 100, 2)},
        {"name": "Expected Goals (Poisson)", "value": f"{xg_a:.2f} vs {xg_b:.2f}",
         "impact": round((p_a_win / max(1e-9, p_a_win + p_b_win) - baseline) * w["poisson"] * 100, 2)},
        {"name": "Recent Form",        "value": f"{a['form']} vs {b['form']}",
         "impact": round((p_form - baseline) * w["form"] * 100, 2)},
        {"name": "Head-to-Head",       "value": f"{hh['a_wins']}W-{hh['draws']}D-{hh['b_wins']}L",
         "impact": round((p_h2h - baseline) * w["h2h"] * 100, 2)},
        {"name": "Squad Availability", "value": f"{len(a.get('injuries', []))} vs {len(b.get('injuries', []))} out",
         "impact": round((p_inj - baseline) * w["injury"] * 100, 2)},
    ]
    features.sort(key=lambda f: abs(f["impact"]), reverse=True)

    # Real SHAP values (TreeExplainer on the trained XGBoost model)
    shap_vals = xgb_model.shap_contributions(xgb_features)

    return {
        "home": code_a,
        "away": code_b,
        "prob_home": round(p_a, 4),
        "prob_draw": round(p_d, 4),
        "prob_away": round(p_b, 4),
        "xg_home": round(xg_a, 2),
        "xg_away": round(xg_b, 2),
        "features": features,
        "shap": shap_vals,
        "shap_ready": xgb_model.shap_ready(),
        "confidence": round(abs(p_a - p_b), 3),
    }


# --------- Monte Carlo bracket simulation -----------------------------------
def _knockout_pick(p_a: float, p_d: float, p_b: float, rng: random.Random) -> int:
    """Pick winner index (0=A, 1=B). In knockouts, draw goes to penalties — split 50/50."""
    r = rng.random()
    if r < p_a:
        return 0
    if r < p_a + p_b:
        return 1
    # draw → penalties → 50/50
    return 0 if rng.random() < 0.5 else 1


def monte_carlo(n_runs: int = 10000, seed: int = 42, results: dict | None = None) -> Dict:
    """Simulate the remainder of the bracket n_runs times.

    Args:
        results: optional dict {match_id -> winner_code}. When provided, matches
                 with a known winner are FROZEN (deterministic) instead of sampled.

    Returns a mapping team_code -> {r16_wins, qf, sf, final, champion} probabilities.
    """
    rng = random.Random(seed)
    results = results or {}
    codes = [t["code"] for t in TEAMS_BY_CODE.values()]
    stats = {c: {"advance_qf": 0, "reach_sf": 0, "reach_final": 0, "champion": 0} for c in codes}

    # Precompute R16 predictions
    r16_preds = {}
    for m in BRACKET_STRUCTURE["R16"]:
        pred = predict_match(m["home"], m["away"])
        r16_preds[m["id"]] = (m["home"], m["away"], pred["prob_home"], pred["prob_draw"], pred["prob_away"])

    for _ in range(n_runs):
        winners: Dict[str, str] = {}
        # R16
        for mid, (h, a, ph, pd, pa) in r16_preds.items():
            if mid in results:
                winners[mid] = results[mid]
            else:
                idx = _knockout_pick(ph, pd, pa, rng)
                winners[mid] = h if idx == 0 else a
            stats[winners[mid]]["advance_qf"] += 1

        # QF
        for qf in BRACKET_STRUCTURE["QF"]:
            h_src, a_src = qf["feeders"]
            h, a = winners[h_src], winners[a_src]
            if qf["id"] in results:
                winners[qf["id"]] = results[qf["id"]]
            else:
                pred = predict_match(h, a)
                idx = _knockout_pick(pred["prob_home"], pred["prob_draw"], pred["prob_away"], rng)
                winners[qf["id"]] = h if idx == 0 else a
            stats[winners[qf["id"]]]["reach_sf"] += 1

        # SF
        for sf in BRACKET_STRUCTURE["SF"]:
            h_src, a_src = sf["feeders"]
            h, a = winners[h_src], winners[a_src]
            if sf["id"] in results:
                winners[sf["id"]] = results[sf["id"]]
            else:
                pred = predict_match(h, a)
                idx = _knockout_pick(pred["prob_home"], pred["prob_draw"], pred["prob_away"], rng)
                winners[sf["id"]] = h if idx == 0 else a
            stats[winners[sf["id"]]]["reach_final"] += 1

        # Final
        f = BRACKET_STRUCTURE["F"][0]
        h_src, a_src = f["feeders"]
        h, a = winners[h_src], winners[a_src]
        if f["id"] in results:
            champion = results[f["id"]]
        else:
            pred = predict_match(h, a)
            idx = _knockout_pick(pred["prob_home"], pred["prob_draw"], pred["prob_away"], rng)
            champion = h if idx == 0 else a
        stats[champion]["champion"] += 1

    # normalise
    out = []
    for code, s in stats.items():
        out.append({
            "code": code,
            "name": TEAMS_BY_CODE[code]["name"],
            "flag": TEAMS_BY_CODE[code]["flag"],
            "elo": TEAMS_BY_CODE[code]["elo"],
            "prob_qf": round(s["advance_qf"] / n_runs, 4),
            "prob_sf": round(s["reach_sf"] / n_runs, 4),
            "prob_final": round(s["reach_final"] / n_runs, 4),
            "prob_champion": round(s["champion"] / n_runs, 4),
        })
    out.sort(key=lambda x: x["prob_champion"], reverse=True)
    return {"runs": n_runs, "teams": out, "frozen_matches": list(results.keys())}


# --------- Expected bracket path (deterministic favourite path) -------------
def expected_bracket(results: dict | None = None) -> Dict:
    """Return the bracket where each match's favourite advances (for UI overlay).

    If `results` is provided (mapping match_id -> winner_code), those matches are
    FROZEN — the actual winner is used instead of the model favourite and each
    frozen match is tagged with `is_actual: True`.
    """
    results = results or {}
    winners: Dict[str, str] = {}
    matches = []
    for m in BRACKET_STRUCTURE["R16"]:
        pred = predict_match(m["home"], m["away"])
        is_actual = m["id"] in results
        winner = results[m["id"]] if is_actual else (m["home"] if pred["prob_home"] >= pred["prob_away"] else m["away"])
        winners[m["id"]] = winner
        matches.append({**m, "prediction": pred, "predicted_winner": winner, "is_actual": is_actual})

    for qf in BRACKET_STRUCTURE["QF"]:
        h_src, a_src = qf["feeders"]
        h, a = winners[h_src], winners[a_src]
        pred = predict_match(h, a)
        is_actual = qf["id"] in results
        winner = results[qf["id"]] if is_actual else (h if pred["prob_home"] >= pred["prob_away"] else a)
        winners[qf["id"]] = winner
        matches.append({**qf, "home": h, "away": a, "prediction": pred, "predicted_winner": winner, "is_actual": is_actual})

    for sf in BRACKET_STRUCTURE["SF"]:
        h_src, a_src = sf["feeders"]
        h, a = winners[h_src], winners[a_src]
        pred = predict_match(h, a)
        is_actual = sf["id"] in results
        winner = results[sf["id"]] if is_actual else (h if pred["prob_home"] >= pred["prob_away"] else a)
        winners[sf["id"]] = winner
        matches.append({**sf, "home": h, "away": a, "prediction": pred, "predicted_winner": winner, "is_actual": is_actual})

    f = BRACKET_STRUCTURE["F"][0]
    h_src, a_src = f["feeders"]
    h, a = winners[h_src], winners[a_src]
    pred = predict_match(h, a)
    is_actual_f = f["id"] in results
    winner = results[f["id"]] if is_actual_f else (h if pred["prob_home"] >= pred["prob_away"] else a)
    winners[f["id"]] = winner
    matches.append({**f, "home": h, "away": a, "prediction": pred, "predicted_winner": winner, "is_actual": is_actual_f})

    # Third-place playoff — SF losers meet
    sf1_h, sf1_a = BRACKET_STRUCTURE["SF"][0]["feeders"]
    sf2_h, sf2_a = BRACKET_STRUCTURE["SF"][1]["feeders"]
    sf1_pair = (winners[sf1_h], winners[sf1_a])
    sf2_pair = (winners[sf2_h], winners[sf2_a])
    sf1_loser = sf1_pair[0] if winners["SF-1"] == sf1_pair[1] else sf1_pair[1]
    sf2_loser = sf2_pair[0] if winners["SF-2"] == sf2_pair[1] else sf2_pair[1]
    tp = BRACKET_STRUCTURE["3P"][0]
    tp_pred = predict_match(sf1_loser, sf2_loser)
    tp_winner = sf1_loser if tp_pred["prob_home"] >= tp_pred["prob_away"] else sf2_loser
    matches.append({**tp, "home": sf1_loser, "away": sf2_loser, "prediction": tp_pred, "predicted_winner": tp_winner})

    return {"matches": matches, "champion": winner, "third_place": tp_winner}
