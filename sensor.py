"""Sensor platform for IBEX Price integration."""
import datetime
import logging
import random

import pytz
import requests

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_SCAN_INTERVAL

from .const import (
    DOMAIN, 
    DEFAULT_NAME, 
    DEFAULT_SCAN_INTERVAL, 
    DEFAULT_TIMEZONE, 
    DEFAULT_API_ENDPOINT,
    CONF_TIMEZONE,
    CONF_API_ENDPOINT
)

_LOGGER = logging.getLogger(__name__)

# Singleton instance to prevent multiple sensors
_sensor_instance = None


async def async_setup_entry(hass, config_entry, add_entities):
    """Set up IBEX Price sensor from config entry."""
    global _sensor_instance
    
    # Only create sensor if it doesn't exist
    if _sensor_instance is None:
        scan_interval = config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        timezone = config_entry.data.get(CONF_TIMEZONE, DEFAULT_TIMEZONE)
        api_endpoint = config_entry.data.get(CONF_API_ENDPOINT, DEFAULT_API_ENDPOINT)
        
        _sensor_instance = IbexPriceSensor(scan_interval, timezone, api_endpoint)
    
    add_entities([_sensor_instance])


class IbexPriceSensor(SensorEntity):
    def __init__(self, scan_interval, timezone, api_endpoint):
        self._name = DEFAULT_NAME
        self._scan_interval = scan_interval
        self._timezone = timezone
        self._api_endpoint = api_endpoint
        self._state_eur = None
        self._cached_prices = {}
        self._cached_day = None
        self._session = None
        self._attr_icon = "mdi:cash-clock"
        self._attr_unique_id = "ibex_current_price_eur_mwh"
        self._attr_native_unit_of_measurement = "EUR/MWh"

    @property
    def name(self):
        return self._name

    @property
    def native_value(self):
        return self._state_eur

    @property
    def extra_state_attributes(self):
        attributes = {}
        
        if self._state_eur is not None:
            attributes["price_eur_kwh"] = self._state_eur / 1000
            
        return attributes

    @property
    def scan_interval(self):
        """Return the scan interval."""
        return datetime.timedelta(seconds=self._scan_interval)

    def update(self):
        """Update the sensor state."""
        try:
            # Use configured timezone
            try:
                tz = pytz.timezone(self._timezone)
            except pytz.UnknownTimeZoneError:
                _LOGGER.warning(f"Unknown timezone '{self._timezone}', falling back to CET")
                tz = pytz.timezone(DEFAULT_TIMEZONE)
                    
            now = datetime.datetime.now(tz)
            today = now.date()
            current_hour = now.hour
            current_minute = now.minute
            
            # Calculate current 15-minute interval (QH product number: 1-96)
            # QH 1 = 00:00-00:15, QH 2 = 00:15-00:30, etc.
            current_qh = (current_hour * 4) + (current_minute // 15) + 1

            # Don't call IBEX if we have the prices for today
            # Check for both QH (15-minute) and PH (hourly) cached data
            if self._cached_day == today and self._cached_prices:
                if current_qh in self._cached_prices:
                    # Have QH data cached
                    self._state_eur = self._cached_prices[current_qh]
                    _LOGGER.debug(f"Using cached IBEX price for QH {current_qh}")
                    return
                elif current_hour in self._cached_prices:
                    # Have PH data cached
                    self._state_eur = self._cached_prices[current_hour]
                    _LOGGER.debug(f"Using cached IBEX price for PH {current_hour + 1} (hour {current_hour})")
                    return

            _LOGGER.info(f"Fetching IBEX prices for date: {today}")
            
            # Initialize session if needed
            if self._session is None:
                self._session = requests.Session()
                self._session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Referer': 'https://ibex.bg/sdac-pv-bg/'
                })
                _LOGGER.debug("Initialized new session")

            # Get CSRF token using configured API endpoint
            try:
                token_response = self._session.get(
                    self._api_endpoint,
                    params={'action': 'get_csrf_token'},
                    timeout=10
                )
                token_response.raise_for_status()
                token_data = token_response.json()
                csrf_token = token_data.get('csrf_token')
                if not csrf_token:
                    raise ValueError("No CSRF token in response")
            except Exception as e:
                _LOGGER.error(f"Error getting CSRF token: {e}")
                return

            # Make API request with CSRF token using configured endpoint
            response = self._session.get(
                self._api_endpoint,
                params={
                    'action': 'get_data',
                    'date': today.strftime('%Y-%m-%d'),
                    'lang': 'bg',
                    'rand': random.random(),
                    'csrf_token': csrf_token
                },
                timeout=15
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Check if we have main_data in the response
            if "main_data" not in data or not data["main_data"]:
                _LOGGER.error("No main_data found in IBEX response.")
                self._state_eur = None
                return
            
            # Detect if we have QH (15-minute) or PH (hourly) products
            first_product = data["main_data"][0]["product"]
            is_qh_data = first_product.startswith("QH")
            
            # Parse prices from main_data array
            # QH: 15-minute intervals (QH 1-96)
            # PH: Hourly intervals (PH 1-24)
            self._cached_prices = {}
            
            for price_entry in data["main_data"]:
                try:
                    # Extract product number from product name (e.g., "QH 1" -> 1, "PH 1" -> 1)
                    product = price_entry["product"]
                    product_num = int(product.split()[1])
                    
                    # Parse price from JSON
                    eur = float(price_entry["price"])
                    
                    # Calculate cache key based on product type
                    if is_qh_data:
                        # QH: use product number directly (1-96)
                        cache_key = product_num
                    else:
                        # PH: convert to 0-indexed hour (PH 1 = hour 0, PH 2 = hour 1, etc.)
                        cache_key = product_num - 1
                    
                    self._cached_prices[cache_key] = eur
                except (ValueError, KeyError, IndexError) as e:
                    _LOGGER.warning(f"Invalid price format in entry: {price_entry}, error: {e}")
                    continue

            self._cached_day = today

            # Retrieve price for current time based on product type
            if is_qh_data:
                if current_qh in self._cached_prices:
                    self._state_eur = self._cached_prices[current_qh]
                    _LOGGER.debug(f"IBEX price for QH {current_qh} ({current_hour:02d}:{(current_minute // 15) * 15:02d}): EUR={self._state_eur}")
                else:
                    _LOGGER.warning(f"No price found in IBEX data for QH: {current_qh}")
                    self._state_eur = None
            else:
                if current_hour in self._cached_prices:
                    self._state_eur = self._cached_prices[current_hour]
                    _LOGGER.debug(f"IBEX price for PH {current_hour + 1} (hour {current_hour:02d}): EUR={self._state_eur}")
                else:
                    _LOGGER.warning(f"No price found in IBEX data for hour: {current_hour}")
                    self._state_eur = None

        except Exception as e:
            _LOGGER.error(f"Error while loading prices from IBEX: {e}")
            self._state_eur = None
    
    def __del__(self):
        """Cleanup session when sensor is destroyed."""
        if self._session:
            self._session.close()
            _LOGGER.debug("Closed HTTP session")
            