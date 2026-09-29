FROM otel/opentelemetry-collector-contrib:0.123.0@sha256:e39311df1f3d941923c00da79ac7ba6269124a870ee87e3c3ad24d60f8aee4d2 AS collector
FROM rust:1.85.1-slim-bookworm@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36 AS rust
FROM node:22-bookworm-slim@sha256:43ac6c60b8f89723f746e8a92ce91abd5017e627ce1ddfe4238355d3a30b772c
RUN apt-get update && apt-get install -y --no-install-recommends python3 gcc libc6-dev ca-certificates git curl && rm -rf /var/lib/apt/lists/*
RUN npm install -g @anthropic-ai/claude-code@2.1.284 && claude --version
COPY --from=rust /usr/local/rustup /usr/local/rustup
COPY --from=rust /usr/local/cargo/bin /usr/local/bin
ENV RUSTUP_HOME=/usr/local/rustup
COPY --from=collector /otelcol-contrib /usr/local/bin/otelcol-contrib
COPY evals/harness/host/ /opt/host/
ENV CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
USER 1000:1000
ENTRYPOINT []
CMD ["python3", "/opt/host/claude_code_adapter.py"]
