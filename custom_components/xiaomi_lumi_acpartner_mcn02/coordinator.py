"""DataUpdateCoordinator for the integration."""

from datetime import timedelta
import logging

from miio.airconditioningcompanionMCN import (
    AirConditioningCompanionMcn02,
    AirConditioningCompanionStatus,
)

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .client import Mcn02Client

_LOGGER = logging.getLogger(__name__)


class Mcn02Coordinator(DataUpdateCoordinator[AirConditioningCompanionStatus]):
    """Mcn02 coordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry,
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

    async def _async_setup(self):
        await self.hass.async_add_executor_job(self._device.info)

    async def _async_update_data(self):
        await self.hass.async_add_executor_job(self._client.update_status, True)
