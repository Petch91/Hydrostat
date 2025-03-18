from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_time_interval
from datetime import timedelta
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Ajoute le capteur binaire au système"""
    sensor_entity_id = config.get("sensor")
    if not sensor_entity_id:
        _LOGGER.error("Aucun capteur d'humidité spécifié ! Ajoutez 'sensor: sensor.nom_du_capteur' dans configuration.yaml")
        return

    sensor = HumiditeAlerte(hass, sensor_entity_id)
    async_add_entities([sensor])
    sensor.start_tracking()

class HumiditeAlerte(Entity):
    """Binary Sensor qui surveille l'humidité"""

    def __init__(self, hass, sensor_entity_id):
        self._hass = hass
        self._sensor_entity_id = sensor_entity_id
        self._state = False
        self._last_humidity = None
        self._attr_name = f"Alerte Humidité ({sensor_entity_id})"
        self._attr_unique_id = f"humidite_alerte_{sensor_entity_id}"
        onHumidity = 0

    @property
    def name(self):
        return f"Alerte Humidité ({self._sensor_entity_id})"

    @property
    def is_on(self):
        return self._state

    def start_tracking(self):
        """Démarre le suivi de l'humidité toutes les 5 minutes"""
        async_track_time_interval(self._hass, self.update_humidity, timedelta(minutes=5))

    def update_humidity(self, _):
        """Vérifie l'humidité et met à jour l'alerte"""
        sensor = self._hass.states.get(self._sensor_entity_id)

        if sensor is None:
            _LOGGER.warning(f"Le capteur {self._sensor_entity_id} n'existe pas !")
            return

        try:
            current_humidity = float(sensor.state)
        except ValueError:
            _LOGGER.warning(f"Impossible de lire l'humidité du capteur {self._sensor_entity_id} !")
            return

        # Vérification de l'augmentation
        if self._state is False:
            if self._last_humidity is not None:
                variation = current_humidity - self._last_humidity
                if variation > 8:
                    self._state = True
                    onHumidity = current_humidity
            self._last_humidity = current_humidity
        else:
            variation = onHumidity - current_humidity
            if variation >= 5:
                self._state = False
            if variation < 0:
                onHumidity = current_humidity

        self.async_write_ha_state()
