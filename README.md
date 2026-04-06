# Zwaailicht P2000 — Home Assistant Integration

A HACS-compatible Home Assistant custom integration that surfaces live P2000 emergency alerts from [zwaailicht.nu](https://zwaailicht.nu) as sensor entities. Set a radius around your home and get notified about nearby incidents on your dashboards, NSPanel displays, and in automations.

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
3. Set a **radius** (km) around your HA home location — only alerts within this radius are shown
4. Toggle **pieken** on/off — notable multi-unit incidents
5. Optionally adjust the update interval (default: 60s, minimum: 30s)

That's it. The integration polls the national feed and filters by distance from your home.

## Sensors

### Meldingen (`sensor.zwaailicht_meldingen`)

- **State**: title of the most recent nearby alert (e.g. "🚑 A1 Spoed — Brouwersgracht, Amsterdam")
- **Attributes**:
  - `dienst` — ambulance, brandweer, politie, knrm
  - `timestamp` — alert timestamp (ISO 8601)
  - `link` — URL to the alert on zwaailicht.nu
  - `stad` — city
  - `prioriteit_code` — priority code (A1, A2, B1, B2, P1, P2, etc.)
  - `prioriteit` — priority label (Spoed, Urgent, Gepland vervoer, etc.)
  - `locatie` — street/location name
  - `summary` — full summary text
  - `eenheid` — responding unit (e.g. BAD-01)
  - `type` — incident type (Medisch, Brand, etc.)
  - `latitude` / `longitude` — incident coordinates
  - `distance_km` — distance from your home location
  - `recent_alerts` — list of the last 10 nearby alerts

### Pieken (`sensor.zwaailicht_pieken`)

Created when pieken is enabled. Same attribute structure, with `dienst` set to `piek` and longer narrative summaries.

## Events

Two event types fire for genuinely new entries within your radius (not on every poll):

- `zwaailicht_new_alert` — new melding nearby
- `zwaailicht_new_piek` — new piek nearby

### Example: flash NSPanel on nearby brandweer alert

```yaml
automation:
  - alias: "P2000 Brandweer Alert"
    trigger:
      - platform: event
        event_type: zwaailicht_new_alert
        event_data:
          dienst: brandweer
    action:
      - service: notify.nspanel
        data:
          message: "🔥 {{ trigger.event.data.title }} ({{ trigger.event.data.distance_km }}km)"
```

### Example: notify on nearby pieken

```yaml
automation:
  - alias: "Piek Alert"
    trigger:
      - platform: event
        event_type: zwaailicht_new_piek
    action:
      - service: notify.mobile_app
        data:
          title: "P2000 Piek"
          message: "{{ trigger.event.data.title }} ({{ trigger.event.data.distance_km }}km)"
```

### Example: filter by priority

```yaml
    condition:
      - condition: template
        value_template: "{{ trigger.event.data.prioriteit_code in ['A1', 'P1'] }}"
```

## Links

- [zwaailicht.nu](https://zwaailicht.nu) — P2000 alerts for the Netherlands
