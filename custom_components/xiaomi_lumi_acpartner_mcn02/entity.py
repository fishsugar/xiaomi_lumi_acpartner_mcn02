"""Base entity for the integration."""

from abc import ABC

import homeassistant.helpers.device_registry as dr
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import Mcn02ConfigEntry
from .const import DOMAIN
from .coordinator import Mcn02Coordinator


class Mcn02Entity(ABC, CoordinatorEntity[Mcn02Coordinator]):
    """Base entity for the integration."""

    def __init__(
        self,
        config_entry: Mcn02ConfigEntry,
    ) -> None:
        """Initialize an Mcn02Entity."""

        super().__init__(config_entry.runtime_data.coordinator)

        device = config_entry.runtime_data.device
        self._device = device
        self._client = config_entry.runtime_data.client

        device_id = f"{device.device_id:08X}"
        self._device_id = device_id

        miio_device_info = device.info()
        device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            manufacturer="Xiaomi",
            model_id=device.model,
            hw_version=miio_device_info.hardware_version,
            sw_version=miio_device_info.firmware_version,
            translation_key="air_conditioning_companion_mcn02",
        )
        mac = miio_device_info.mac_address
        if mac is not None:
            device_info["connections"] = {
                (dr.CONNECTION_NETWORK_MAC, dr.format_mac(mac))
            }
        self._attr_device_info = device_info
