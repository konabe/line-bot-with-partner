
FROM python:3.11-slim
WORKDIR /app
# uvインストール
RUN pip install uv
COPY requirements.txt ./
# BuildKitのキャッシュ活用（uvはpip互換キャッシュを利用）
RUN --mount=type=cache,target=/root/.cache/pip uv pip install -r requirements.txt --system
COPY . .
ENV PYTHONPATH=/app
ENV PORT=8080
# run with gunicorn WSGI server in production
CMD exec gunicorn --bind 0.0.0.0:${PORT} --workers 2 --threads 4 --timeout 30 "src.app:app"
