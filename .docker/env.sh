#!/usr/bin/env bash
#
# Copyright 2016 - 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

if [ -z "$CENV" ]; then
    set -e
    export CENV=1
    if [[ -n "$ACTIVATE_VENV" ]] && [[ -n "$MARV_VENV" ]]; then
        source $MARV_VENV/bin/activate
    fi
    if [[ -d "/home/marv/site" ]]; then
        export MARV_SITE="/home/marv/site"
        export MARV_CONFIG="$MARV_SITE/marv.conf"
    fi
    cd
    set +e
fi
