"""
Phase 2 — Agrochemical VOC Enrichment

Researches fertilizers and pesticides commonly used for the crop:
  - Fertilizer VOC emissions (urea → NH3, organic → various)
  - Pesticide active ingredients and their VOC signatures
  - Fumigant residual VOCs
  - Application timing relative to sensor readings

Data source: Claude AI + PubChem compound data

Output: agrochemicals_{project_id}.json
"""
import json
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ProjectConfig


def query_claude_agrochemicals(config: ProjectConfig) -> dict:
    """Query Claude for fertilizer and pesticide VOC data for this crop."""
    if not config.anthropic_api_key:
        return _placeholder_agrochem_data(config)

    prompt = f"""You are an agricultural chemistry expert specializing in VOC emissions from agrochemicals.

For this crop:
- Crop: {config.seed_name} ({config.seed_common_name}), family {config.crop_family}
- Location: {config.location_name}

Provide JSON with:

1. "fertilizers": Common fertilizers used for this crop. For each:
   - name: product/type name
   - type: "synthetic_N" | "synthetic_P" | "synthetic_K" | "organic" | "foliar" | "slow_release"
   - active_compounds: array of chemical compounds
   - voc_emissions: VOCs released during/after application
     [{{compound, formula, peak_concentration_ppb, duration_hours, trigger: "application"|"rain"|"heat"}}]
   - application_frequency: typical schedule

2. "pesticides": Common pesticides for this crop. For each:
   - name: trade/generic name
   - type: "fungicide" | "insecticide" | "herbicide" | "nematicide" | "acaricide"
   - active_ingredient: chemical name
   - active_ingredient_formula: chemical formula
   - voc_emissions: VOCs from the product itself
     [{{compound, formula, concentration_ppb, half_life_hours}}]
   - target_organisms: what it controls
   - application_method: "foliar_spray" | "soil_drench" | "fumigation" | "seed_treatment"

3. "fumigants": If applicable for this crop/region:
   - name, active_ingredient, residual_vocs, dissipation_days

4. "agrochemical_voc_markers": Top 10 VOCs that indicate recent agrochemical application:
   - compound, formula, source_type, persistence_hours, sensor_channel

Respond ONLY with valid JSON."""

    headers = {
        "x-api-key": config.anthropic_api_key,
        "content-type": "application/json",
        "anthropic-version": "2023-06-01",
    }

    body = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }

    print(f"[agrochem] Querying Claude for {config.seed_common_name} agrochemicals...")
    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers, json=body, timeout=120,
        )
        resp.raise_for_status()
        text = resp.json()["content"][0]["text"].strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        result = json.loads(text)
        n_fert = len(result.get("fertilizers", []))
        n_pest = len(result.get("pesticides", []))
        print(f"[agrochem] Found: {n_fert} fertilizers, {n_pest} pesticides")
        return result
    except Exception as e:
        print(f"[agrochem] Claude API error: {e}")
        return _placeholder_agrochem_data(config)


def _placeholder_agrochem_data(config: ProjectConfig) -> dict:
    """Placeholder data."""
    return {
        "note": "PLACEHOLDER — provide anthropic_api_key for real data",
        "fertilizers": [
            {
                "name": "Urea (46-0-0)",
                "type": "synthetic_N",
                "active_compounds": ["CO(NH2)2"],
                "voc_emissions": [
                    {"compound": "ammonia", "formula": "NH3",
                     "peak_concentration_ppb": [500, 5000], "duration_hours": 72, "trigger": "application"},
                ],
                "application_frequency": "every 4-6 weeks",
            },
            {
                "name": "Compost/Manure",
                "type": "organic",
                "active_compounds": ["various"],
                "voc_emissions": [
                    {"compound": "ammonia", "formula": "NH3",
                     "peak_concentration_ppb": [200, 2000], "duration_hours": 168, "trigger": "application"},
                    {"compound": "dimethyl_disulfide", "formula": "C2H6S2",
                     "peak_concentration_ppb": [10, 200], "duration_hours": 96, "trigger": "application"},
                    {"compound": "methane", "formula": "CH4",
                     "peak_concentration_ppb": [100, 1000], "duration_hours": 48, "trigger": "application"},
                    {"compound": "H2S", "formula": "H2S",
                     "peak_concentration_ppb": [50, 500], "duration_hours": 48, "trigger": "application"},
                ],
                "application_frequency": "pre-planting + monthly",
            },
        ],
        "pesticides": [
            {
                "name": "Chlorothalonil",
                "type": "fungicide",
                "active_ingredient": "chlorothalonil",
                "active_ingredient_formula": "C8Cl4N2",
                "voc_emissions": [
                    {"compound": "chlorothalonil_vapor", "formula": "C8Cl4N2",
                     "concentration_ppb": [1, 50], "half_life_hours": 24},
                ],
                "target_organisms": ["Botrytis", "Alternaria", "downy mildew"],
                "application_method": "foliar_spray",
            },
        ],
        "fumigants": [],
        "agrochemical_voc_markers": [
            {
                "compound": "ammonia", "formula": "NH3",
                "source_type": "fertilizer", "persistence_hours": 72,
                "sensor_channel": "dfrobot_h2s",  # cross-sensitivity
            },
        ],
    }


def run_agrochemical_enrichment(config: ProjectConfig) -> Path:
    """Fetch and save agrochemical VOC data."""
    out_path = config.enriched_dir / f"agrochemicals_{config.project_id}.json"

    if out_path.exists():
        print(f"[agrochem] Already exists: {out_path}")
        return out_path

    config.ensure_dirs()
    data = query_claude_agrochemicals(config)

    data["_meta"] = {
        "seed_name": config.seed_name,
        "location": config.location_name,
        "generated_at": __import__("datetime").datetime.now().isoformat(),
    }

    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"[agrochem] Saved → {out_path}")
    return out_path
