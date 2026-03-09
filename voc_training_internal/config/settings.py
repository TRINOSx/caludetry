"""
Project settings — the programmer fills this before running.

This is the SINGLE configuration file that drives the entire pipeline.
Fill in your APIs, seed info, location, and start date, then run:
    python run_project.py
"""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"


@dataclass
class ProjectConfig:
    """
    Fill this config before running the training pipeline.
    All 3 phases read from this single config.
    """

    # ─────────────────────────────────────────────────────────
    # REQUIRED: Programmer must fill these
    # ─────────────────────────────────────────────────────────

    # Crop / Seed identity
    seed_name: str = ""              # e.g. "Solanum lycopersicum" (tomato)
    seed_variety: str = ""           # e.g. "Roma VF"
    seed_common_name: str = ""       # e.g. "tomato"
    crop_family: str = ""            # e.g. "Solanaceae"

    # Location (GPS)
    latitude: float = 0.0            # e.g. 20.6597
    longitude: float = 0.0           # e.g. -103.3496
    altitude_m: float = 0.0          # meters above sea level
    location_name: str = ""          # e.g. "Guadalajara, Jalisco, MX"
    timezone: str = "UTC"            # e.g. "America/Mexico_City"

    # Time range for data collection
    start_date: str = ""             # ISO format: "2026-03-09T08:00:00"
    end_date: str = ""               # optional, empty = ongoing

    # ─────────────────────────────────────────────────────────
    # API Keys (programmer provides)
    # ─────────────────────────────────────────────────────────
    openweather_api_key: str = ""    # Climate history
    google_earth_engine_project: str = ""  # AlphaEarth / GEE
    anthropic_api_key: str = ""      # Claude for seed/microorganism VOC research
    ncbi_api_key: str = ""           # PubChem / NCBI for compound data (optional)

    # ─────────────────────────────────────────────────────────
    # MQTT / Sensor transport (for live data collection)
    # ─────────────────────────────────────────────────────────
    mqtt_broker: str = "localhost"
    mqtt_port: int = 1883
    mqtt_topic_prefix: str = "training/voc"
    lora_gateway_serial: str = ""    # serial port, e.g. "/dev/ttyUSB0"

    # ─────────────────────────────────────────────────────────
    # Pipeline behavior
    # ─────────────────────────────────────────────────────────
    sample_interval_s: int = 30      # sensor read interval
    batch_size_training: int = 64
    epochs: int = 100
    learning_rate: float = 1e-3
    val_split: float = 0.15
    test_split: float = 0.15
    random_seed: int = 42

    # Enrichment flags (which Phase 2 modules to run)
    enrich_climate: bool = True
    enrich_seed_voc: bool = True
    enrich_microorganisms: bool = True
    enrich_agrochemicals: bool = True
    enrich_alpha_earth: bool = True

    # ─────────────────────────────────────────────────────────
    # Derived paths (auto-computed)
    # ─────────────────────────────────────────────────────────
    raw_dir: Path = field(default_factory=lambda: DATA_DIR / "raw")
    enriched_dir: Path = field(default_factory=lambda: DATA_DIR / "enriched")
    models_dir: Path = field(default_factory=lambda: DATA_DIR / "models")
    cache_dir: Path = field(default_factory=lambda: DATA_DIR / "cache")

    def validate(self) -> list[str]:
        """Check required fields are filled. Returns list of errors."""
        errors = []
        if not self.seed_name:
            errors.append("seed_name is required (e.g. 'Solanum lycopersicum')")
        if not self.latitude or not self.longitude:
            errors.append("latitude/longitude are required")
        if not self.start_date:
            errors.append("start_date is required (ISO format)")
        if not self.anthropic_api_key:
            errors.append("anthropic_api_key is required for seed/microorganism VOC research")
        return errors

    def ensure_dirs(self):
        """Create data directories."""
        for d in [self.raw_dir, self.enriched_dir, self.models_dir, self.cache_dir]:
            d.mkdir(parents=True, exist_ok=True)

    @property
    def start_datetime(self) -> datetime:
        return datetime.fromisoformat(self.start_date) if self.start_date else datetime.now()

    @property
    def project_id(self) -> str:
        """Unique ID for this training run."""
        seed_slug = self.seed_common_name.lower().replace(" ", "_") or "unknown"
        date_slug = self.start_datetime.strftime("%Y%m%d")
        return f"{seed_slug}_{date_slug}_{abs(hash((self.latitude, self.longitude))) % 10000:04d}"
