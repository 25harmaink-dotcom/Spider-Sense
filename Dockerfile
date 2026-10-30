FROM node:22-alpine AS frontend
WORKDIR /site
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
COPY --from=frontend /site/dist ./frontend/dist
EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn app.hosted:app --host 0.0.0.0 --port ${PORT:-8000}"]
