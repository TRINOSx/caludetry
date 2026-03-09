"""
Phase 2 — Seed/Plant VOC Profile Enrichment

Uses AI (Claude) to research and compile:
  - Known VOC emissions for the specific crop/seed
  - Growth stage VOC patterns (germination → flowering → fruiting)
  - Stress response VOCs for this species
  - Fruit/seed ripening VOC markers

Output: seed_voc_{project_id}.json
  {
    "seed": "Solanum lycopersicum",
    "growth_stages": [...],
    "voc_profiles": {
      "healthy": [...],
      "stress_drought": [...],
      "stress_heat": [...],
      "flowering": [...],
      "fruiting": [...],
    },
    "key_biomarkers": [...]
  }
"""
import json
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ProjectConfig


def query_claude_seed_voc(config: ProjectConfig) -> dict:
    """
    Use Claude API to research VOC emission profiles for the specific seed.
    Returns structured JSON with known VOC data.
    """
    if not config.anthropic_api_key:
        print("[seed_voc] No Anthropic API key. Using placeholder data.")
        return _placeholder_seed_data(config)

    prompt = f"""You are an expert plant physiologist and volatile organic compound (VOC) researcher.

I need a comprehensive VOC emission profile for this crop:
- Scientific name: {config.seed_name}
- Variety: {config.seed_variety}
- Common name: {config.seed_common_name}
- Family: {config.crop_family}
- Growing location: {config.location_name} ({config.latitude}, {config.longitude})

Provide a JSON response with:
1. "growth_stages": array of growth stages with duration_days and key_vocs for each
2. "voc_profiles": object with keys for each condition:
   - "healthy_baseline": VOCs emitted during normal growth
   - "stress_drought": VOCs elevated during water stress
   - "stress_heat": VOCs elevated during heat stress
   - "stress_cold": VOCs elevated during cold stress
   - "flowering": VOCs emitted during flowering
   - "fruiting": VOCs emitted during fruit development/ripening
   - "pathogen_fungal": VOCs elevated during fungal infection
   - "pathogen_bacterial": VOCs elevated during bacterial infection
   - "herbivore_insect": VOCs emitted as defense against insects
3. "key_biomarkers": top 15 most important VOCs for this crop with:
   - compound name
   - formula
   - typical_concentration_ppb (range)
   - biological_role
   - detectable_by (which sensor types: MOx, PID, electrochemical)

For each VOC, include:
- compound: common name
- formula: chemical formula
- concentration_ppb: typical range [min, max]
- biological_role: why the plant emits this

IMPORTANT: Only include well-documented VOCs from peer-reviewed literature.
Respond ONLY with valid JSON, no markdown or explanation."""

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

    print(f"[seed_voc] Querying Claude for {config.seed_name} VOC profile...")
    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=body,
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()

        text = data["content"][0]["text"]
        # Parse JSON from response (handle potential markdown wrapping)
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]

        result = json.loads(text)
        print(f"[seed_voc] Got {len(result.get('key_biomarkers', []))} biomarkers")
        return result

    except Exception as e:
        print(f"[seed_voc] Claude API error: {e}")
        return _placeholder_seed_data(config)


def query_claude_fruit_voc(config: ProjectConfig) -> dict:
    """
    Query Claude specifically for fruit/seed ripening VOC markers.
    """
    if not config.anthropic_api_key:
        return {}

    prompt = f"""As a post-harvest biology expert, list the VOCs emitted during
fruit/seed development and ripening of {config.seed_name} ({config.seed_common_name}).

Include for each VOC:
- compound, formula, concentration_ppb [min, max]
- ripening_stage: "immature", "breaker", "turning", "pink", "ripe", "overripe"
- is_climacteric_marker: boolean

Respond ONLY with valid JSON array."""

    headers = {
        "x-api-key": config.anthropic_api_key,
        "content-type": "application/json",
        "anthropic-version": "2023-06-01",
    }

    body = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 2048,
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers, json=body, timeout=120,
        )
        resp.raise_for_status()
        text = resp.json()["content"][0]["text"].strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        return {"fruit_ripening_vocs": json.loads(text)}
    except Exception as e:
        print(f"[seed_voc] Fruit VOC query failed: {e}")
        return {}


