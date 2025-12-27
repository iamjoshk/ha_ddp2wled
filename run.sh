#!/usr/bin/with-contenv bashio

# Get log level from options
LOG_LEVEL=$(bashio::config 'log_level')

bashio::log.info "Starting Pixel Magic Tool..."
bashio::log.info "Log level: ${LOG_LEVEL}"

# Start nginx
bashio::log.info "Starting nginx web server on port 8099..."
exec nginx -g "daemon off;"
