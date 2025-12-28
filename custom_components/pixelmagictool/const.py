"""Constants for the Pixel Magic Tool integration."""

DOMAIN = "pixelmagictool"

# Service names
SERVICE_CONVERT_IMAGE = "convert_image"
SERVICE_SEND_TO_WLED = "send_to_wled"
SERVICE_SEND_TO_WLED_DDP = "send_to_wled_ddp"

# Configuration and options
CONF_WLED_HOST = "wled_host"
CONF_SEGMENT_ID = "segment_id"
CONF_BRIGHTNESS = "brightness"
CONF_WIDTH = "width"
CONF_HEIGHT = "height"
CONF_PATTERN = "pattern"
CONF_TRANSPARENT_COLOR = "transparent_color"
CONF_API_URL = "api_url"
CONF_COMPRESSION = "compression"
CONF_COMPRESSION_LEVEL = "compression_level"
CONF_USE_CHUNKS = "use_chunks"
CONF_CHUNK_SIZE = "chunk_size"
CONF_CHUNK_DELAY = "chunk_delay"
CONF_COLORS_ONLY = "colors_only"
CONF_PROTOCOL = "protocol"

# Default values
DEFAULT_SEGMENT_ID = 0
DEFAULT_BRIGHTNESS = 128
DEFAULT_WIDTH = 16
DEFAULT_HEIGHT = 16
DEFAULT_PATTERN = "range"
DEFAULT_API_URL = "https://pixelmagictool.vercel.app/api/wled/image"
DEFAULT_COMPRESSION = False
DEFAULT_COMPRESSION_LEVEL = 5
DEFAULT_USE_CHUNKS = False
DEFAULT_CHUNK_SIZE = 128  # Conservative size for WLED-MM compatibility (was 256)
DEFAULT_CHUNK_DELAY = 0.15  # Delay in seconds between chunks (150ms for better stability)
DEFAULT_COLORS_ONLY = False
DEFAULT_PROTOCOL = "json"

# Protocol types
PROTOCOL_JSON = "json"
PROTOCOL_DDP = "ddp"
PROTOCOLS = [PROTOCOL_JSON, PROTOCOL_DDP]

# Pattern types
PATTERN_INDIVIDUAL = "individual"
PATTERN_INDEX = "index"
PATTERN_RANGE = "range"

PATTERNS = [PATTERN_INDIVIDUAL, PATTERN_INDEX, PATTERN_RANGE]

# Sensor attributes
ATTR_LAST_IMAGE_URL = "last_image_url"
ATTR_LAST_CONVERSION = "last_conversion"
ATTR_WLED_JSON = "wled_json"
ATTR_SEGMENT_ID = "segment_id"
ATTR_BRIGHTNESS = "brightness"
ATTR_DIMENSIONS = "dimensions"

