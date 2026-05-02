# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# Dockerfile
#
# Fleet Dashboard - Multi-stage build
#
# Richard J. Sears
# richardjsears@protonmail.com
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

# Stage 1: Build frontend
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Production image
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend
COPY backend/ ./backend/

# Copy frontend build (includes public/ assets)
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Default port (can be overridden by PORT env var)
ENV PORT=80
EXPOSE 80

# Run the application using shell form to expand $PORT
CMD uvicorn backend.main:app --host 0.0.0.0 --port $PORT
