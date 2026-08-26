"""Shared Pydantic response models."""

from pydantic import BaseModel


class PredictionResponse(BaseModel):
    label: str
    confidence: float
