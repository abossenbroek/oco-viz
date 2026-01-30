FROM nvidia/opengl:1.2-glvnd-devel-ubuntu22.04 AS base

ENV DEBIAN_FRONTEND=noninteractive
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility,graphics

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    git \
    ffmpeg \
    libegl1-mesa-dev \
    libgl1-mesa-dev \
    && rm -rf /var/lib/apt/lists/*

# Install pixi
RUN curl -fsSL https://pixi.sh/install.sh | bash
ENV PATH="/root/.pixi/bin:${PATH}"

WORKDIR /app

# Copy project config first for layer caching
COPY pixi.toml pyproject.toml ./
COPY src/oco_viz/__init__.py src/oco_viz/__init__.py
COPY src/oco_viz/py.typed src/oco_viz/py.typed
RUN mkdir -p tests && touch tests/__init__.py

RUN pixi install

# Copy remaining source
COPY . .

# Re-install to pick up editable package
RUN pixi install

ENTRYPOINT ["pixi", "run"]
CMD ["python", "-c", "import oco_viz; print('oco_viz ready')"]
