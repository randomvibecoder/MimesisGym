FROM python:3.12-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    MPLCONFIGDIR=/tmp/matplotlib \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash coreutils ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir \
       aggdraw \
       matplotlib \
       numpy \
       opencv-python-headless \
       pillow \
       scikit-image

COPY docker/image/guest_tools.py /opt/mimesis/guest_tools.py

RUN useradd --create-home --uid 10001 agent \
    && mkdir -p /workspace /tmp/matplotlib \
    && chown -R agent:agent /workspace /tmp/matplotlib \
    && chmod 0555 /opt/mimesis/guest_tools.py

USER agent
WORKDIR /workspace
CMD ["sleep", "infinity"]
