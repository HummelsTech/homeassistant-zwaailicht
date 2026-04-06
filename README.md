# Zwaailicht P2000 — Home Assistant Integration

A HACS-compatible Home Assistant custom integration that surfaces live P2000 emergency alerts from [zwaailicht.nu](https://zwaailicht.nu) as sensor entities. Configure one or more cities and get real-time alert data on your dashboards, NSPanel displays, and in automations.

<!-- Screenshot placeholder: add a screenshot of a dashboard card showing a P2000 alert -->

## Installation

### HACS (recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu → **Custom repositories**
3. Add `https://github.com/graus/homeassistant-zwaailicht` as an **Integration**
4. Search for "Zwaailicht P2000" and install
5. Restart Home Assistant

### Manual

Copy the `custom_components/zwaailicht` folder into your Home Assistant `config/custom_components/` directory and restart.

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for "Zwaailicht P2000"
3. Enter the city slug as used on zwaailicht.nu (e.g. `amsterdam`, `utrecht`, `rotterdam`)
4. Optionally adjust the update interval (default: 60s) and maximum distance filter

You can add multiple cities — each becomes a separate sensor entity.

## Sensors

Each configured city creates a sensor `sensor.zwaailicht_{stad}` with:

- **State**: title of the most recent alert
- **Attributes**: `dienst`, `timestamp`, `link`, `capcode`, `latitude`, `longitude`, `distance_km`, `piek_url`, `recent_alerts` (last 10)
- **Icon**: dynamic based on dienst (fire truck, ambulance, police badge, lifebuoy)

## Events

A `zwaailicht_new_alert` event fires for each new alert (not on every poll). Use this in automations:

```yaml
automation:
  - alias: "P2000 Alert on NSPanel"
    trigger:
      - platform: event
        event_type: zwaailicht_new_alert
        event_data:
          stad: amsterdam
          dienst: brandweer
    action:
      - service: notify.nspanel
        data:
          message: "🚒 {{ trigger.event.data.title }} ({{ trigger.event.data.distance_km }}km)"
```

### Filter by distance in automations

If you don't set `max_distance_km` in the config, you can still filter per automation:

```yaml
    condition:
      - condition: template
        value_template: "{{ trigger.event.data.distance_km | float < 5 }}"
```

## Links

- [zwaailicht.nu](https://zwaailicht.nu) — P2000 alerts for the Netherlands
