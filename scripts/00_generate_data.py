"""Synthetic messy lead dataset generator — Project 1.
Deterministic (seed 42). All data synthetic. See PRD A9 / LLD D9.
Usage: python scripts/00_generate_data.py [--n 4000] [--seed 42]
Output: data/raw/leads_raw.csv (all columns as text)
Date convention: day-first (DD/MM/YYYY) for ambiguous dates.
"""
import argparse
import numpy as np
import pandas as pd
from pathlib import Path

def fmt_created_mixed(dt: pd.Timestamp, r: float) -> str:
    # 70% ISO, 15% dd/mm/yyyy, 15% "d Mon yyyy"
    if r < 0.70:
        return dt.strftime("%Y-%m-%d")
    elif r < 0.85:
        return dt.strftime("%d/%m/%Y")
    else:
        return dt.strftime("%-d %b %Y") if hasattr(dt, "strftime") else dt.strftime("%d %b %Y").lstrip("0")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", type=str, default="data/raw/leads_raw.csv")
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    N = args.n
    sources = ["Campus Event", "Instagram", "Referral", "Direct", "Web Form"]
    weights = [0.30, 0.25, 0.15, 0.15, 0.15]
    conv_p = {"Campus Event": 0.18, "Instagram": 0.06, "Referral": 0.28, "Direct": 0.20, "Web Form": 0.09}
    cities = ["Bengaluru", "Hyderabad", "Chennai", "Kochi"]
    agents = [f"Agent {i}" for i in range(1, 9)]

    src = rng.choice(sources, N, p=weights)
    conv = np.array([rng.random() < conv_p[s] for s in src])
    other = rng.choice(["Interested", "Positive", "Follow-up", "Non-converted", "New"], N,
                       p=[0.20, 0.12, 0.25, 0.33, 0.10])
    status = np.where(conv, "Converted", other)
    created = pd.to_datetime("2026-04-01") + pd.to_timedelta(rng.integers(0, 180, N), unit="D")
    phones = rng.integers(6_000_000_000, 9_999_999_999, N).astype(str)

    df = pd.DataFrame({
        "lead_id": [f"L{100000+i}" for i in range(N)],
        "lead_name": [f"Person {i}" for i in range(N)],
        "phone_raw": phones,
        "source": src,
        "city": rng.choice(cities, N),
        "created_date": created.strftime("%Y-%m-%d"),
        "agent": rng.choice(agents, N),
        "status_raw": status,
        "last_contact_date": (created + pd.to_timedelta(rng.integers(0, 30, N), unit="D")).strftime("%Y-%m-%d"),
        "deal_value_raw": np.where(conv, rng.choice([1200, 2500, 3500], N), 0).astype(str),
    })

    # --- inject mess ---
    # 1. duplicates: 6% rows cloned with new lead_id (same phone)
    dup_idx = rng.choice(N, int(0.06 * N), replace=False)
    dups = df.iloc[dup_idx].copy()
    dups["lead_id"] = [f"L{200000+i}" for i in range(len(dups))]
    df = pd.concat([df, dups], ignore_index=True)

    # 2. phone format variants
    df["phone_raw"] = df["phone_raw"].map(
        lambda p: rng.choice([p, f"+91 {p[:5]}-{p[5:]}", f" {p} "]))
    # 3. blank names 4%, mixed case + trailing spaces
    df.loc[rng.choice(len(df), int(0.04 * len(df)), replace=False), "lead_name"] = ""
    mask = rng.random(len(df)) < 0.30
    df.loc[mask, "lead_name"] = df.loc[mask, "lead_name"].str.lower() + " "
    # 4. blank source 2%
    df.loc[rng.choice(len(df), int(0.02 * len(df)), replace=False), "source"] = ""
    # 5. invalid phones 2%
    df.loc[rng.choice(len(df), int(0.02 * len(df)), replace=False), "phone_raw"] = "12345"
    # 6. status case/format variants
    def vary(s):
        r = rng.random()
        if r < 0.25: return s.lower()
        if r < 0.50: return s.upper()
        if r < 0.65: return s.replace("-", " ")
        if r < 0.75: return f" {s} "
        return s
    df["status_raw"] = df["status_raw"].map(vary)
    # 7. city variants (case + spaces)
    def vary_city(c):
        r = rng.random()
        if r < 0.15: return c.lower()
        if r < 0.25: return c.upper()
        if r < 0.35: return f" {c} "
        return c
    df["city"] = df["city"].map(vary_city)
    # 8. blank last_contact 10%
    df.loc[rng.choice(len(df), int(0.10 * len(df)), replace=False), "last_contact_date"] = ""
    # 9. deal value format variants for converted
    def vary_deal(v):
        if v == "0": return "" if rng.random() < 0.5 else "0"
        r = rng.random()
        if r < 0.3: return f"\u20b9{int(v):,}"
        if r < 0.5: return f" {v} "
        return v
    df["deal_value_raw"] = df["deal_value_raw"].map(vary_deal)
    # 10. mixed created_date formats (15% dd/mm/yyyy, 15% d Mon yyyy)
    fmt_r = rng.random(len(df))
    # reconstruct datetimes for formatting: parse current ISO where possible
    base_created = pd.to_datetime("2026-04-01") + pd.to_timedelta(
        rng.integers(0, 180, len(df)), unit="D")
    # keep original order correlation: reuse existing created where ISO, else new random
    # simpler: reformat existing ISO dates into mixed styles
    def mix(dstr, r):
        try:
            dt = pd.to_datetime(dstr, dayfirst=False)
        except Exception:
            return dstr
        if r < 0.70:
            return dt.strftime("%Y-%m-%d")
        elif r < 0.85:
            return dt.strftime("%d/%m/%Y")
        else:
            s = dt.strftime("%d %b %Y")
            return s.lstrip("0")
    df["created_date"] = [mix(d, r) for d, r in zip(df["created_date"], fmt_r)]

    df = df.sample(frac=1, random_state=args.seed).reset_index(drop=True)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"Wrote {len(df)} rows -> {out}")
    print(f"raw rows={len(df)}, dup clones={len(dups)}")

if __name__ == "__main__":
    main()
