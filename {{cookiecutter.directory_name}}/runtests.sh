#!/usr/bin/env sh

pytest \
    --tb=native \
    --durations=20 \
    --nomigrations \
    --reuse-db \
    --log-level=ERROR "$@"
