# Day 2 — multi-stage build (Fri 20 Nov 2026)
#
# Two stages, same base image. The builder stage holds the source;
# the runtime stage copies only what the app needs to run.
# Honest note: this app uses only the Python standard library, so there
# are no dependencies to leave behind — the size saving vs Day 1 will be
# small. The point today is the pattern (and measuring it), not a big
# saving. The saving becomes real once an app has build-time deps.
FROM python:3.12-slim AS builder
WORKDIR /app
COPY app.py .

FROM python:3.12-slim AS runtime
WORKDIR /app
COPY --from=builder /app/app.py .
EXPOSE 8000
ENV PORT=8000 DB_HOST=db DB_PORT=5432
CMD ["python3", "app.py"]
