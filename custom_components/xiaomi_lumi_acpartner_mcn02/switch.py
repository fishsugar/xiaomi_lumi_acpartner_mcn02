"""switch platform."""

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any, override

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import Mcn02ConfigEntry
from .client import Mcn02Client
from .entity import Mcn02Entity

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class _EntityDescription(SwitchEntityDescription):
    """Class describing sensor entities."""

    value_fn: Callable[[Mcn02Client], bool | None]
    setter_fn: Callable[[Mcn02Client, bool], None]


_SENSOR_DESCRIPTIONS: tuple[_EntityDescription, ...] = (
    _EntityDescription(
        key="en_nnlight",
        translation_key="en_nnlight",
        has_entity_name=True,
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda client: (
            client.en_nnlight == 1 if client.en_nnlight is not None else None
        ),
        setter_fn=lambda client, value: client.set_en_nnlight(1 if value else 0),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: Mcn02ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the switch platform."""

    async_add_entities(
        _Entity(config_entry, description) for description in _SENSOR_DESCRIPTIONS
    )


class _Entity(SwitchEntity, Mcn02Entity):
    """Representation of a switch entity."""

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
        """Return True if entity is on."""
        return self.entity_description.value_fn(self._client)

    @override
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await self.hass.async_add_executor_job(
            self.entity_description.setter_fn, self._client, True
        )
        await self.coordinator.async_refresh()

    @override
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await self.hass.async_add_executor_job(
            self.entity_description.setter_fn, self._client, False
        )
        await self.coordinator.async_refresh()
