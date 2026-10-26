"""binary_sensor platform."""

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import override

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import Mcn02ConfigEntry
from .client import Mcn02Client
from .entity import Mcn02Entity

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class _EntityDescription(BinarySensorEntityDescription):
    """Class describing sensor entities."""

    value_fn: Callable[[Mcn02Client], bool | None]


_SENSOR_DESCRIPTIONS: tuple[_EntityDescription, ...] = (
    _EntityDescription(
        key="match_state",
        translation_key="match_state",
        has_entity_name=True,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda client: (
            client.match_state == 1 if client.match_state is not None else None
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: Mcn02ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensor platform."""

    async_add_entities(
        _Entity(config_entry, description) for description in _SENSOR_DESCRIPTIONS
    )


class _Entity(BinarySensorEntity, Mcn02Entity):
    """Representation of a binary_sensor entity."""

    _attr_has_entity_name = True

    entity_description: _EntityDescription

    def __init__(
        self,
        config_entry: Mcn02ConfigEntry,
        description: _EntityDescription,
    ) -> None:
        """Initialize entity with entity description."""

        super().__init__(config_entry)

        self.entity_description = description
        self._attr_unique_id = f"{self._device_id}.{self.entity_description.key}"

    @property
    @override
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        return self.entity_description.value_fn(self._client)
