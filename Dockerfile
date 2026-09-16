FROM python:3.12-slim AS builder
WORKDIR /app
COPY lidas/ ./lidas/
COPY pyproject.toml* setup.cfg* ./

RUN mkdir -p /app/data

FROM gcr.io/distroless/python3-debian12
WORKDIR /app

COPY --from=builder /app/lidas ./lidas

COPY --from=builder --chown=65532:65532 /app/data /app/data

USER nonroot
ENTRYPOINT ["/usr/bin/python3", "-m", "lidas.cli"]