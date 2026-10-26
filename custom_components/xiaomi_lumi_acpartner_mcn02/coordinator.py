"""DataUpdateCoordinator for the integration."""

from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import override

from miio.airconditioningcompanionMCN import AirConditioningCompanionMcn02

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .client import Mcn02Client

_LOGGER = logging.getLogger(__name__)


type Mcn02ConfigEntry = ConfigEntry[McnRuntimeData]


@dataclass
class McnRuntimeData:
    "Runtime data for the integration."

    device: AirConditioningCompanionMcn02
    coordinator: Mcn02Coordinator
    client: Mcn02Client


class Mcn02Coordinator(DataUpdateCoordinator[None]):
    """Mcn02 coordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: Mcn02ConfigEntry,
        device: AirConditioningCompanionMcn02,
        client: Mcn02Client,
    ) -> None:
        """Initialize Mcn02 coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Mcn02Coordinator",
            config_entry=config_entry,
            update_interval=timedelta(seconds=3),
            always_update=True,
        )
        self._device = device
        self._client = client

    @override
    async def _async_setup(self) -> None:
        await self.hass.async_add_executor_job(self._device.info)

    @override
    async def _async_update_data(self) -> None:
        await self.hass.async_add_executor_job(self._client.update_status, True)
