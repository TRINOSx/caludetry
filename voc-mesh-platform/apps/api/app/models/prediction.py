import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MLPrediction(Base):
    __tablename__ = "ml_predictions"

    time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
        default=lambda: datetime.now(timezone.utc),
    )
    parcela_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("parcelas.id"), primary_key=True
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    stress_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    bloom_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    pest_zone_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    pest_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    carbon_index: Mapped[float | None] = mapped_column(Float, nullable=True)
    fire_alert: Mapped[bool] = mapped_column(Boolean, default=False)
    model_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
