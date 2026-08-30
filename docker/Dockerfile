# syntax=docker/dockerfile:1.7

FROM docker.io/library/debian:12-slim@sha256:abd67ffcfa541b485a3dff59865ab629aa048a6c613e639d36e7456b0b229241 AS ilastik-assets

ARG TARGETARCH
ARG ILASTIK_VERSION=1.4.2
ARG ILASTIK_COMMIT=cfcb94fcfdb83ddd0f85e322173f6549f760e653
ARG ILASTIK_ARCHIVE_SHA256=164facabba4b1103a98d806c156f70937136bee0363aeeae84df6dade1e6763f
ARG ILASTIK_ARCHIVE_BYTES=681505433
ARG ILASTIK_DOWNLOAD_PARTS=16

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/cache/ilastik-download,sharing=locked \
    set -eux; \
    test "$TARGETARCH" = amd64; \
    rm -f /etc/apt/apt.conf.d/docker-clean; \
    echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache; \
    for attempt in 1 2 3 4 5; do \
      rm -rf /var/lib/apt/lists/*; \
      apt-get -o Acquire::Retries=5 -o Acquire::http::No-Cache=true update \
      && apt-get -o Acquire::Retries=5 -o Acquire::http::No-Cache=true install -y --no-install-recommends \
        bzip2 ca-certificates coreutils curl tar \
      && break; \
      test "$attempt" -lt 5; \
      sleep $((attempt * 5)); \
    done; \
    archive_url="https://files.ilastik.org/ilastik-${ILASTIK_VERSION}-Linux.tar.bz2"; \
    chunk_bytes=$(((ILASTIK_ARCHIVE_BYTES + ILASTIK_DOWNLOAD_PARTS - 1) / ILASTIK_DOWNLOAD_PARTS)); \
    download_part() { \
      index="$1"; \
      start=$((index * chunk_bytes)); \
      end=$((start + chunk_bytes - 1)); \
      test "$end" -lt "$ILASTIK_ARCHIVE_BYTES" || end=$((ILASTIK_ARCHIVE_BYTES - 1)); \
      expected=$((end - start + 1)); \
      part="/var/cache/ilastik-download/ilastik-${ILASTIK_VERSION}.parts-${ILASTIK_DOWNLOAD_PARTS}.${start}-${end}"; \
      actual=0; \
      test ! -f "$part" || actual="$(wc -c < "$part")"; \
      if test "$actual" -gt "$expected"; then rm -f "$part"; actual=0; fi; \
      attempt=0; \
      while test "$actual" -lt "$expected"; do \
        attempt=$((attempt + 1)); \
        test "$attempt" -le 100; \
        resume_start=$((start + actual)); \
        next="${part}.next"; \
        rm -f "$next"; \
        curl_status=0; \
        curl --http1.1 --fail --location --silent --show-error \
          --connect-timeout 30 --max-time 180 --speed-limit 1024 --speed-time 60 \
          --range "${resume_start}-${end}" -o "$next" "$archive_url" \
          || curl_status=$?; \
        received=0; \
        test ! -f "$next" || received="$(wc -c < "$next")"; \
        if test "$received" -gt 0; then cat "$next" >> "$part"; fi; \
        rm -f "$next"; \
        actual="$(wc -c < "$part")"; \
        test "$actual" -le "$expected"; \
        if test "$curl_status" -ne 0; then \
          echo "ilastik archive part ${index}: curl status ${curl_status}; resuming at ${actual}/${expected}" >&2; \
        fi; \
        if test "$received" -eq 0; then sleep 3; fi; \
      done; \
      test "$actual" -eq "$expected"; \
    }; \
    pids=; \
    index=0; \
    while test "$index" -lt "$ILASTIK_DOWNLOAD_PARTS"; do \
      ( download_part "$index" ) & \
      pids="$pids $!"; \
      index=$((index + 1)); \
    done; \
    failed=0; \
    for pid in $pids; do wait "$pid" || failed=1; done; \
    test "$failed" -eq 0; \
    : > /tmp/ilastik.tar.bz2; \
    index=0; \
    while test "$index" -lt "$ILASTIK_DOWNLOAD_PARTS"; do \
      start=$((index * chunk_bytes)); \
      end=$((start + chunk_bytes - 1)); \
      test "$end" -lt "$ILASTIK_ARCHIVE_BYTES" || end=$((ILASTIK_ARCHIVE_BYTES - 1)); \
      cat "/var/cache/ilastik-download/ilastik-${ILASTIK_VERSION}.parts-${ILASTIK_DOWNLOAD_PARTS}.${start}-${end}" >> /tmp/ilastik.tar.bz2; \
      index=$((index + 1)); \
    done; \
    test "$(wc -c < /tmp/ilastik.tar.bz2)" -eq "$ILASTIK_ARCHIVE_BYTES"; \
    echo "$ILASTIK_ARCHIVE_SHA256  /tmp/ilastik.tar.bz2" | sha256sum -c -; \
    mkdir -p /opt/ilastik; \
    tar -xjf /tmp/ilastik.tar.bz2 -C /opt/ilastik --strip-components=1; \
    test -x /opt/ilastik/run_ilastik.sh; \
    test -x /opt/ilastik/bin/python; \
    test -s /opt/ilastik/LICENSE.txt; \
    rm -f /tmp/ilastik.tar.bz2; \
    rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    rm -rf /opt/ilastik/etc/conda/test-files; \
    find /opt/ilastik/lib/python3.11/site-packages -depth -type d \
      \( -name tests -o -name test \) \
      ! -path /opt/ilastik/lib/python3.11/site-packages/astropy/tests \
      -exec rm -rf {} +; \
    find /opt/ilastik -xdev -type f -name '*.pyc' -delete; \
    find /opt/ilastik -xdev -depth -type d -name __pycache__ -empty -delete

RUN set -eux; \
    mkdir -p /opt/ilastik-upstream; \
    for file in LICENSE CITATION.cff Readme.md LICENSE.gpl2 LICENSE.gpl3 LICENSE.lgpl2 LICENSE.lgpl3 LICENSE.Python; do \
      curl --http1.1 -fL --retry 5 --retry-delay 3 --retry-all-errors \
        -o "/opt/ilastik-upstream/${file}" \
        "https://raw.githubusercontent.com/ilastik/ilastik/${ILASTIK_COMMIT}/${file}"; \
    done; \
    printf '%s  %s\n' \
      13fa8c36b70a4250c8700652d123583c56eff3f08c2c7723d9ddafe787205395 /opt/ilastik-upstream/LICENSE \
      4c791b1e3fb1b172857d2ff794ffdc107baf6575ac173da674bf8e18064db059 /opt/ilastik-upstream/CITATION.cff \
      a9f0ebfbaf65a1d489aa2dfa52252e3a1b1cf2741c3c6dfa5ac8b0dcab4bf2aa /opt/ilastik-upstream/Readme.md \
      8177f97513213526df2cf6184d8ff986c675afb514d4e68a404010521b880643 /opt/ilastik-upstream/LICENSE.gpl2 \
      8ceb4b9ee5adedde47b31e975c1d90c73ad27b6b165a1dcd80c7c545eb65b903 /opt/ilastik-upstream/LICENSE.gpl3 \
      dc626520dcd53a22f727af3ee42c770e56c97a64fe3adb063799d8ab032fe551 /opt/ilastik-upstream/LICENSE.lgpl2 \
      da7eabb7bafdf7d3ae5e9f223aa5bdc1eece45ac569dc21b3b037520b4464768 /opt/ilastik-upstream/LICENSE.lgpl3 \
      78b12c3a81360b357002334f0e70ea0e92eebf7a9b358805c03c48484945f3bb /opt/ilastik-upstream/LICENSE.Python \
      | sha256sum -c -

FROM docker.io/library/debian:12-slim@sha256:abd67ffcfa541b485a3dff59865ab629aa048a6c613e639d36e7456b0b229241 AS novnc-assets

ARG NOVNC_VERSION=1.7.0
ARG NOVNC_SOURCE_SHA256=b1003a11b6e6e8d8f7f5e5586daae7f8ca651d8aee0aa155ff9ac841c48f52c6
ARG WEBSOCKIFY_VERSION=0.13.0
ARG WEBSOCKIFY_SOURCE_SHA256=b6413e364efd04f3c92ec8c17747e3c4adc20157c2ef1c5d019a26d944a46df8

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked set -eux; \
    rm -f /etc/apt/apt.conf.d/docker-clean; \
    echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache; \
    for attempt in 1 2 3 4 5; do \
      rm -rf /var/lib/apt/lists/*; \
      apt-get -o Acquire::Retries=5 -o Acquire::http::No-Cache=true update \
      && apt-get -o Acquire::Retries=5 -o Acquire::http::No-Cache=true install -y --no-install-recommends \
        ca-certificates curl tar \
      && break; \
      test "$attempt" -lt 5; \
      sleep $((attempt * 5)); \
    done; \
    curl --http1.1 -fL --retry 5 --retry-delay 5 --retry-all-errors \
      -o /tmp/novnc.tar.gz "https://github.com/novnc/noVNC/archive/refs/tags/v${NOVNC_VERSION}.tar.gz"; \
    echo "$NOVNC_SOURCE_SHA256  /tmp/novnc.tar.gz" | sha256sum -c -; \
    curl --http1.1 -fL --retry 5 --retry-delay 5 --retry-all-errors \
      -o /tmp/websockify.tar.gz "https://github.com/novnc/websockify/archive/refs/tags/v${WEBSOCKIFY_VERSION}.tar.gz"; \
    echo "$WEBSOCKIFY_SOURCE_SHA256  /tmp/websockify.tar.gz" | sha256sum -c -; \
    mkdir -p /opt; \
    tar -xzf /tmp/novnc.tar.gz -C /opt; \
    mv "/opt/noVNC-${NOVNC_VERSION}" /opt/noVNC; \
    tar -xzf /tmp/websockify.tar.gz -C /opt; \
    mv "/opt/websockify-${WEBSOCKIFY_VERSION}" /opt/websockify; \
    rm -f /tmp/novnc.tar.gz /tmp/websockify.tar.gz; \
    rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    rm -rf /opt/noVNC/tests

FROM docker.io/library/debian:12-slim@sha256:abd67ffcfa541b485a3dff59865ab629aa048a6c613e639d36e7456b0b229241

ARG TARGETARCH
ARG ILASTIK_VERSION=1.4.2
ARG ILASTIK_COMMIT=cfcb94fcfdb83ddd0f85e322173f6549f760e653
ARG ILASTIK_ARCHIVE_SHA256=164facabba4b1103a98d806c156f70937136bee0363aeeae84df6dade1e6763f
ARG ILASTIK_ARCHIVE_BYTES=681505433
ARG NOVNC_VERSION=1.7.0
ARG NOVNC_SOURCE_SHA256=b1003a11b6e6e8d8f7f5e5586daae7f8ca651d8aee0aa155ff9ac841c48f52c6
ARG WEBSOCKIFY_VERSION=0.13.0
ARG WEBSOCKIFY_SOURCE_SHA256=b6413e364efd04f3c92ec8c17747e3c4adc20157c2ef1c5d019a26d944a46df8

ENV DEBIAN_FRONTEND=noninteractive

COPY --from=ilastik-assets /opt/ilastik/ /opt/ilastik/
COPY --from=ilastik-assets /opt/ilastik-upstream/ /usr/share/doc/ilastik-upstream/
COPY --from=novnc-assets /opt/noVNC/ /opt/noVNC/
COPY --from=novnc-assets /opt/websockify/ /opt/websockify/

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked set -eux; \
    test "$TARGETARCH" = amd64; \
    rm -f /etc/apt/apt.conf.d/docker-clean; \
    echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache; \
    for attempt in 1 2 3 4 5; do \
      rm -rf /var/lib/apt/lists/*; \
      apt-get -o Acquire::Retries=5 -o Acquire::http::No-Cache=true update \
      && apt-get -o Acquire::Retries=5 -o Acquire::http::No-Cache=true install -y --no-install-recommends \
        ca-certificates coreutils curl dbus-x11 findutils fontconfig fonts-dejavu-core \
        grep libasound2 libdbus-1-3 libegl1 libfontconfig1 libfreetype6 libgl1 \
        libglib2.0-0 libice6 libnspr4 libnss3 libsm6 libtbb12 libx11-6 libx11-xcb1 \
        libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 \
        libxcb-render-util0 libxcb-render0 libxcb-shape0 libxcb-shm0 libxcb-sync1 \
        libxcb-util1 libxcb-xfixes0 libxcb-xinerama0 libxcb-xinput0 libxcb-xkb1 \
        libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 \
        libxi6 libxkbcommon-x11-0 libxrandr2 libxrender1 libxtst6 procps python3 \
        sed twm x11vnc xauth xdg-utils xdotool xvfb \
      && break; \
      test "$attempt" -lt 5; \
      sleep $((attempt * 5)); \
    done; \
    chmod 0755 /opt/websockify/run /opt/noVNC/utils/novnc_proxy; \
    mkdir -p /usr/share/ilastik-taffish; \
    printf '%s\n' \
      'upstream_repo=https://github.com/ilastik/ilastik' \
      "upstream_tag=${ILASTIK_VERSION}" \
      "upstream_commit=${ILASTIK_COMMIT}" \
      'archive_url=https://files.ilastik.org/ilastik-1.4.2-Linux.tar.bz2' \
      "archive_sha256=${ILASTIK_ARCHIVE_SHA256}" \
      "archive_bytes=${ILASTIK_ARCHIVE_BYTES}" \
      "novnc_version=${NOVNC_VERSION}" \
      "novnc_source_sha256=${NOVNC_SOURCE_SHA256}" \
      "websockify_version=${WEBSOCKIFY_VERSION}" \
      "websockify_source_sha256=${WEBSOCKIFY_SOURCE_SHA256}" \
      "architecture=${TARGETARCH}" \
      > /usr/share/ilastik-taffish/source.txt; \
    dpkg-query -W -f='${Package}\t${Version}\t${Installed-Size}\n' \
      > /usr/share/ilastik-taffish/debian-packages.tsv; \
    rm -rf /var/lib/apt/lists/*

COPY docker/ilastik-launch /usr/local/bin/ilastik
COPY docker/ilastik-gui /usr/local/bin/ilastik-gui
COPY docker/ilastik-models /usr/local/bin/ilastik-models
COPY docker/ilastik-smoke /usr/local/bin/ilastik-smoke
COPY docker/websockify-launch /usr/local/bin/websockify

ENV PATH=/usr/local/sbin:/usr/local/bin:/opt/ilastik/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENV HOME=/root
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV BIOIMAGEIO_CACHE_PATH=/tmp/ilastik-bioimageio-cache
ENV MPLCONFIGDIR=/tmp/ilastik-matplotlib-cache
ENV NUMBA_CACHE_DIR=/tmp/ilastik-numba-cache
ENV XDG_CACHE_HOME=/tmp/ilastik-xdg-cache
ENV XDG_CONFIG_HOME=/tmp/ilastik-xdg-config
ENV XDG_DATA_HOME=/tmp/ilastik-xdg-data
ENV LIBGL_ALWAYS_SOFTWARE=1
ENV QT_OPENGL=software
ENV QT_X11_NO_MITSHM=1

RUN set -eux; \
    chmod 0755 /usr/local/bin/ilastik /usr/local/bin/ilastik-gui /usr/local/bin/ilastik-models /usr/local/bin/ilastik-smoke /usr/local/bin/websockify; \
    PYTHONDONTWRITEBYTECODE=1 ilastik-smoke buildtime

EXPOSE 5801

WORKDIR /root

ENTRYPOINT []
CMD []

ENV TAFFISH_ENV=TAFFISH
ENV TAFFISH_NAME=ilastik
