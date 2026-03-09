# IBEX Price Sensor for Home Assistant

A Home Assistant custom integration that fetches current electricity market prices from the IBEX Bulgarian electricity exchange.

## Features

- **Real-time pricing**: Fetches current electricity prices with 15-minute granularity
- **EUR/MWh pricing**: Provides prices in Euro per Megawatt-hour
- **Automatic updates**: Updates every 15 minutes to match current pricing interval
- **Caching**: Efficiently caches daily pricing data to minimize API calls
- **Clean integration**: Uses modern Home Assistant config flow for easy setup

## Installation via HACS

1. Open HACS in your Home Assistant
2. Go to "Integrations"
3. Click the three dots menu and select "Custom repositories"
4. Add this repository URL: `https://github.com/stefan-tabakov/ibex-price-ha-sensor`
5. Select "Integration" as the category
6. Click "Add"
7. Search for "IBEX Price Sensor" and install it
8. Restart Home Assistant
9. Go to "Settings" > "Devices & Services" > "Integrations"
10. Click "+ Add Integration" and search for "IBEX Price Sensor"
11. Configure the sensor with your preferred name

## Manual Installation

1. Copy the `ibex-price-ha-sensor` folder to your `config/custom_components` directory
2. Restart Home Assistant
3. Go to "Settings" > "Devices & Services" > "Integrations"
4. Click "+ Add Integration" and search for "IBEX Price Sensor"

## Configuration

The integration requires minimal configuration:

- **Update Interval**: How often to fetch new prices in seconds (default: 900 seconds = 15 minutes, minimum: 60 seconds)
- **Timezone**: Timezone for price calculations (default: CET)
- **API Endpoint**: IBEX API endpoint URL (default: official IBEX API endpoint)

### Recommended Settings:
- **Update Interval**: 900 seconds (15 minutes) - matches IBEX pricing intervals
- **Timezone**: CET - matches Bulgarian market timezone
- **API Endpoint**: Leave default unless using alternative IBEX endpoint

## Sensor Data

The sensor provides:

- **State**: Current price in EUR/MWh
- **Attributes**: 
  - `price_eur_kwh`: Current price in EUR/kWh (for easier reading)

## Data Source

This integration fetches data from the official IBEX (Independent Bulgarian Energy Exchange) public API, providing reliable and up-to-date electricity market pricing for the Bulgarian market.

## Version History

- **v2.0**: Migrated to new JSON API with 15-minute interval pricing
- **v1.0**: Initial release with HTML scraping and hourly pricing

## License

This integration is provided as-is for personal use. Please respect the IBEX terms of service when using this integration.
