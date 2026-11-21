# /// script
# requires-python = ">=3.10"
# dependencies = ["duckdb"]
# ///
"""Note un ou plusieurs pipelines de rapprochement AVP ↔ ESCO sur le jeu de référence.

Usage :
    uv run esco-gold/score.py run.duckdb                       # run du notebook (tables avp_skill…)
    uv run esco-gold/score.py a.jsonl b.jsonl --split test     # comparaison finale de deux pipelines
    uv run esco-gold/score.py esco-gold/annotator2.jsonl --covered-only --split test   # plafond humain

Format JSONL d'une prédiction (une ligne par exigence, ou par exigence et par AVP : les lignes d'une
même exigence sont fusionnées) :
    {"phrase": "Rigueur et autonomie", "pred": ["http://data.europa.eu/esco/skill/…"], "candidates": […]}
    {"avp_id": "3134-26-1268/SR", "pred": ["http://data.europa.eu/esco/occupation/…"], "candidates": […]}
La clé peut aussi être "id" (s001, o001…). "pred" : concepts retenus ; "candidates" (facultatif) :
liste classée soumise au LLM, pour le rappel@k. À défaut de "pred", le champ "gold" est lu.
"""

import argparse
import json
import random
import re
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
KS = (1, 5, 10, 20, 50)
N_BOOT = 2000
SEED = 42


def phrase_key(phrase):
    """Même normalisation que l'échantillonnage : « Etre rigoureux » = « Être rigoureux »."""
    text = unicodedata.normalize("NFKD", phrase.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text).split())


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def load_gold():
    rows = read_jsonl(HERE / "skills.jsonl") + read_jsonl(HERE / "occupations.jsonl")
    by_key = {}
    for r in rows:
        by_key[r["id"]] = r
        by_key[phrase_key(r["phrase"]) if "phrase" in r else r["avp_id"]] = r
    return rows, by_key


def merge(rows, gold_by_key):
    """Regroupe les prédictions par ligne du jeu : union des concepts retenus, meilleur rang des candidates."""
    out = {}
    for p in rows:
        key = p.get("id") or (phrase_key(p["phrase"]) if "phrase" in p else p.get("avp_id"))
        g = gold_by_key.get(key)
        if g is None:
            continue
        cur = out.setdefault(g["id"], {"pred": [], "candidates": {}})
        for u in p.get("pred", p.get("gold")) or []:
            if u not in cur["pred"]:
                cur["pred"].append(u)
        for rank, u in enumerate(p.get("candidates") or []):
            cur["candidates"][u] = min(rank, cur["candidates"].get(u, rank))
    for v in out.values():
        v["candidates"] = sorted(v["candidates"], key=v["candidates"].get)
    return out


def from_run(path):
    """Lit les tables d'un run du notebook (avp_esco.duckdb)."""
    import duckdb

    con = duckdb.connect(str(path), read_only=True)
    rows = []
    q = "SELECT {k}, list({u} ORDER BY {o}) FILTER (WHERE {u} IS NOT NULL) FROM {t} GROUP BY ALL"
    sel = dict(con.execute(q.format(k="phrase", u="skill_uri", o="llm_order", t="avp_skill")).fetchall())
    cand = dict(con.execute(q.format(k="phrase", u="skill_uri", o="rank", t="skill_candidate")).fetchall())
    for phrase in set(sel) | set(cand) | {r[0] for r in con.execute("SELECT phrase FROM skill_decision").fetchall()}:
        rows.append({"phrase": phrase, "pred": sel.get(phrase) or [], "candidates": cand.get(phrase) or []})
    sel = dict(con.execute(q.format(k="avp_id", u="occupation_uri", o="rank", t="avp_occupation")).fetchall())
    cand = dict(con.execute(q.format(k="avp_id", u="occupation_uri", o="rank", t="occupation_candidate")).fetchall())
    for avp_id, in con.execute("SELECT avp_id FROM avp").fetchall():
        rows.append({"avp_id": avp_id, "pred": sel.get(avp_id) or [], "candidates": cand.get(avp_id) or []})
    return rows


def line_counts(g, p):
    """Compteurs d'une ligne : (vrais positifs, faux positifs stricts, faux positifs tolérants, faux négatifs)."""
    gold, acc, pred = set(g["gold"]), set(g["acceptable"]), set(p["pred"]) if p else set()
    tp = len(pred & gold)
    return tp, len(pred - gold), len(pred - gold - acc), len(gold - pred)


def prf(counts, tolerant=False):
    tp = sum(c[0] for c in counts)
    fp = sum(c[2 if tolerant else 1] for c in counts)
    fn = sum(c[3] for c in counts)
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return p, r, 2 * p * r / (p + r) if p + r else 0.0


def boot_ci(counts, rng):
    """IC à 95 % du F1 strict par rééchantillonnage des lignes."""
    f1s = sorted(prf([rng.choice(counts) for _ in counts])[2] for _ in range(N_BOOT))
    return f1s[int(0.025 * N_BOOT)], f1s[int(0.975 * N_BOOT)]


