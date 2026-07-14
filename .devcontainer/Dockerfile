# AKWF-FREE dev container — audio build toolchain
FROM mcr.microsoft.com/devcontainers/base:bookworm

ARG DEBIAN_FRONTEND=noninteractive

# System tools for waveform conversion, plotting, and validation
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3-pip \
        python3-venv \
        sox \
        libsox-fmt-all \
        ffmpeg \
        libsndfile1 \
        gnuplot \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Python build dependencies (wheels preferred; libsndfile runtime is above)
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --break-system-packages --no-cache-dir -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

USER vscode
