# One isolated, ephemeral, fictional-data demo. Build from repository root.
FROM node:24-bookworm-slim AS web-build
WORKDIR /build
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm install -g pnpm@11.25.0
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web ./apps/web
RUN pnpm install --frozen-lockfile && pnpm build

FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1     NEXT_TELEMETRY_DISABLED=1 NODE_ENV=production     OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1     PORT=10000 SYNTHETIC_IMPORTS_ENABLED=false
RUN apt-get update && apt-get install -y --no-install-recommends     nginx libstdc++6 libatomic1     && rm -rf /var/lib/apt/lists/*     && useradd --create-home --uid 1000 demo
COPY --from=web-build /usr/local/bin/node /usr/local/bin/node
WORKDIR /app/api
COPY apps/api ./
RUN pip install --no-cache-dir .
COPY --from=web-build /build/apps/web/.next/standalone /app/web/
COPY --from=web-build /build/apps/web/.next/static /app/web/apps/web/.next/static
COPY deploy/demo/start.sh deploy/demo/nginx.conf /app/demo/
USER demo
EXPOSE 10000
HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=3     CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.environ['PORT']+'/healthz',timeout=3)"
CMD ["bash", "/app/demo/start.sh"]
