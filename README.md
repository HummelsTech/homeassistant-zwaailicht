<p align="center">
  <img src="custom_components/zwaailicht/icon.png" alt="Zwaailicht" width="80" />
</p>

# Zwaailicht P2000 — Home Assistant Integration

A HACS-compatible Home Assistant custom integration that surfaces live P2000 emergency alerts from [zwaailicht.nu](https://zwaailicht.nu) as sensor entities. Set a radius around your home and get notified about nearby incidents on your dashboards, NSPanel displays, and in automations.

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
4. Toggle **significant only** — filters out routine/low-priority alerts server-side (default: on)
5. Toggle **pieken** on/off — notable multi-unit incidents (default: on)
6. Optionally adjust the update interval (default: 60s, minimum: 30s)

That's it. The integration polls the national feed and filters by distance from your home. All settings can be changed later via **Settings → Devices & Services → Zwaailicht P2000 → Configure**.

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

Created when pieken is enabled. Same attribute structure, with `dienst` set to `piek`, longer narrative summaries, and `recent_pieken` instead of `recent_alerts`. Pieken without coordinates are always included (high-signal, low-volume).

## Events & Triggers

The integration fires Home Assistant events for each genuinely new entry within your configured radius. These only fire once per alert (not on every poll), making them ideal for automations.

### `zwaailicht_new_alert`

Fires when a new P2000 melding appears within your radius.

**Event data:**

| Field | Type | Example | Always present |
|---|---|---|---|
| `id` | string | `https://zwaailicht.nu/amsterdam/medisch/2026-04-06/4712c0` | yes |
| `title` | string | `🚑 A1 Spoed — Brouwersgracht, Amsterdam` | yes |
| `timestamp` | string | `2026-04-06T13:01:29Z` | yes |
| `link` | string | `https://zwaailicht.nu/amsterdam/medisch/...` | yes |
| `dienst` | string | `ambulance`, `brandweer`, `politie`, `knrm` | yes |
| `stad` | string | `amsterdam` | yes |
| `latitude` | float | `52.3781` | yes |
| `longitude` | float | `4.8870` | yes |
| `distance_km` | float | `2.3` | yes |
| `prioriteit_code` | string | `A1`, `A2`, `B1`, `P1`, `P2` | when parseable |
| `prioriteit` | string | `Spoed`, `Urgent`, `Gepland vervoer` | when parseable |
| `locatie` | string | `Brouwersgracht` | when parseable |
| `summary` | string | `Ambulance melding. Prioriteit: Spoed. Type: Medisch.` | when available |
| `eenheid` | string | `BAD-01` | when in summary |
| `type` | string | `Medisch`, `Brand` | when in summary |

### `zwaailicht_new_piek`

Fires when a new piek (notable multi-unit incident) appears. Same fields as above, except:
- `dienst` is always `piek`
- `summary` contains a longer narrative description
- `prioriteit_code`, `prioriteit`, `locatie`, `eenheid`, `type` are not present
- `latitude`, `longitude`, `distance_km` may be absent (pieken without coordinates are included)

## Automation Examples

### Flash NSPanel on nearby brandweer alert

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

### Push notification for nearby ambulance spoed

```yaml
automation:
  - alias: "Ambulance Spoed Nearby"
    trigger:
      - platform: event
        event_type: zwaailicht_new_alert
        event_data:
          dienst: ambulance
    condition:
      - condition: template
        value_template: "{{ trigger.event.data.prioriteit_code == 'A1' }}"
    action:
      - service: notify.mobile_app_phone
        data:
          title: "🚑 Ambulance A1"
          message: "{{ trigger.event.data.locatie }}, {{ trigger.event.data.stad }} ({{ trigger.event.data.distance_km }}km)"
```

### Notify on nearby pieken

```yaml
automation:
  - alias: "Piek Alert"
    trigger:
      - platform: event
        event_type: zwaailicht_new_piek
    action:
      - service: notify.mobile_app_phone
        data:
          title: "P2000 Piek — {{ trigger.event.data.stad }}"
          message: "{{ trigger.event.data.title }}"
```

### Only react to very close alerts (< 2km)

```yaml
automation:
  - alias: "Very Close Alert"
    trigger:
      - platform: event
        event_type: zwaailicht_new_alert
    condition:
      - condition: template
        value_template: "{{ trigger.event.data.distance_km < 2 }}"
    action:
      - service: light.turn_on
        target:
          entity_id: light.warning_lamp
        data:
          color_name: red
          flash: long
```

### Filter by priority — only spoed/P1

```yaml
    condition:
      - condition: template
        value_template: "{{ trigger.event.data.prioriteit_code in ['A1', 'P1'] }}"
```

### Sensor state change trigger

You can also trigger on the sensor state itself (changes when a new alert arrives within radius):

```yaml
automation:
  - alias: "New Nearby Alert"
    trigger:
      - platform: state
        entity_id: sensor.zwaailicht_meldingen
    action:
      - service: notify.mobile_app_phone
        data:
          message: "{{ states('sensor.zwaailicht_meldingen') }}"
```

## Links

- [zwaailicht.nu](https://zwaailicht.nu) — P2000 alerts for the Netherlands
