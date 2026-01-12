"""select platform."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import Mcn02ConfigEntry
from .client import Mcn02Client
from .entity import Mcn02Entity

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class _EntityDescription(SelectEntityDescription):
    """Class describing sensor entities."""

    value_fn: Callable[[Mcn02Client], str | None]
    setter_fn: Callable[[Mcn02Client, str], None]


_SENSOR_DESCRIPTIONS: tuple[_EntityDescription, ...] = (
    _EntityDescription(
        key="ac_mode",
        translation_key="ac_mode",
        has_entity_name=True,
        entity_category=EntityCategory.CONFIG,
        options=["0", "1"],
        value_fn=lambda client: str(client.ac_mode)
        if client.ac_mode is not None
        else None,
        setter_fn=lambda client, value: client.set_ac_mode(int(value)),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: Mcn02ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the select platform."""

    async_add_entities(
        _Entity(config_entry, description) for description in _SENSOR_DESCRIPTIONS
    )


class _Entity(SelectEntity, Mcn02Entity):
    """Representation of a select entity."""

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
    def current_option(self) -> str | None:
        """Return the selected entity option to represent the entity state."""
        return self.entity_description.value_fn(self._client)

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self.hass.async_add_executor_job(
            self.entity_description.setter_fn, self._client, option
        )
        await self.coordinator.async_refresh()
