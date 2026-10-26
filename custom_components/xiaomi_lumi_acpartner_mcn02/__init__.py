"""The xiaomi_lumi_acpartner_mcn02 integration."""

from miio.airconditioningcompanionMCN import AirConditioningCompanionMcn02

from homeassistant.const import CONF_HOST, CONF_TOKEN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .client import Mcn02Client
from .coordinator import Mcn02ConfigEntry, Mcn02Coordinator, McnRuntimeData

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.CLIMATE,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: Mcn02ConfigEntry) -> bool:
    """Set up integration from a config entry."""

    host = entry.data[CONF_HOST]
    token = entry.data[CONF_TOKEN]
    device = AirConditioningCompanionMcn02(host, token)
    try:
        await hass.async_add_executor_job(device.info)
    except Exception as ex:
        raise ConfigEntryNotReady from ex

    client = Mcn02Client(device)
    coordinator = Mcn02Coordinator(hass, entry, device, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = McnRuntimeData(device, coordinator, client)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: Mcn02ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
