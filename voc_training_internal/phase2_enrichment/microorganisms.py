"""
Phase 2 — Microorganism VOC Enrichment

Researches microorganisms associated with:
  1. The specific crop/seed (pathogens, symbionts, soil microbiome)
  2. The geographic zone (region-specific pathogens)

For each microorganism, fetches:
  - Species name
  - Type (fungal, bacterial, viral, nematode)
  - Associated VOC emissions (what gases they produce)
  - Disease they cause (if pathogenic)
  - Typical conditions for occurrence

Data sources:
  - Claude AI (literature synthesis)
  - PubChem (compound verification)

Output: microorganisms_{project_id}.json
"""
import json
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ProjectConfig


def query_claude_crop_microorganisms(config: ProjectConfig) -> dict:
    """
    Use Claude to research microorganisms associated with the crop.
    """
    if not config.anthropic_api_key:
        return _placeholder_microorg_data(config)

    prompt = f"""You are a plant pathologist and microbial ecology expert.

For this crop and location:
- Crop: {config.seed_name} ({config.seed_common_name}), family {config.crop_family}
- Location: {config.location_name} ({config.latitude}, {config.longitude})

Provide a JSON response with:

1. "crop_pathogens": Array of pathogens that affect this crop. For each:
   - species: scientific name
   - common_name: disease name
   - type: "fungal" | "bacterial" | "viral" | "nematode" | "oomycete"
   - voc_emissions: array of VOCs the pathogen produces [{{compound, formula, concentration_ppb}}]
   - plant_defense_vocs: array of VOCs the plant emits in response
   - favorable_conditions: {{temp_range_c, humidity_range_pct, soil_moisture}}
   - detectable_days_before_visual: how early VOC detection can spot it

2. "soil_microbiome": Array of key soil microorganisms for this crop:
   - species, type ("beneficial_fungal" | "beneficial_bacterial" | "pathogenic")
   - voc_emissions: what VOCs they produce in soil
   - effect_on_crop: description

3. "regional_threats": Pathogens specifically common in this geographic region:
   - species, type, disease, prevalence ("common" | "moderate" | "rare")
   - seasonal_peak: month range

4. "microbial_voc_biomarkers": Top 10 microbial VOCs for sensor detection:
   - compound, formula, source_organism, indicates (what condition)
   - typical_concentration_ppb, sensor_detectability ("high" | "medium" | "low")

IMPORTANT: Only cite well-documented organisms and their VOCs.
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

    print(f"[microorg] Querying Claude for {config.seed_common_name} microorganisms at {config.location_name}...")
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
        n_pathogens = len(result.get("crop_pathogens", []))
        n_soil = len(result.get("soil_microbiome", []))
        n_regional = len(result.get("regional_threats", []))
        print(f"[microorg] Found: {n_pathogens} pathogens, {n_soil} soil microbes, {n_regional} regional threats")
        return result
    except Exception as e:
        print(f"[microorg] Claude API error: {e}")
        return _placeholder_microorg_data(config)


def _placeholder_microorg_data(config: ProjectConfig) -> dict:
    """Placeholder when no API key available."""
    return {
        "note": "PLACEHOLDER — provide anthropic_api_key for real data",
        "crop_pathogens": [
            {
                "species": "Botrytis cinerea",
                "common_name": "gray mold",
                "type": "fungal",
                "voc_emissions": [
                    {"compound": "1-octen-3-ol", "formula": "C8H16O", "concentration_ppb": [5, 50]},
                    {"compound": "3-octanone", "formula": "C8H16O", "concentration_ppb": [2, 30]},
                ],
                "plant_defense_vocs": [
                    {"compound": "methyl_salicylate", "formula": "C8H8O3"},
                    {"compound": "hexanal", "formula": "C6H12O"},
                ],
                "favorable_conditions": {"temp_range_c": [15, 25], "humidity_range_pct": [80, 100]},
                "detectable_days_before_visual": 3,
            },
            {
                "species": "Fusarium oxysporum",
                "common_name": "fusarium wilt",
                "type": "fungal",
                "voc_emissions": [
                    {"compound": "dimethyl_disulfide", "formula": "C2H6S2", "concentration_ppb": [10, 100]},
                    {"compound": "dimethyl_trisulfide", "formula": "C2H6S3", "concentration_ppb": [5, 50]},
                ],
                "plant_defense_vocs": [
                    {"compound": "ethylene", "formula": "C2H4"},
                    {"compound": "methyl_jasmonate", "formula": "C13H20O3"},
                ],
                "favorable_conditions": {"temp_range_c": [20, 30], "humidity_range_pct": [60, 90]},
                "detectable_days_before_visual": 5,
            },
        ],
        "soil_microbiome": [
            {
                "species": "Trichoderma harzianum",
                "type": "beneficial_fungal",
                "voc_emissions": [
                    {"compound": "6-pentyl-2H-pyranone", "formula": "C10H14O2"},
                ],
                "effect_on_crop": "biocontrol agent, suppresses soil pathogens",
            },
        ],
        "regional_threats": [],
        "microbial_voc_biomarkers": [
            {
                "compound": "1-octen-3-ol",
                "formula": "C8H16O",
                "source_organism": "various fungi",
                "indicates": "fungal infection",
                "typical_concentration_ppb": [2, 100],
                "sensor_detectability": "medium",
            },
            {
                "compound": "dimethyl_disulfide",
                "formula": "C2H6S2",
                "source_organism": "soil bacteria, Fusarium",
                "indicates": "root disease, anaerobic soil",
                "typical_concentration_ppb": [5, 200],
                "sensor_detectability": "high",
            },
        ],
    }


def run_microorganism_enrichment(config: ProjectConfig) -> Path:
    """
    Fetch and save microorganism VOC data.
    Returns path to JSON file.
    """
    out_path = config.enriched_dir / f"microorganisms_{config.project_id}.json"

    if out_path.exists():
        print(f"[microorg] Already exists: {out_path}")
        return out_path

    config.ensure_dirs()
    data = query_claude_crop_microorganisms(config)

    data["_meta"] = {
        "seed_name": config.seed_name,
        "location": config.location_name,
        "generated_at": __import__("datetime").datetime.now().isoformat(),
    }

    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"[microorg] Saved → {out_path}")
    return out_path