def _placeholder_seed_data(config: ProjectConfig) -> dict:
    """Placeholder data when no API key is available."""
    return {
        "seed": config.seed_name,
        "variety": config.seed_variety,
        "note": "PLACEHOLDER — provide anthropic_api_key for real data",
        "growth_stages": [
            {"stage": "germination", "duration_days": 7, "key_vocs": ["ethanol", "acetaldehyde"]},
            {"stage": "seedling", "duration_days": 21, "key_vocs": ["isoprene", "ethylene"]},
            {"stage": "vegetative", "duration_days": 30, "key_vocs": ["isoprene", "alpha-pinene", "limonene"]},
            {"stage": "flowering", "duration_days": 14, "key_vocs": ["linalool", "geraniol", "beta-caryophyllene"]},
            {"stage": "fruiting", "duration_days": 30, "key_vocs": ["ethylene", "hexanal", "cis-3-hexenal"]},
            {"stage": "senescence", "duration_days": 14, "key_vocs": ["ethanol", "acetaldehyde", "methanol"]},
        ],
        "voc_profiles": {
            "healthy_baseline": [
                {"compound": "isoprene", "formula": "C5H8", "concentration_ppb": [5, 50]},
                {"compound": "alpha-pinene", "formula": "C10H16", "concentration_ppb": [1, 20]},
            ],
            "stress_drought": [
                {"compound": "ethylene", "formula": "C2H4", "concentration_ppb": [50, 500]},
                {"compound": "ethanol", "formula": "C2H5OH", "concentration_ppb": [100, 2000]},
                {"compound": "acetaldehyde", "formula": "C2H4O", "concentration_ppb": [20, 200]},
            ],
            "flowering": [
                {"compound": "linalool", "formula": "C10H18O", "concentration_ppb": [10, 300]},
                {"compound": "geraniol", "formula": "C10H18O", "concentration_ppb": [5, 100]},
            ],
            "herbivore_insect": [
                {"compound": "methyl_salicylate", "formula": "C8H8O3", "concentration_ppb": [10, 200]},
                {"compound": "DMNT", "formula": "C11H18", "concentration_ppb": [5, 100]},
                {"compound": "beta-caryophyllene", "formula": "C15H24", "concentration_ppb": [5, 80]},
            ],
        },
        "key_biomarkers": [
            {"compound": "ethylene", "formula": "C2H4", "typical_concentration_ppb": [10, 500],
             "biological_role": "stress hormone, ripening", "detectable_by": ["PID", "MOx"]},
            {"compound": "isoprene", "formula": "C5H8", "typical_concentration_ppb": [5, 100],
             "biological_role": "thermotolerance", "detectable_by": ["PID", "MOx"]},
            {"compound": "methyl_salicylate", "formula": "C8H8O3", "typical_concentration_ppb": [5, 200],
             "biological_role": "defense signaling", "detectable_by": ["PID", "MOx"]},
        ],
    }


def run_seed_voc_enrichment(config: ProjectConfig) -> Path:
    """
    Fetch and save seed VOC profile.
    Returns path to JSON file.
    """
    out_path = config.enriched_dir / f"seed_voc_{config.project_id}.json"

    if out_path.exists():
        print(f"[seed_voc] Already exists: {out_path}")
        return out_path

    config.ensure_dirs()

    # Main seed VOC profile
    seed_data = query_claude_seed_voc(config)

    # Fruit/seed ripening VOCs
    fruit_data = query_claude_fruit_voc(config)
    if fruit_data:
        seed_data.update(fruit_data)

    # Add metadata
    seed_data["_meta"] = {
        "seed_name": config.seed_name,
        "variety": config.seed_variety,
        "location": config.location_name,
        "generated_at": __import__("datetime").datetime.now().isoformat(),
    }

    with open(out_path, "w") as f:
        json.dump(seed_data, f, indent=2)

    print(f"[seed_voc] Saved → {out_path}")
    return out_path
