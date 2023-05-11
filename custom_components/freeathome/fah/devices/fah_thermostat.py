import asyncio
import logging

from .fah_device import FahDevice
from ..const import (
        FUNCTION_IDS_ROOM_TEMPERATURE_CONTROLLER,
        PID_ECO_MODE_ON_OFF_REQUEST,
        PID_CONTROLLER_ON_OFF_REQUEST,
        PID_ABSOLUTE_SETPOINT_TEMPERATURE,
        PID_SET_VALUE_TEMPERATURE,
        PID_CONTROLLER_ON_OFF,
        PID_STATUS_INDICATION,
        PID_MEASURED_TEMPERATURE,
        PID_MEASURED_HUMIDITY,
        PID_HEATING_DEMAND,
        PARAM_TEMPERATURE_CORRECTION,
    )

LOG = logging.getLogger(__name__)

class FahThermostat(FahDevice):
    """Free@Home thermostat """
    current_temperature = None
    current_humidity = None
    current_actuator = None
    target_temperature = None
    temperature_correction = None

    def pairing_ids(function_id=None):
        if function_id in FUNCTION_IDS_ROOM_TEMPERATURE_CONTROLLER:
            return {
                    "inputs": [
                        PID_ECO_MODE_ON_OFF_REQUEST,
                        PID_CONTROLLER_ON_OFF_REQUEST,
                        PID_ABSOLUTE_SETPOINT_TEMPERATURE,
                        ],
                    "outputs": [
                        PID_SET_VALUE_TEMPERATURE,
                        PID_CONTROLLER_ON_OFF,
                        PID_STATUS_INDICATION,
                        PID_MEASURED_TEMPERATURE,
                        PID_MEASURED_HUMIDITY,
                        PID_HEATING_DEMAND,
                        ]
                    }

    def parameter_ids(function_id=None):
        if function_id in FUNCTION_IDS_ROOM_TEMPERATURE_CONTROLLER:
            return {
                    "parameters": [
                        PARAM_TEMPERATURE_CORRECTION,
                        ]
                    }

    async def turn_on(self):
        """ Turn the thermostat on   """
        await self.client.set_datapoint(self.serialnumber, self.channel_id, self._datapoints[PID_ECO_MODE_ON_OFF_REQUEST], '0')
        await self.client.set_datapoint(self.serialnumber, self.channel_id, self._datapoints[PID_CONTROLLER_ON_OFF_REQUEST], '1')

    async def turn_off(self):
        """ Turn the thermostat off   """
        await self.client.set_datapoint(self.serialnumber, self.channel_id, self._datapoints[PID_CONTROLLER_ON_OFF_REQUEST], '0')

    async def eco_mode(self):
        """ Put the thermostat in eco mode   """
        await self.client.set_datapoint(self.serialnumber, self.channel_id, self._datapoints[PID_ECO_MODE_ON_OFF_REQUEST], '1')

    async def set_target_temperature(self, temperature):
        await self.client.set_datapoint(self.serialnumber, self.channel_id, self._datapoints[PID_ABSOLUTE_SETPOINT_TEMPERATURE], '%.2f' % temperature)

    async def set_temperature_correction(self, correction):
        await self.client.set_parameter(self.serialnumber, self.channel_id, self._parameters[PARAM_TEMPERATURE_CORRECTION], '%.2f' % correction)

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        self._state = state == '1'

    @property
    def ecomode(self):
        return self._eco_mode

    @ecomode.setter
    def ecomode(self, eco_mode):
        self._eco_mode = int(eco_mode) & 0x04 == 0x04

    def update_datapoint(self, dp, value):
        """Receive updated datapoint."""
        if self._datapoints.get(PID_SET_VALUE_TEMPERATURE) == dp:
            self.target_temperature = value
            LOG.info("thermostat %s (%s) dp %s target temp %s", self.name, self.lookup_key, dp, value)

        elif self._datapoints.get(PID_CONTROLLER_ON_OFF) == dp:
            self.state = value
            LOG.info("thermostat %s (%s) dp %s state %s", self.name, self.lookup_key, dp, value)

        elif self._datapoints.get(PID_STATUS_INDICATION) == dp:
            self.ecomode = value
            LOG.info("thermostat %s (%s) dp %s ecomode %s", self.name, self.lookup_key, dp, value)

        elif self._datapoints.get(PID_MEASURED_TEMPERATURE) == dp:
            self.current_temperature = value
            LOG.info("thermostat %s (%s) dp %s current temperature %s", self.name, self.lookup_key, dp, value)

        elif self._datapoints.get(PID_MEASURED_HUMIDITY) == dp:
            self.current_humidity = value
            LOG.info("thermostat %s (%s) dp %s current humidity %s", self.name, self.lookup_key, dp, value)

        elif self._datapoints.get(PID_HEATING_DEMAND) == dp:
            self.current_actuator = value
            LOG.info("thermostat %s (%s) dp %s current actuator %s", self.name, self.lookup_key, dp, value)

        else:
            LOG.info("thermostat %s (%s) unknown dp %s value %s", self.name, self.lookup_key, dp, value)


    def update_parameter(self, param, value):
        """Receive updated parameter."""
        if self._parameters.get(PARAM_TEMPERATURE_CORRECTION) == param:
            self.temperature_correction = value
            LOG.info("thermostat %s (%s) param %s temperatur correction %s", self.name, self.lookup_key, param, value)
