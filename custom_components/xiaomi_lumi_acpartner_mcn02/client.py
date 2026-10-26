"""Handle communication with the device."""

# ruff: noqa: D101,D102,D107
from typing import Any, Literal, NamedTuple

from miio.airconditioningcompanionMCN import (
    AirConditioningCompanionMcn02,
    FanSpeed,
    OperationMode,
    SwingMode,
)
from miio.exceptions import DeviceException


class _RawProperties(NamedTuple):
    power: str
    mode: str
    tar_temp: int
    fan_level: str
    ver_swing: str
    load_power: float | Literal[""]
    ac_mode: int | Literal[""]
    ac_state: str
    en_nnlight: int | Literal[""]
    quick_cool_state: int | Literal[""]
    sleep_state: int | Literal[""]
    list_crc32: int | Literal[""]
    match_state: int | Literal[""]


class Mcn02Client:
    _device: AirConditioningCompanionMcn02
    _props: _RawProperties
    _target_temperature: int | None = None
    _ac_model: str | None

    def __init__(self, device: AirConditioningCompanionMcn02) -> None:
        self._device = device

    def update_status(self, full_update: bool = False) -> None:
        """Update the status of the device."""

        if full_update:
            try:
                self._ac_model = self._device.send("get_ac_model")
            except DeviceException:
                self._ac_model = None

        values = self._device.get_properties(list(_RawProperties._fields))  # type: ignore[no-untyped-call]
        self._props = _RawProperties(*values)

        if not self._should_use_saved_temperature or self._target_temperature is None:
            # Discard saved temperature and use device temperature instead
            self._target_temperature = self._props.tar_temp

    @property
    def _should_use_saved_temperature(self) -> bool:
        return not self.is_on or self.mode is OperationMode.Ventilate

    def set_target_temperature(self, value: int) -> None:
        self.update_status()
        if self._should_use_saved_temperature:
            self._target_temperature = value
        else:
            self._device.send("set_tar_temp", [value])

    @property
    def target_temperature(self) -> int | None:
        return self._target_temperature

    @property
    def is_on(self) -> bool:
        if self._props.power == "on":
            return True
        if self._props.power == "off":
            return False
        raise ValueError("Invalid status")

    @property
    def swing_supported(self) -> bool:
        return self._props.ver_swing != "unsupport"  # codespell:ignore unsupport

    @property
    def mode(self) -> OperationMode:
        return OperationMode(self._props.mode)

    @property
    def fan_level(self) -> FanSpeed | None:
        return FanSpeed(self._props.fan_level) if self._props.fan_level else None

    @property
    def swing_mode(self) -> SwingMode | None:
        return SwingMode(self._props.ver_swing) if self._props.ver_swing else None

    @property
    def ac_model(self) -> str | None:
        return self._ac_model

    @property
    def load_power(self) -> float | None:
        return self._props.load_power if self._props.load_power != "" else None

    @property
    def ac_mode(self) -> int | None:
        return self._props.ac_mode if self._props.ac_mode != "" else None

    def set_ac_mode(self, value: int) -> None:
        self._set_prop("ac_mode", value)

    @property
    def ac_state(self) -> str | None:
        return self._props.ac_state if self._props.ac_state != "" else None

    @property
    def en_nnlight(self) -> int | None:
        return self._props.en_nnlight if self._props.en_nnlight != "" else None

    def set_en_nnlight(self, value: int) -> None:
        self._set_prop("en_nnlight", value)

    @property
    def quick_cool_state(self) -> int | None:
        return (
            self._props.quick_cool_state if self._props.quick_cool_state != "" else None
        )

    @property
    def sleep_state(self) -> int | None:
        return self._props.sleep_state if self._props.sleep_state != "" else None

    @property
    def list_crc32(self) -> int | None:
        return self._props.list_crc32 if self._props.list_crc32 != "" else None

    @property
    def match_state(self) -> int | None:
        return self._props.match_state if self._props.match_state != "" else None

    def get_sleep_func(self) -> Any:
        return self._device.send("get_sleep_func")

    def get_quick_cool_func(self) -> Any:
        return self._device.send("get_quick_cool_func")

    def _set_prop(self, prop: str, value: Any) -> None:
        self._device.send("set_prop", {prop: value})
