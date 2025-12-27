# Pixel Magic Tool - Example Configurations

This file contains example configurations for common use cases with the Pixel Magic Tool Home Assistant integration.

## Table of Contents
- [Media Player Album Art](#media-player-album-art)
- [Weather Display](#weather-display)
- [Camera Snapshots](#camera-snapshots)
- [Notification Icons](#notification-icons)
- [Dynamic Image Rotation](#dynamic-image-rotation)
- [Using with Scripts](#using-with-scripts)
- [REST Command Integration](#rest-command-integration)

---

## Media Player Album Art

### Spotify Album Art on LED Matrix

```yaml
automation:
  - alias: "Display Spotify Album Art on WLED"
    description: "Updates LED matrix whenever song changes on Spotify"
    trigger:
      - platform: state
        entity_id: media_player.spotify
        attribute: entity_picture
    condition:
      - condition: state
        entity_id: media_player.spotify
        state: "playing"
    action:
      - service: pixelmagictool.send_to_wled
        data:
          image_url: "{{ state_attr('media_player.spotify', 'entity_picture') }}"
          wled_host: "192.168.1.100"
          width: 32
          height: 32
          brightness: 150
          pattern: "range"
          segment_id: 0
```

### Plex Now Playing

```yaml
automation:
  - alias: "Plex Album Art to WLED"
    trigger:
      - platform: state
        entity_id: media_player.plex
        to: "playing"
      - platform: state
        entity_id: media_player.plex
        attribute: entity_picture
    action:
      - service: pixelmagictool.send_to_wled
        data:
          image_url: "http://{{ states.sensor.homeassistant_ip.state }}:8123{{ state_attr('media_player.plex', 'entity_picture') }}"
          wled_host: "10.0.0.50"
          width: 64
          height: 64
          brightness: 200
          pattern: "range"
```

---

## Weather Display

### Current Weather Icon

```yaml
automation:
  - alias: "Display Weather Icon on LED Matrix"
    description: "Shows current weather as pixel art"
    trigger:
      - platform: state
        entity_id: weather.home
      - platform: time_pattern
        hours: "/1"  # Update every hour
    action:
      - service: pixelmagictool.send_to_wled
        data:
          image_url: >
            {% set condition = states('weather.home') %}
            {% set icon_map = {
              'sunny': 'https://example.com/icons/sunny.png',
              'cloudy': 'https://example.com/icons/cloudy.png',
              'rainy': 'https://example.com/icons/rainy.png',
              'snowy': 'https://example.com/icons/snowy.png'
            } %}
            {{ icon_map.get(condition, 'https://example.com/icons/default.png') }}
          wled_host: "192.168.1.100"
          width: 16
          height: 16
          brightness: 180
```

### Weather with Temperature Display

```yaml
script:
  weather_to_led:
    sequence:
      # First, show the weather icon
      - service: pixelmagictool.send_to_wled
        data:
          image_url: "{{ states.sensor.weather_icon_url.state }}"
          wled_host: "192.168.1.100"
          width: 32
          height: 32
          brightness: 200
          segment_id: 0
      # Then update a text segment with temperature (if you have one)
      - delay: 00:00:01
      - service: wled.effect
        data:
          entity_id: light.wled_matrix
          segment_id: 1
          effect: "Solid"
```

---

## Camera Snapshots

### Doorbell Camera on Motion

```yaml
automation:
  - alias: "Show Doorbell on LED Matrix"
    trigger:
      - platform: state
        entity_id: binary_sensor.front_door_motion
        to: "on"
    action:
      # Take a snapshot
      - service: camera.snapshot
        target:
          entity_id: camera.front_door
        data:
          filename: /config/www/snapshots/doorbell.jpg
      # Wait for file to be written
      - delay: 00:00:02
      # Convert and send to WLED
      - service: pixelmagictool.send_to_wled
        data:
          image_url: "http://homeassistant.local:8123/local/snapshots/doorbell.jpg"
          wled_host: "192.168.1.100"
          width: 64
          height: 64
          brightness: 255
          pattern: "range"
```

### Security Camera Feed (Periodic)

```yaml
automation:
  - alias: "Update LED with Camera Feed"
    trigger:
      - platform: time_pattern
        seconds: "/30"  # Every 30 seconds
    condition:
      - condition: state
        entity_id: binary_sensor.security_system_armed
        state: "on"
    action:
      - service: camera.snapshot
        target:
          entity_id: camera.backyard
        data:
          filename: /config/www/snapshots/backyard_latest.jpg
      - delay: 00:00:01
      - service: pixelmagictool.send_to_wled
        data:
          image_url: "http://homeassistant.local:8123/local/snapshots/backyard_latest.jpg"
          wled_host: "192.168.1.101"
          width: 32
          height: 32
          brightness: 128
```

---

## Notification Icons

### Status Icons Based on Conditions

```yaml
automation:
  - alias: "LED Status Indicator"
    trigger:
      - platform: state
        entity_id:
          - binary_sensor.front_door
          - binary_sensor.garage_door
          - alarm_control_panel.home
    action:
      - service: pixelmagictool.send_to_wled
        data:
          image_url: >
            {% if is_state('binary_sensor.front_door', 'on') %}
              http://homeassistant.local:8123/local/icons/door_open.png
            {% elif is_state('binary_sensor.garage_door', 'on') %}
              http://homeassistant.local:8123/local/icons/garage_open.png
            {% elif is_state('alarm_control_panel.home', 'armed_away') %}
              http://homeassistant.local:8123/local/icons/alarm_armed.png
            {% else %}
              http://homeassistant.local:8123/local/icons/home_secure.png
            {% endif %}
          wled_host: "192.168.1.100"
          width: 16
          height: 16
          brightness: 200
```

### Person Presence Indicator

```yaml
automation:
  - alias: "Show Who's Home"
    trigger:
      - platform: state
        entity_id:
          - person.john
          - person.jane
    action:
      - service: pixelmagictool.send_to_wled
        data:
          image_url: >
            {% set john_home = is_state('person.john', 'home') %}
            {% set jane_home = is_state('person.jane', 'home') %}
            {% if john_home and jane_home %}
              http://homeassistant.local:8123/local/avatars/both.png
            {% elif john_home %}
              http://homeassistant.local:8123/local/avatars/john.png
            {% elif jane_home %}
              http://homeassistant.local:8123/local/avatars/jane.png
            {% else %}
              http://homeassistant.local:8123/local/avatars/empty.png
            {% endif %}
          wled_host: "192.168.1.100"
          width: 32
          height: 32
```

---

## Dynamic Image Rotation

### Slideshow of Images

```yaml
script:
  led_slideshow:
    sequence:
      # Image 1
      - service: pixelmagictool.send_to_wled
        data:
          image_url: "http://homeassistant.local:8123/local/slideshow/image1.png"
          wled_host: "192.168.1.100"
          width: 32
          height: 32
      - delay: 00:00:10
      
      # Image 2
      - service: pixelmagictool.send_to_wled
        data:
          image_url: "http://homeassistant.local:8123/local/slideshow/image2.png"
          wled_host: "192.168.1.100"
          width: 32
          height: 32
      - delay: 00:00:10
      
      # Image 3
      - service: pixelmagictool.send_to_wled
        data:
          image_url: "http://homeassistant.local:8123/local/slideshow/image3.png"
          wled_host: "192.168.1.100"
          width: 32
          height: 32

automation:
  - alias: "Run LED Slideshow"
    trigger:
      - platform: time_pattern
        minutes: "/1"  # Every minute
    action:
      - service: script.turn_on
        target:
          entity_id: script.led_slideshow
```

---

## Using with Scripts

### Convert First, Then Use

```yaml
script:
  convert_and_store:
    alias: "Convert Image to Sensor"
    sequence:
      - service: pixelmagictool.convert_image
        data:
          image_url: "{{ image_url }}"
          width: 32
          height: 32
          brightness: 200
          segment_id: 0
      - delay: 00:00:02
      # Now the sensor has the JSON
      - service: notify.mobile_app
        data:
          message: "Image converted and stored in sensor"
```

### Conditional Conversion

```yaml
script:
  smart_led_update:
    sequence:
      - choose:
          # If it's daytime, use bright image
          - conditions:
              - condition: sun
                after: sunrise
                before: sunset
            sequence:
              - service: pixelmagictool.send_to_wled
                data:
                  image_url: "{{ image_url }}"
                  wled_host: "192.168.1.100"
                  brightness: 255
          # If it's nighttime, use dim image
          - conditions:
              - condition: sun
                after: sunset
            sequence:
              - service: pixelmagictool.send_to_wled
                data:
                  image_url: "{{ image_url }}"
                  wled_host: "192.168.1.100"
                  brightness: 50
```

---

## REST Command Integration

### Using Stored Conversion with REST Command

First, define the REST command in `configuration.yaml`:

```yaml
rest_command:
  send_wled_json:
    url: "http://{{ wled_host }}/json/state"
    method: POST
    content_type: "application/json"
    payload: "{{ wled_json }}"
```

Then use it in automation:

```yaml
automation:
  - alias: "Convert and Send via REST"
    trigger:
      - platform: state
        entity_id: sensor.album_art
        attribute: url
    action:
      # Convert and store
      - service: pixelmagictool.convert_image
        data:
          image_url: "{{ state_attr('sensor.album_art', 'url') }}"
          width: 32
          height: 32
      # Wait for conversion
      - delay: 00:00:02
      # Send using REST command
      - service: rest_command.send_wled_json
        data:
          wled_host: "192.168.1.100"
          wled_json: "{{ state_attr('sensor.pixel_magic_tool_last_conversion', 'wled_json') }}"
```

---

## Advanced: Multi-Panel Setup

### Different Images on Multiple WLED Devices

```yaml
automation:
  - alias: "Sync Multiple LED Matrices"
    trigger:
      - platform: state
        entity_id: media_player.spotify
        attribute: entity_picture
    action:
      # Main display - full res
      - service: pixelmagictool.send_to_wled
        data:
          image_url: "{{ state_attr('media_player.spotify', 'entity_picture') }}"
          wled_host: "192.168.1.100"
          width: 64
          height: 64
          brightness: 200
      
      # Secondary display - lower res
      - service: pixelmagictool.send_to_wled
        data:
          image_url: "{{ state_attr('media_player.spotify', 'entity_picture') }}"
          wled_host: "192.168.1.101"
          width: 32
          height: 32
          brightness: 150
      
      # Kitchen display - smaller
      - service: pixelmagictool.send_to_wled
        data:
          image_url: "{{ state_attr('media_player.spotify', 'entity_picture') }}"
          wled_host: "192.168.1.102"
          width: 16
          height: 16
          brightness: 100
```

---

## Tips and Best Practices

1. **Use Templates**: Leverage Jinja2 templates for dynamic image selection
2. **Add Delays**: When taking camera snapshots, add small delays before conversion
3. **Error Handling**: Use `try` in scripts to handle failed conversions gracefully
4. **Brightness Automation**: Adjust brightness based on time of day or ambient light sensors
5. **Test First**: Use `pixelmagictool.convert_image` first to test without sending to WLED
6. **Pattern Selection**: 
   - Use `range` for most cases (best compression)
   - Use `index` for complex images with many unique pixels
   - Use `individual` only for very small images
7. **Image Hosting**: Host frequently-used images locally in `/config/www/` for faster access
8. **Sensor States**: Check `sensor.pixel_magic_tool_last_conversion` state before using stored JSON

---

For more information, see the [main README](README.md) and [DOCS](DOCS.md).
