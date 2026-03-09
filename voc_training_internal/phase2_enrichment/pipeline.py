"""
Phase 2 — Enrichment Orchestrator

Runs all enrichment modules based on config flags:
  1. Climate history (Open-Meteo / OpenWeatherMap)
  2. Seed VOC profiles (Claude AI)
  3. Microorganism VOCs (Claude AI)
  4. Agrochemical VOCs (Claude AI)
  5. AlphaEarth geospatial (SoilGrids / GEE)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ProjectConfig


def run_phase2(config: ProjectConfig) -> dict[str, Path]:
    """
    Execute all Phase 2 enrichment modules.

    Returns dict mapping module name → output file path.
    """
    print("=" * 60)
    print("PHASE 2: Data Enrichment")
    print("=" * 60)
    print(f"Seed: {config.seed_name} ({config.seed_common_name})")
    print(f"Location: {config.location_name}")
    print()

    results = {}

    # 1. Climate history
    if config.enrich_climate:
        print("--- Module 1: Climate History ---")
        from phase2_enrichment.climate import run_climate_enrichment
        results["climate"] = run_climate_enrichment(config)
        print()

    # 2. Seed VOC profiles
    if config.enrich_seed_voc:
        print("--- Module 2: Seed VOC Profiles ---")
        from phase2_enrichment.seed_voc import run_seed_voc_enrichment
        results["seed_voc"] = run_seed_voc_enrichment(config)
        print()

    # 3. Microorganism VOCs
    if config.enrich_microorganisms:
        print("--- Module 3: Microorganism VOCs ---")
        from phase2_enrichment.microorganisms import run_microorganism_enrichment
        results["microorganisms"] = run_microorganism_enrichment(config)
        print()

    # 4. Agrochemical VOCs
    if config.enrich_agrochemicals:
        print("--- Module 4: Agrochemical VOCs ---")
        from phase2_enrichment.agrochemicals import run_agrochemical_enrichment
        results["agrochemicals"] = run_agrochemical_enrichment(config)
        print()

    # 5. AlphaEarth geospatial
    if config.enrich_alpha_earth:
        print("--- Module 5: AlphaEarth Geospatial ---")
        from phase2_enrichment.alpha_earth import run_alpha_earth_enrichment
        results["alpha_earth"] = run_alpha_earth_enrichment(config)
        print()

    print(f"[phase2] Complete. {len(results)} enrichment modules ran.")
    for name, path in results.items():
        print(f"  {name}: {path}")

    return results
