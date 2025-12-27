ARG BUILD_FROM
FROM $BUILD_FROM

# Set shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install nginx and other required packages
RUN apk add --no-cache \
    nginx \
    bash

# Copy add-on files
COPY run.sh /
COPY pxmagic.htm /usr/share/nginx/html/
COPY inpxmagic.htm /usr/share/nginx/html/
COPY images /usr/share/nginx/html/images/

# Create nginx configuration
RUN echo 'server { \
    listen 8099; \
    root /usr/share/nginx/html; \
    index pxmagic.htm; \
    location / { \
        try_files $uri $uri/ /pxmagic.htm; \
    } \
}' > /etc/nginx/http.d/default.conf

# Make run script executable
RUN chmod a+x /run.sh

# Set working directory
WORKDIR /usr/share/nginx/html

# Labels
LABEL \
    io.hass.name="Pixel Magic Tool" \
    io.hass.description="A tool that converts any image into code in JSON WLED format for 2D Matrix panels" \
    io.hass.version="1.0.0" \
    io.hass.type="addon" \
    io.hass.arch="armhf|armv7|aarch64|amd64|i386"

# Start script
CMD [ "/run.sh" ]