def evaluate(gold_rows, preds, kind):
    counts, n_cov, invalid, n_pred = [], 0, 0, 0
    abst = [0, 0]  # lignes sans équivalent ESCO : [bien laissées vides, total]
    hits = {k: [0, 0] for k in KS}  # rappel@k strict, rappel@k tolérant
    n_cand = 0
    prefix = f"http://data.europa.eu/esco/{kind}/"
    for g in gold_rows:
        p = preds.get(g["id"])
        n_cov += p is not None
        counts.append(line_counts(g, p))
        pred = p["pred"] if p else []
        n_pred += len(pred)
        invalid += sum(not u.startswith(prefix) for u in pred)
        if not g["gold"]:
            abst[1] += 1
            abst[0] += not pred
        elif p and p["candidates"]:
            n_cand += 1
            for k in KS:
                top = set(p["candidates"][:k])
                hits[k][0] += bool(top & set(g["gold"]))
                hits[k][1] += bool(top & (set(g["gold"]) | set(g["acceptable"])))
    return {
        "counts": counts,
        "n": len(gold_rows),
        "covered": n_cov,
        "strict": prf(counts),
        "tolerant": prf(counts, tolerant=True),
        "abstention": abst,
        "invalid": (invalid, n_pred),
        "recall_at_k": {k: (h[0] / n_cand, h[1] / n_cand) for k, h in hits.items()} if n_cand else None,
        "n_cand": n_cand,
    }


def fmt(x):
    return f"{100 * x:5.1f}"


def report(name, res, rng):
    for kind, r in res.items():
        if not r["n"]:
            continue
        lo, hi = boot_ci(r["counts"], rng)
        sp, sr, sf = r["strict"]
        tp, _, tf = r["tolerant"]
        a_ok, a_n = r["abstention"]
        inv, n_pred = r["invalid"]
        print(f"  {kind:<12} {r['covered']:>3}/{r['n']:<3} │ strict P {fmt(sp)} R {fmt(sr)} F1 {fmt(sf)} [{fmt(lo)}–{fmt(hi)}]"
              f" │ tolérant P {fmt(tp)} F1 {fmt(tf)} │ abstention {a_ok}/{a_n} │ invalides {inv}/{n_pred}")
        if r["recall_at_k"]:
            rk = "  ".join(f"@{k} {fmt(s).strip()}/{fmt(t).strip()}" for k, (s, t) in r["recall_at_k"].items())
            print(f"  {'':<12} rappel@k strict/tolérant ({r['n_cand']} lignes) : {rk}")


def paired(res_a, res_b, rng):
    """Différence de F1 strict (B − A) et IC à 95 % par rééchantillonnage apparié des lignes."""
    for kind in res_a:
        ca, cb = res_a[kind]["counts"], res_b[kind]["counts"]
        if not ca:
            continue
        idx = range(len(ca))
        diffs = []
        for _ in range(N_BOOT):
            s = [rng.choice(idx) for _ in idx]
            diffs.append(prf([cb[i] for i in s])[2] - prf([ca[i] for i in s])[2])
        diffs.sort()
        d = prf(cb)[2] - prf(ca)[2]
        lo, hi = diffs[int(0.025 * N_BOOT)], diffs[int(0.975 * N_BOOT)]
        verdict = "significatif" if lo > 0 or hi < 0 else "non significatif"
        print(f"  {kind:<12} ΔF1 {100 * d:+5.1f} [{100 * lo:+5.1f} ; {100 * hi:+5.1f}] → {verdict}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("preds", nargs="+", help="prédictions : .jsonl ou run .duckdb")
    ap.add_argument("--split", choices=("dev", "test", "all"), default="dev",
                    help="dev par défaut ; test seulement pour les comparaisons finales")
    ap.add_argument("--covered-only", action="store_true",
                    help="ne note que les lignes présentes dans les prédictions (ex. annotator2.jsonl)")
    args = ap.parse_args()

    gold_rows, gold_by_key = load_gold()
    if args.split != "all":
        gold_rows = [g for g in gold_rows if g["split"] == args.split]
    if args.split == "test":
        print("⚠ test : ne rien ajuster d'après ces erreurs.\n")

    results = []
    for path in args.preds:
        raw = from_run(path) if path.endswith(".duckdb") else read_jsonl(path)
        preds = merge(raw, gold_by_key)
        rows = [g for g in gold_rows if g["id"] in preds] if args.covered_only else gold_rows
        res = {kind: evaluate([g for g in rows if g["id"][0] == kind[0]], preds, kind) for kind in ("skill", "occupation")}
        print(f"{path} ({args.split})")
        report(path, res, random.Random(SEED))
        print()
        results.append((path, res))

    for (pa, ra), (pb, rb) in zip(results, results[1:]):
        print(f"{Path(pb).name} − {Path(pa).name}")
        paired(ra, rb, random.Random(SEED))


if __name__ == "__main__":
    main()
