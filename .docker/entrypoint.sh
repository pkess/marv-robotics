#!/usr/bin/env bash
#
# Copyright 2016 - 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

source /etc/profile.d/marv_env.sh

set -e

if [[ -n "$DEBUG" ]]; then
    set -x
fi

echo "$TIMEZONE" > /etc/timezone
ln -sf /usr/share/zoneinfo/"$TIMEZONE" /etc/localtime
dpkg-reconfigure -f noninteractive tzdata

groupadd -g $MARV_GID marv || true
useradd -M -u $MARV_UID -g $MARV_GID --shell /bin/bash marv
chown $MARV_UID:$MARV_GID /home/marv
if [[ $MARV_UID -ne 1000 ]] || [[ $MARV_GID -ne 1000 ]]; then
    chown -R $MARV_UID:$MARV_GID $MARV_VENV
fi

for x in /etc/skel/.*; do
    target="/home/marv/$(basename "$x")"
    if [[ ! -e "$target" ]]; then
        cp -a "$x" "$target"
        chown -R $MARV_UID:$MARV_GID "$target"
    fi
done

if [[ -n "$DEVELOP" ]]; then
    find "$DEVELOP" -maxdepth 2 -name setup.py \
        -execdir su -c "$MARV_VENV/bin/pip install -e ." marv \;
fi

export HOME=/home/marv
cd $MARV_SITE

if [[ -d code ]]; then
    find code -maxdepth 2 -name setup.py -execdir su -c "$MARV_VENV/bin/pip install -e ." marv \;
fi

if [[ -n "$MARV_INIT" ]] || [[ ! -e db ]]; then
    su marv -p -c '/opt/marv/bin/marv --config "$MARV_CONFIG" init'
fi
su marv -p -c '/opt/marv/bin/marv --config "${MARV_CONFIG}" serve --host 0.0.0.0 --approot "${MARV_APPLICATION_ROOT:-/}" ${MARV_ARGS}' &

echo 'Container startup complete.'
exec "$@"
