FROM debian:12.7

# Declare ARG to make it available in the RUN commands
ARG TARGETPLATFORM
RUN echo "Building for ${TARGETPLATFORM}"
RUN if [ "${TARGETPLATFORM}" != "linux/amd64" ] && [ "${TARGETPLATFORM}" != "linux/arm64" ]; then \
        echo "Unsupported architecture: ${TARGETPLATFORM}" && \
        exit 1; \
    fi

# Set the general environment variables, and move to temp dir
ENV DEBIAN_FRONTEND="noninteractive"
RUN mkdir -p /app/temp
WORKDIR /app/temp

# Install debian packages
RUN apt update && \
    apt install -y \
        wget zip unzip p7zip-full tzdata git ffmpeg npm python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Install Node.js
RUN npm install --global n@latest && \
    n v22

# Go to the app dir, delete the temporary dir and create backups dir
WORKDIR /app
RUN rm -rf /app/temp

##############
# START HERE #
##############

COPY package.json .
COPY package-lock.json .
RUN npm install

COPY . .
RUN npm run build

CMD ["node", "build/index.js"]
