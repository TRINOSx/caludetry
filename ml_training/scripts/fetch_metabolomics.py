#!/usr/bin/env python3
"""
Fetch plant VOC compound data from Metabolomics Workbench and MetaboLights APIs.

These repositories provide GC-MS compound identification data — NOT sensor readings.
The data is used to:
  1. Identify which compounds are emitted under specific plant conditions
  2. Build compound emission profiles for stress/defense/flowering states
  3. Generate training targets for the compound_sensor_map bridge

Usage:
    python fetch_metabolomics.py                              # Fetch from both sources
    python fetch_metabolomics.py --source metabolomics_workbench
    python fetch_metabolomics.py --source metabolights
    python fetch_metabolomics.py --query "plant volatile stress"
"""
import argparse
import json
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import METABOLOMICS_SOURCES, DATASETS_DIR, COMPOUND_SENSOR_FINGERPRINTS

# Output directory for fetched metabolomics data
METABOLOMICS_DIR = DATASETS_DIR / "metabolomics"


def _retry_get(url: str, params: dict = None, max_retries: int = 3, timeout: int = 30) -> requests.Response:
    """GET with exponential backoff for flaky APIs."""
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, params=params, timeout=timeout)
            resp.raise_for_status()
            return resp
        except (requests.RequestException, requests.HTTPError) as e:
            if attempt == max_retries - 1:
                raise
            wait = 2 ** (attempt + 1)
            print(f"  [retry] {e} — waiting {wait}s")
            time.sleep(wait)


# ─────────────────────────────────────────────────────────────
# Metabolomics Workbench
# ─────────────────────────────────────────────────────────────

def fetch_mw_studies(keywords: list[str] = None) -> list[dict]:
    """Fetch study list from Metabolomics Workbench, optionally filtered by keywords."""
    cfg = METABOLOMICS_SOURCES["metabolomics_workbench"]
    base = cfg["base_url"]
    keywords = keywords or cfg["plant_study_keywords"]

    studies = []
    for kw in keywords:
        url = f"{base}/study/study_title/{kw}/summary"
        try:
            resp = _retry_get(url, timeout=60)
            data = resp.json()
            if isinstance(data, dict) and "1" in data:
                # MW returns {"1": {...}, "2": {...}, ...}
                for val in data.values():
                    if isinstance(val, dict):
                        studies.append(val)
            elif isinstance(data, list):
                studies.extend(data)
            print(f"  [MW] keyword '{kw}': {len(data) if isinstance(data, (dict, list)) else 0} results")
        except Exception as e:
            print(f"  [MW] keyword '{kw}' failed: {e}")

    # Deduplicate by study_id
    seen = set()
    unique = []
    for s in studies:
        sid = s.get("study_id", s.get("STUDY_ID", ""))
        if sid and sid not in seen:
            seen.add(sid)
            unique.append(s)

    return unique


def fetch_mw_metabolites(study_id: str) -> list[dict]:
    """Fetch metabolite list for a specific MW study."""
    cfg = METABOLOMICS_SOURCES["metabolomics_workbench"]
    url = f"{cfg['base_url']}/study/study_id/{study_id}/metabolites"
    try:
        resp = _retry_get(url, timeout=60)
        data = resp.json()
        if isinstance(data, dict):
            return list(data.values()) if all(k.isdigit() for k in data.keys()) else [data]
        return data if isinstance(data, list) else []
    except Exception as e:
        print(f"  [MW] metabolites for {study_id} failed: {e}")
        return []


# ─────────────────────────────────────────────────────────────
# MetaboLights
# ─────────────────────────────────────────────────────────────

def fetch_ml_studies(keywords: list[str] = None) -> list[dict]:
    """Fetch study list from MetaboLights, filtered by plant-related keywords."""
    cfg = METABOLOMICS_SOURCES["metabolights"]
    base = cfg["base_url"]
    keywords = keywords or cfg["plant_study_keywords"]

    studies = []
    for kw in keywords:
        url = f"{base}/studies"
        try:
            resp = _retry_get(url, params={"search": kw}, timeout=60)
            data = resp.json()
            if isinstance(data, dict) and "content" in data:
                studies.extend(data["content"])
            elif isinstance(data, list):
                studies.extend(data)
            print(f"  [ML] keyword '{kw}': {len(data.get('content', [])) if isinstance(data, dict) else len(data)} results")
        except Exception as e:
            print(f"  [ML] keyword '{kw}' failed: {e}")

    seen = set()
    unique = []
    for s in studies:
        sid = s.get("accession", s.get("id", ""))
        if sid and sid not in seen:
            seen.add(sid)
            unique.append(s)

    return unique


def fetch_ml_metabolites(study_id: str) -> list[dict]:
    """Fetch metabolite list for a specific MetaboLights study."""
    cfg = METABOLOMICS_SOURCES["metabolights"]
    url = f"{cfg['base_url']}/studies/{study_id}/metabolites"
    try:
        resp = _retry_get(url, timeout=60)
        data = resp.json()
        return data if isinstance(data, list) else data.get("metaboliteAssignmentLines", [])
    except Exception as e:
        print(f"  [ML] metabolites for {study_id} failed: {e}")
        return []


