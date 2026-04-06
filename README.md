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
3. Choose a feed type:
   - **Meldingen** — individual P2000 alerts for a specific city
   - **Pieken** — notable multi-unit incidents across the Netherlands
4. For meldingen: enter the city slug as used on zwaailicht.nu (e.g. `amsterdam`, `utrecht`)
5. Optionally adjust the update interval (default: 60s) and maximum distance filter

You can add multiple entries — multiple cities and/or pieken.

## Sensors

### Meldingen (`sensor.zwaailicht_{stad}`)

- **State**: title of the most recent alert (e.g. "🚑 A1 Spoed — Brouwersgracht, Amsterdam")
- **Attributes**:
  - `dienst` — ambulance, brandweer, politie, knrm
  - `timestamp` — alert timestamp (ISO 8601)
  - `link` — URL to the alert on zwaailicht.nu
  - `stad` — city slug
  - `prioriteit_code` — priority code (A1, A2, B1, B2, P1, P2, etc.)
  - `prioriteit` — priority label (Spoed, Urgent, Gepland vervoer, etc.)
  - `locatie` — street/location name
  - `summary` — full summary text
  - `eenheid` — responding unit (e.g. BAD-01)
  - `type` — incident type (Medisch, Brand, etc.)
  - `latitude` / `longitude` — incident coordinates (when available)
  - `distance_km` — distance from your HA home location (when coordinates available)
  - `recent_alerts` — list of the last 10 alerts
- **Icon**: dynamic based on dienst (fire truck, ambulance, police badge, lifebuoy)

### Pieken (`sensor.zwaailicht_pieken`)

- **State**: title of the most recent piek (e.g. "Zeer grote industriebrand Vaart Obdam")
- **Attributes**: same structure as meldingen, with `dienst` set to `piek` and a longer narrative `summary`

## Events

Two event types fire for genuinely new entries (not on every poll):

- `zwaailicht_new_alert` — new meldingen entry
- `zwaailicht_new_piek` — new pieken entry

### Example: flash NSPanel on nearby brandweer alert

```yaml
automation:
  - alias: "P2000 Brandweer Alert on NSPanel"
    trigger:
      - platform: event
        event_type: zwaailicht_new_alert
        event_data:
          stad: amsterdam
          dienst: brandweer
    condition:
      - condition: template
        value_template: "{{ trigger.event.data.distance_km | float(999) < 5 }}"
    action:
      - service: notify.nspanel
        data:
          message: "🔥 {{ trigger.event.data.title }} ({{ trigger.event.data.distance_km }}km)"
```

### Example: notify on pieken in your area

```yaml
automation:
  - alias: "Piek Alert Nearby"
    trigger:
      - platform: event
        event_type: zwaailicht_new_piek
    condition:
      - condition: template
        value_template: "{{ trigger.event.data.distance_km | float(999) < 10 }}"
    action:
      - service: notify.mobile_app
        data:
          title: "P2000 Piek"
          message: "{{ trigger.event.data.title }}"
```

### Example: filter by priority only

```yaml
    condition:
      - condition: template
        value_template: "{{ trigger.event.data.prioriteit_code in ['A1', 'P1'] }}"
```

## Distance filtering

Alerts with coordinates include a `distance_km` attribute calculated from your Home Assistant home location. You can filter on distance in two ways:

1. **In the config**: set "Maximum distance (km)" to only surface alerts within that radius. Alerts without coordinates are always included.
2. **In automations**: use a template condition on `trigger.event.data.distance_km` (see examples above).

## Links

- [zwaailicht.nu](https://zwaailicht.nu) — P2000 alerts for the Netherlands
