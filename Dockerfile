FROM ubuntu:18.04

ENV BROWSER=/browser \
    LC_ALL=en_US.UTF-8 \
    SPARK_VERSION=2.3.2 \
    JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64

COPY requirements.txt dashboard_server/requirements.txt


RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-suggests --no-install-recommends \
      ca-certificates locales gcc g++ wget python-psycopg2 \
      python3 python3-dev python3-distutils git && \
    echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && \
    locale-gen && \
    wget -O - https://bootstrap.pypa.io/get-pip.py | python3 && \
    cd dashboard_server && \
    pip3 install --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt && \
    apt-get remove -y python3-dev gcc g++ wget git && \
    apt-get remove -y .*-doc .*-man >/dev/null && \
    apt-get clean && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/* && \
    echo '#!/bin/bash\n\
\n\
echo\n\
echo "  $@"\n\
echo\n\' > /browser && \
    chmod +x /browser

COPY . dashboard_server/
RUN cd dashboard_server && pip3 install .
