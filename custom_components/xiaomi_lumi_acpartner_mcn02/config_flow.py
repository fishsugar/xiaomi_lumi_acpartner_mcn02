"""Config flow for the integration."""

import logging
import socket
from typing import Any, override

from miio.airconditioningcompanionMCN import (
    MODEL_ACPARTNER_MCN02,
    AirConditioningCompanionMcn02,
)
from miio.exceptions import DeviceException
import probatio

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_DEVICE_ID, CONF_HOST, CONF_TOKEN, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.schema_config_entry_flow import (
    SchemaFlowFormStep,
    SchemaOptionsFlowHandlerWithReload,
)
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
)
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from .const import (
    CONF_MAX_TEMP,
    CONF_MIN_TEMP,
    DEFAULT_MAX_TEMP,
    DEFAULT_MIN_TEMP,
    DOMAIN,
)

RETRIEVING_TOKEN_URL = (
    "https://www.home-assistant.io/integrations/xiaomi_miio#retrieving-the-access-token"
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = probatio.Schema(
    {
        probatio.Required(CONF_HOST): str,
        probatio.Required(CONF_TOKEN): probatio.All(str, probatio.Length(32, 32)),
    }
)
STEP_AUTH_DATA_SCHEMA = probatio.Schema(
    {
        probatio.Optional(CONF_DEVICE_ID): TextSelector(
            TextSelectorConfig(read_only=True)
        ),
        probatio.Optional(CONF_HOST): TextSelector(TextSelectorConfig(read_only=True)),
        probatio.Required(CONF_TOKEN): probatio.All(str, probatio.Length(32, 32)),
    }
)
OPTIONS_SCHEMA = probatio.Schema(
    {
        probatio.Optional(CONF_MIN_TEMP, default=DEFAULT_MIN_TEMP): NumberSelector(
            NumberSelectorConfig(
                mode=NumberSelectorMode.BOX,
                unit_of_measurement="°C",
            )
        ),
        probatio.Optional(CONF_MAX_TEMP, default=DEFAULT_MAX_TEMP): NumberSelector(
            NumberSelectorConfig(
                mode=NumberSelectorMode.BOX,
                unit_of_measurement=UnitOfTemperature.CELSIUS,
            )
        ),
    }
)
OPTIONS_FLOW = {
    "init": SchemaFlowFormStep(OPTIONS_SCHEMA),
}


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, str]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """

    device = await hass.async_add_executor_job(
        _authenticate, data[CONF_HOST], data[CONF_TOKEN]
    )

    # Checking compatibility by read properties with no exception
    s = device.status()
    _ = s.is_on
    _ = s.target_temperature
    _ = s.fan_speed

    return {"device_id": _format_device_id(device.device_id)}


def _format_device_id(device_id: int) -> str:
    return f"{device_id:08X}"


def _authenticate(ip: str, token: str) -> AirConditioningCompanionMcn02:
    device = AirConditioningCompanionMcn02(ip, token)
    device.retry_count = 0
    try:
        device.send_handshake()  # type: ignore[no-untyped-call]
    except DeviceException as ex:
        raise CannotConnect from ex
    except socket.gaierror as ex:
        raise CannotConnect from ex

    try:
        device.info()
    except DeviceException as ex:
        raise InvalidAuth from ex

    return device


class XiaomiMcnConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for xiaomi_lumi_acpartner_mcn02."""

    VERSION = 1

    _device: AirConditioningCompanionMcn02

    @staticmethod
    @callback
    @override
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Create the options flow."""
        return SchemaOptionsFlowHandlerWithReload(config_entry, OPTIONS_FLOW)

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                data = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(data["device_id"])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=MODEL_ACPARTNER_MCN02,
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "retrieving_token_url": RETRIEVING_TOKEN_URL,
            },
        )

    async def async_step_discovery_auth(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Finish configuration after discovery."""

        device = self._device

        if user_input is not None:
            user_input[CONF_HOST] = device.ip
            return self.async_create_entry(
                title=MODEL_ACPARTNER_MCN02,
                data={**user_input, CONF_HOST: device.ip},
            )
        return self.async_show_form(
            step_id="discovery_auth",
            data_schema=self.add_suggested_values_to_schema(
                STEP_AUTH_DATA_SCHEMA,
                {
                    CONF_HOST: device.ip,
                    CONF_DEVICE_ID: device.device_id,
                },
            ),
            description_placeholders={
                "retrieving_token_url": RETRIEVING_TOKEN_URL,
            },
        )

    @override
    async def async_step_dhcp(
        self, discovery_info: DhcpServiceInfo
    ) -> ConfigFlowResult:
        """Handle dhcp discovery."""

        device = AirConditioningCompanionMcn02(discovery_info.ip)
        try:
            await self.hass.async_add_executor_job(device.send_handshake)
        except DeviceException as e:
            if str(e).startswith("Unable to discover the device "):
                return self.async_abort(reason="no_devices_found")
            return self.async_abort(reason="cannot_connect")

        await self.async_set_unique_id(_format_device_id(device.device_id))
        self._abort_if_unique_id_configured()

        self.context["title_placeholders"] = {
            "model": device.model,
            "host": device.ip,
        }

        self._device = device
        return await self.async_step_discovery_auth()


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
