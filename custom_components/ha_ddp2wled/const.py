"""Constants for the HA DDP2WLED integration."""

DOMAIN = "ha_ddp2wled"

# Service names
SERVICE_SEND_TO_WLED_DDP = "send_to_wled_ddp"
SERVICE_STOP_DDP_STREAM = "stop_ddp_stream"

# Configuration and options
CONF_WLED_HOST = "wled_host"
CONF_BRIGHTNESS = "brightness"
CONF_WIDTH = "width"
CONF_HEIGHT = "height"
CONF_SEGMENT_ID = "segment_id"
CONF_CLEAR_DISPLAY = "clear_display"

# Default values
DEFAULT_BRIGHTNESS = 255
DEFAULT_WIDTH = 64
DEFAULT_HEIGHT = 64
DEFAULT_SEGMENT_ID = 0
DEFAULT_CLEAR_DISPLAY = True