#!/bin/sh
# Explicit Phase 2 operator action; no provider request, no evaluation execution.
set -eu
image=$1
case "$image" in *@sha256:*) ;; *) echo 'Digest-pinned image required' >&2; exit 1;; esac
docker network create --internal claude-eval-internal
docker run -d --name claude-eval-proxy --network claude-eval-internal --read-only --cap-drop ALL --security-opt no-new-privileges "$image" python3 /opt/host/api_proxy.py
docker network connect bridge claude-eval-proxy
