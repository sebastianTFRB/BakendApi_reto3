import logging
from typing import Any, Dict, List, Optional

import httpx

from core.config import settings

logger = logging.getLogger(__name__)


def _format_price(value: Any) -> Optional[str]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number.is_integer():
        return f"${number:,.0f}"
    return f"${number:,.2f}"


def _build_description(property_data: Dict[str, Any]) -> str:
    """
    Compose a human friendly description combining the base description with key features.
    """
    base_description = (property_data.get("description") or "").strip()
    features: List[str] = []

    if property_data.get("property_type"):
        features.append(str(property_data.get("property_type")))
    if property_data.get("location"):
        features.append(str(property_data.get("location")))
    if property_data.get("area"):
        features.append(f"Area: {property_data.get('area')}")
    if property_data.get("bedrooms") is not None:
        features.append(f"Habitaciones: {property_data.get('bedrooms')}")
    if property_data.get("bathrooms") is not None:
        features.append(f"Banos: {property_data.get('bathrooms')}")
    if property_data.get("parking") is not None:
        features.append(f"Parqueadero: {'Si' if property_data.get('parking') else 'No'}")

    price_text = _format_price(property_data.get("price"))
    if price_text:
        features.append(f"Precio: {price_text}")

    if not features:
        return base_description

    features_text = " | ".join(features)
    if base_description:
        return f"{base_description}\n\nCaracteristicas: {features_text}"
    return f"Caracteristicas: {features_text}"


class SocialPublisher:
    """
    Lightweight client to send property publications to an n8n webhook.
    """

    def __init__(self, webhook_url: Optional[str] = None) -> None:
        self.webhook_url = webhook_url or settings.n8n_webhook_url

    def _build_payload(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        photos = property_data.get("photos") or []
        image_url = photos[0] if isinstance(photos, list) and photos else None
        return {
            "title": property_data.get("title") or "Nueva propiedad",
            "description": _build_description(property_data),
            "url": image_url,  # alias for first photo URL
            "image_url": image_url,
        }

    def publish_property(self, property_data: Dict[str, Any]) -> None:
        """
        Send property information to n8n. Errors are logged but do not raise.
        """
        if not self.webhook_url:
            logger.info("Skipping social publish: N8N_WEBHOOK_URL not configured")
            return

        payload = self._build_payload(property_data)

        try:
            with httpx.Client(timeout=10) as client:
                logger.info("Sending property to n8n webhook %s with payload: %s", self.webhook_url, payload)
                response = client.post(self.webhook_url, json=payload)
                response.raise_for_status()
                logger.info("n8n webhook notified successfully: status=%s", response.status_code)
        except httpx.HTTPStatusError as exc:
            logger.error(
                "n8n webhook responded with error %s: %s",
                exc.response.status_code,
                exc.response.text,
            )
        except Exception as exc:
            logger.error("Failed to notify n8n webhook: %s", exc, exc_info=True)
