""" Support for Free@Home thermostats """

import logging
import voluptuous as vol

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (HVAC_MODE_HEAT_COOL, HVAC_MODE_OFF,
                                                    SUPPORT_PRESET_MODE,
                                                    SUPPORT_TARGET_TEMPERATURE)
from homeassistant.const import (ATTR_TEMPERATURE, TEMP_CELSIUS)
from homeassistant.helpers import config_validation as cv, entity_platform, service

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_devices, discovery_info=None):
    """ thermostat specific code."""
    _LOGGER.info('FreeAtHome setup thermostat')

    fah = hass.data[DOMAIN][config_entry.entry_id]

    devices = fah.get_devices('thermostat')



    for device_object in devices:
        async_add_devices([FreeAtHomeThermostat(device_object)])
    
    # Add a custom entity service that allows to change the temperature correction
    platform = entity_platform.current_platform.get()
    platform.async_register_entity_service(
            "thermostat_temperature_correction",
            {
               vol.Required('temperature_correction'): vol.Coerce(float),
            },
            "async_set_temperature_correction",
        )


# ch0, odp0008 = 1 == on
# ch0, odp0006 = 19 == target temp

# ch0, odp0008 = 0 == off
# ch0, odp0006 = 7 == ??????????????????????

# ch0, odp0009 = 68 == eco mode on
# ch0, odp0006 = 16 == target temp in eco mode (param pm0000 == 3)

# ch0, odp0009 = 65 = eco mode off
# ch0, odp0006 = 19 = target temp

# ch0, odp0010 = 22.1 = current temperature

# pm0000 = temperature reduction in ECO mode
# pm0001 = temperature correction
# pm0002 = target temperature
# pm0003 = delay
# pm0004 = 60 ?
# pm0005 = 
# pm0006 = 0 ?
# pm0007 = 
# pm0008 = 14 ? could be max positive range from current target
# pm0009 = -14 ? could be max negative range from current target
# pm000a = 1 ?
# pm000b = led backlight% (day?)
# pm000c = led backlight% (night?)


class FreeAtHomeThermostat(ClimateEntity):
    """ Free@home thermostat """
    thermostat_device = None
    _name = ''

    def __init__(self, device):
        self.thermostat_device = device
        self._name = self.thermostat_device.name


    @property
    def extra_state_attributes(self):
        """Return device specific state attributes."""
        attr = {"valve":self.current_actuator,"temperature_correction":self.temperature_correction}
        return attr

    @property
    def name(self):
        """Return the display name of this thermostat."""
        return self._name

    @property
    def device_info(self):
        """Return thermostat device info."""
        return self.thermostat_device.device_info

    @property
    def unique_id(self):
        """Return the ID """
        return self.thermostat_device.serialnumber + '/' + self.thermostat_device.channel_id

    @property
    def should_poll(self):
        """Return that polling is not necessary."""
        return False

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return float(self.thermostat_device.current_temperature)

    @property
    def current_humidity(self):
        """Return the current temperature."""
        return int(self.thermostat_device.current_humidity)

    @property
    def temperature_correction(self):
        """Return the current temperature_correction."""
        if self.thermostat_device.temperature_correction is None:
            return None
        return float(self.thermostat_device.temperature_correction)

    @property
    def current_actuator(self):
        """Return the current heating actuator state."""
        return float(self.thermostat_device.current_actuator)

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        if self.hvac_mode == HVAC_MODE_OFF:
            return None
        return float(self.thermostat_device.target_temperature)

    @property
    def temperature_unit(self):
        """Return the unit of measurement used by the platform."""
        return TEMP_CELSIUS

    @property
    def target_temperature_step(self):
        return 0.5

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE

    @property
    def hvac_mode(self):
        if not self.thermostat_device.state:
            return HVAC_MODE_OFF
        else:
            return HVAC_MODE_HEAT_COOL

    @property
    def hvac_modes(self):
        """Return the list of available hvac operation modes."""
        return [HVAC_MODE_HEAT_COOL, HVAC_MODE_OFF]

    @property
    def preset_modes(self):
        return ["none", "eco"]

    @property
    def preset_mode(self):
        if self.thermostat_device.ecomode:
            return "eco"
        else:
            return None

    @property
    def state(self):
        """Return current operation ie. heat, cool, idle."""
        if not self.thermostat_device.state:
            return HVAC_MODE_OFF
        else:
            return HVAC_MODE_HEAT_COOL

    @property
    def icon(self):
        return 'mdi:thermometer-lines'

    async def async_added_to_hass(self):
        """Register callback to update hass after device was changed."""

        async def after_update_callback(device):
            """Call after device was updated."""
            await self.async_update_ha_state(True)

        self.thermostat_device.register_device_updated_cb(after_update_callback)

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target operation mode."""
        if hvac_mode == HVAC_MODE_HEAT_COOL:
            await self.thermostat_device.turn_on()

        if hvac_mode == HVAC_MODE_OFF:
            await self.thermostat_device.turn_off()

    async def async_set_preset_mode(self, preset_mode):
        """Set new preset mode."""
        if preset_mode == "eco":
            await self.thermostat_device.eco_mode()
        else:
            await self.thermostat_device.turn_on()

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        await self.thermostat_device.set_target_temperature(temperature)

    async def async_set_temperature_correction(self, **kwargs):
        """Set new temperature_correction."""
        temperature_correction = kwargs.get("temperature_correction")
        await self.thermostat_device.set_temperature_correction(temperature_correction)

    async def async_update(self):
        pass
