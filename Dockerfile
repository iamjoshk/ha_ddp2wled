ARG BUILD_FROM
FROM $BUILD_FROM

# Set shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install nginx, curl, and other required packages
RUN apk add --no-cache \
    nginx \
    bash \
    curl

# Copy run script
COPY run.sh /

# Download latest files from Apollo Automation's PixelMagicTool repository
RUN mkdir -p /usr/share/nginx/html && \
    curl -fsSL -o /usr/share/nginx/html/pxmagic.htm https://raw.githubusercontent.com/ApolloAutomation/PixelMagicTool/main/pxmagic.htm && \
    curl -fsSL -o /usr/share/nginx/html/inpxmagic.htm https://raw.githubusercontent.com/ApolloAutomation/PixelMagicTool/main/inpxmagic.htm

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
