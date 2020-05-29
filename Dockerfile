# --- Reference: https://iotbytes.wordpress.com/create-your-first-docker-container-for-raspberry-pi-to-blink-an-led/

# - Python Base Image from https://hub.docker.com/r/arm32v7/python/
FROM arm32v7/python:3.8-buster


# - Install necessary dependencies (required for temperature measurement (vcgencmd))
# https://stackoverflow.com/a/49462622
ARG APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=1

# $$$ TMP FIX wget --inet4-only due to Docker ipv4 problems $$$
RUN apt-get update \
 && apt-get install wget \
 && wget --inet4-only -O - https://archive.raspbian.org/raspbian.public.key | apt-key add - \
 && wget --inet4-only -O - http://archive.raspberrypi.org/debian/raspberrypi.gpg.key | apt-key add - \
 && echo 'deb http://raspbian.raspberrypi.org/raspbian/ buster main contrib non-free rpi' | tee -a /etc/apt/sources.list \
 && echo 'deb http://archive.raspberrypi.org/debian/ buster main ui' | tee -a /etc/apt/sources.list.d/raspi.list \
 && apt-get update  \
 && apt-get install -y --no-install-recommends \
                libraspberrypi-bin \
 && apt-get autoremove \
 && rm -rf /tmp/* \
 && rm -rf /var/lib/apt/lists/*


# - Intall the rpi.gpio python module
RUN pip install --no-cache-dir rpi.gpio


# - Create user (for security)
# RUN useradd --create-home pwmuser
# USER pwmuser


# - Copy Python script
WORKDIR /usr/local/bin
COPY src/fan_control.py .


# - Run python script ('-u' -> unbuffered output => output both stderr & stdout during runtime)
CMD ["python", "-u", "fan_control.py"]
