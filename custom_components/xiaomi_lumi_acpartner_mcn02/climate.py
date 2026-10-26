"""climate platform."""

from collections.abc import Mapping
from typing import Any, override

from miio.airconditioningcompanionMCN import FanSpeed, OperationMode, SwingMode

from homeassistant.components.climate import (
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    SWING_OFF,
    SWING_ON,
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import Mcn02ConfigEntry
from .const import CONF_MAX_TEMP, CONF_MIN_TEMP, DEFAULT_MAX_TEMP, DEFAULT_MIN_TEMP
from .entity import Mcn02Entity

TARGET_TEMPERATURE_STEP = 1

DEFAULT_TIMEOUT = 10

ATTR_AC_MODEL = "ac_model"
ATTR_AC_STATE = "ac_state"
ATTR_QUICK_COOL_STATE = "quick_cool_state"
ATTR_SLEEP_STATE = "sleep_state"
ATTR_LIST_CRC32 = "list_crc32"


_SUPPORTED_FEATURES_ALL = (
    ClimateEntityFeature.TARGET_TEMPERATURE
    | ClimateEntityFeature.FAN_MODE
    | ClimateEntityFeature.TURN_OFF
    | ClimateEntityFeature.TURN_ON
    | ClimateEntityFeature.SWING_MODE
)

_HVAC_MODE_TO_DEVICE = {
    HVACMode.AUTO: OperationMode.Auto,
    HVACMode.HEAT: OperationMode.Heat,
    HVACMode.COOL: OperationMode.Cool,
    HVACMode.DRY: OperationMode.Dehumidify,
    HVACMode.FAN_ONLY: OperationMode.Ventilate,
}
_HVAC_MODE_FROM_DEVICE = {v: k for k, v in _HVAC_MODE_TO_DEVICE.items()}

_FAN_MODE_TO_DEVICE = {
    FAN_AUTO: FanSpeed.Auto,
    FAN_HIGH: FanSpeed.High,
    FAN_MEDIUM: FanSpeed.Medium,
    FAN_LOW: FanSpeed.Low,
}
_FAN_MODE_FROM_DEVICE = {v: k for k, v in _FAN_MODE_TO_DEVICE.items()}

_SWING_MODE_TO_DEVICE = {SWING_ON: SwingMode.On, SWING_OFF: SwingMode.Off}
_SWING_MODE_FROM_DEVICE = {v: k for k, v in _SWING_MODE_TO_DEVICE.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: Mcn02ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the platform from config."""

    async_add_entities([_Entity(entry)])


class _Entity(ClimateEntity, Mcn02Entity):
    """Representation of a climate."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = TARGET_TEMPERATURE_STEP
    _attr_has_entity_name = True
    _attr_translation_key = "ac"

    def __init__(
        self,
        config_entry: Mcn02ConfigEntry,
    ) -> None:
        """Initialize the climate entity."""

        super().__init__(config_entry)

        self._attr_unique_id = self._device_id

        self._attr_available = False
        self._attr_extra_state_attributes = {}
        self._client = config_entry.runtime_data.client

        self._attr_min_temp = config_entry.options.get(CONF_MIN_TEMP, DEFAULT_MIN_TEMP)
        self._attr_max_temp = config_entry.options.get(CONF_MAX_TEMP, DEFAULT_MAX_TEMP)

        self._attr_hvac_modes = [*_HVAC_MODE_TO_DEVICE.keys(), HVACMode.OFF]

        self._attr_fan_modes = [speed.name.lower() for speed in FanSpeed]
        self._attr_swing_modes = [mode.name.lower() for mode in SwingMode]

        self._update_with_coordinator()

    @override
    def turn_on(self) -> None:
        """Turn the miio device on."""
        self._device.on()
        self._client.update_status()

    @override
    def turn_off(self) -> None:
        """Turn the miio device off."""
        self._device.off()
        self._client.update_status()

    @override
    def _handle_coordinator_update(self) -> None:
        self._update_with_coordinator()
        super()._handle_coordinator_update()

    def _update_with_coordinator(self) -> None:
        self._attr_available = True
        if not self._client.is_on:
            self._attr_hvac_mode = HVACMode.OFF
        else:
            self._attr_hvac_mode = (
                _HVAC_MODE_FROM_DEVICE[self._client.mode]
                if self._client.mode is not None
                else None
            )

        self._attr_fan_mode = (
            _FAN_MODE_FROM_DEVICE[self._client.fan_level]
            if self._client.fan_level is not None
            else None
        )

    async def _async_send(self, command: str, parameters: Any = None) -> Any:
        return await self.hass.async_add_executor_job(
            self._device.send, command, parameters
        )

    @property
    @override
    def target_temperature(self) -> float | None:
        """Get target temperature."""
        return self._client.target_temperature

    @property
    @override
    def swing_mode(self) -> str | None:
        """Return the swing setting."""
        return (
            _SWING_MODE_FROM_DEVICE[self._client.swing_mode]
            if self._client.swing_mode is not None
            else None
        )

    @property
    @override
    def supported_features(self) -> ClimateEntityFeature:
        """Return the list of supported features."""
        f = _SUPPORTED_FEATURES_ALL
        if not self._client.swing_supported:
            f &= ~ClimateEntityFeature.SWING_MODE
        return f

    @override
    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set target temperature."""
        await self.hass.async_add_executor_job(
            self._client.set_target_temperature, kwargs[ATTR_TEMPERATURE]
        )
        await self.coordinator.async_refresh()

    @override
    async def async_set_swing_mode(self, swing_mode: str) -> None:
        """Set new target swing operation."""
        value = {
            SWING_ON: SwingMode.On,
            SWING_OFF: SwingMode.Off,
        }[swing_mode].value
        await self._async_send("set_ver_swing", [value])
        await self.coordinator.async_refresh()

    @override
    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set the fan mode."""
        value = _FAN_MODE_TO_DEVICE[fan_mode].value
        await self._async_send("set_fan_level", [value])
        await self.coordinator.async_refresh()

    @override
    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        if hvac_mode == HVACMode.OFF:
            await self.hass.async_add_executor_job(self._device.off)
        else:
            mode_value = _HVAC_MODE_TO_DEVICE[hvac_mode].value
            await self._async_send("set_mode", [mode_value])

            # When power is off, `set_mode` only turn on power, but not change mode.
            # Send `set_mode` again if needed.
            status = await self.hass.async_add_executor_job(self._device.status)
            if status.is_on and _HVAC_MODE_TO_DEVICE[hvac_mode] != status.mode:
                await self._async_send("set_mode", [mode_value])

        await self.coordinator.async_refresh()

    @property
    @override
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return entity specific state attributes."""
        result: dict[str, Any] = {}
        c = self._client
        if c.ac_model is not None:
            result[ATTR_AC_MODEL] = c.ac_model
        if c.ac_state is not None:
            result[ATTR_AC_STATE] = c.ac_state
        if c.quick_cool_state is not None:
            result[ATTR_QUICK_COOL_STATE] = c.quick_cool_state
        if c.sleep_state is not None:
            result[ATTR_SLEEP_STATE] = c.sleep_state
        if c.list_crc32 is not None:
            result[ATTR_LIST_CRC32] = c.list_crc32

        return result
