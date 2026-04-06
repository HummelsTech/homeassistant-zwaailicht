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
4. Optionally adjust the update interval (default: 60s, minimum: 30s)

You can add multiple cities — each becomes a separate sensor entity.

## Sensors

Each configured city creates a sensor `sensor.zwaailicht_{stad}` with:

- **State**: title of the most recent alert (e.g. "🚑 A1 Spoed — Brouwersgracht, Amsterdam")
- **Attributes**:
  - `dienst` — ambulance, brandweer, politie, knrm
  - `timestamp` — alert timestamp (ISO 8601)
  - `link` — URL to the alert on zwaailicht.nu
  - `prioriteit_code` — priority code (A1, A2, B1, B2, P1, P2, etc.)
  - `prioriteit` — priority label (Spoed, Urgent, Gepland vervoer, etc.)
  - `locatie` — street/location name
  - `summary` — full summary text
  - `eenheid` — responding unit (when available, e.g. BAD-01)
  - `type` — incident type (Medisch, Brand, etc.)
  - `recent_alerts` — list of the last 10 alerts
- **Icon**: dynamic based on dienst (fire truck, ambulance, police badge, lifebuoy)

## Events

A `zwaailicht_new_alert` event fires for each new alert (not on every poll). Use this in automations:

```yaml
automation:
  - alias: "P2000 Brandweer Alert on NSPanel"
    trigger:
      - platform: event
        event_type: zwaailicht_new_alert
        event_data:
          stad: amsterdam
          dienst: brandweer
    action:
      - service: notify.nspanel
        data:
          message: "🔥 {{ trigger.event.data.title }}"
```

### Filter by priority

Only trigger on the most urgent alerts:

```yaml
    condition:
      - condition: template
        value_template: "{{ trigger.event.data.prioriteit_code in ['A1', 'P1'] }}"
```

## Links

- [zwaailicht.nu](https://zwaailicht.nu) — P2000 alerts for the Netherlands