# ─────────────────────────────────────────────────────────────
# Compound matching & output
# ─────────────────────────────────────────────────────────────

def match_to_platform_compounds(metabolites: list[dict]) -> list[dict]:
    """
    Match fetched metabolite names against our platform's 50 compound slots
    and known fingerprints. Returns matched compounds with their metadata.
    """
    platform_compounds = set(COMPOUND_SENSOR_FINGERPRINTS.keys())

    # Build name variants for fuzzy matching
    name_map = {}
    for compound in platform_compounds:
        canonical = compound.lower().replace("-", "").replace("_", "")
        name_map[canonical] = compound
        name_map[compound.lower()] = compound

    matched = []
    for m in metabolites:
        # MetaboLights uses "databaseIdentifier", MW uses "metabolite_name"
        name = (
            m.get("metabolite_name", "")
            or m.get("metabolite", "")
            or m.get("databaseIdentifier", "")
            or ""
        ).strip()

        if not name:
            continue

        normalized = name.lower().replace("-", "").replace("_", "").replace(" ", "")

        # Check exact and partial matches
        match_key = None
        for key, compound in name_map.items():
            if key in normalized or normalized in key:
                match_key = compound
                break

        if match_key:
            fingerprint = COMPOUND_SENSOR_FINGERPRINTS.get(match_key, {})
            matched.append({
                "original_name": name,
                "platform_compound": match_key,
                "category": fingerprint.get("category", "unknown"),
                "sensor_responses": {
                    k: v for k, v in fingerprint.items()
                    if k not in ("category", "mw", "boiling_c")
                },
                "source_metadata": m,
            })

    return matched


def save_results(results: dict, filename: str) -> Path:
    """Save fetched results to JSON."""
    METABOLOMICS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = METABOLOMICS_DIR / filename
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"[saved] {out_path} ({len(json.dumps(results))} bytes)")
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Fetch plant VOC data from metabolomics APIs")
    parser.add_argument("--source", choices=["metabolomics_workbench", "metabolights", "both"],
                        default="both", help="Which API to query")
    parser.add_argument("--query", nargs="+", help="Custom search keywords")
    parser.add_argument("--max-studies", type=int, default=10,
                        help="Max studies to fetch metabolites from per source")
    args = parser.parse_args()

    METABOLOMICS_DIR.mkdir(parents=True, exist_ok=True)
    keywords = args.query

    all_results = {"metabolomics_workbench": {}, "metabolights": {}}

    # --- Metabolomics Workbench ---
    if args.source in ("metabolomics_workbench", "both"):
        print("\n=== Metabolomics Workbench ===")
        studies = fetch_mw_studies(keywords)
        print(f"Found {len(studies)} unique studies")

        all_metabolites = []
        for study in studies[:args.max_studies]:
            sid = study.get("study_id", study.get("STUDY_ID", ""))
            if not sid:
                continue
            mets = fetch_mw_metabolites(sid)
            if mets:
                all_metabolites.extend(mets)
                print(f"  {sid}: {len(mets)} metabolites")
            time.sleep(0.5)  # Rate limiting

        matched = match_to_platform_compounds(all_metabolites)
        all_results["metabolomics_workbench"] = {
            "studies_found": len(studies),
            "metabolites_fetched": len(all_metabolites),
            "platform_matches": len(matched),
            "matched_compounds": matched,
            "studies": studies[:args.max_studies],
        }
        print(f"Platform compound matches: {len(matched)}")

    # --- MetaboLights ---
    if args.source in ("metabolights", "both"):
        print("\n=== MetaboLights ===")
        studies = fetch_ml_studies(keywords)
        print(f"Found {len(studies)} unique studies")

        all_metabolites = []
        for study in studies[:args.max_studies]:
            sid = study.get("accession", study.get("id", ""))
            if not sid:
                continue
            mets = fetch_ml_metabolites(sid)
            if mets:
                all_metabolites.extend(mets)
                print(f"  {sid}: {len(mets)} metabolites")
            time.sleep(0.5)

        matched = match_to_platform_compounds(all_metabolites)
        all_results["metabolights"] = {
            "studies_found": len(studies),
            "metabolites_fetched": len(all_metabolites),
            "platform_matches": len(matched),
            "matched_compounds": matched,
            "studies": studies[:args.max_studies],
        }
        print(f"Platform compound matches: {len(matched)}")

    # --- Save ---
    save_results(all_results, "metabolomics_compounds.json")

    # --- Summary ---
    total_mw = len(all_results["metabolomics_workbench"].get("matched_compounds", []))
    total_ml = len(all_results["metabolights"].get("matched_compounds", []))
    print(f"\n=== Summary ===")
    print(f"Metabolomics Workbench matches: {total_mw}")
    print(f"MetaboLights matches:           {total_ml}")
    print(f"Total unique compound matches:  {total_mw + total_ml}")
    print(f"\nThese compounds can now be used with compound_sensor_map.py")
    print(f"to generate synthetic MOx sensor training data.")


if __name__ == "__main__":
    main()
