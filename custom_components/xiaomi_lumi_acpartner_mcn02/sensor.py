"""sensor platform."""

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import override

from miio.airconditioningcompanionMCN import AirConditioningCompanionStatus

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType

from . import Mcn02ConfigEntry
from .client import Mcn02Client
from .entity import Mcn02Entity

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class Mcn02SensorEntityDescription(SensorEntityDescription):
    """Class describing sensor entities."""

    value_fn: Callable[[Mcn02Client], StateType]


_SENSOR_DESCRIPTIONS: tuple[Mcn02SensorEntityDescription, ...] = (
    Mcn02SensorEntityDescription(
        key="power",
        has_entity_name=True,
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda client: client.load_power if client else None,
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


class _Entity(SensorEntity, Mcn02Entity):
    """Representation of a sensor entity."""

    _attr_has_entity_name = True

    entity_description: Mcn02SensorEntityDescription
    _status: AirConditioningCompanionStatus | None = None
    _value: StateType

    def __init__(
        self,
        config_entry: Mcn02ConfigEntry,
        description: Mcn02SensorEntityDescription,
    ) -> None:
        """Initialize entity with entity description."""

        super().__init__(config_entry)

        self.entity_description = description
        self._attr_unique_id = f"{self._device_id}.{self.entity_description.key}"

    @property
    @override
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self._client)
