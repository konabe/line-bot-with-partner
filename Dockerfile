
FROM python:3.11-slim
WORKDIR /app
# pipキャッシュ活用（BuildKit有効時のみ）
COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "app.py"]
