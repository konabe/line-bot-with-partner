
FROM python:3.12-slim
WORKDIR /app
# uvインストール
RUN pip install uv
COPY requirements.txt ./
# BuildKitのキャッシュ活用（uvはpip互換キャッシュを利用）
RUN --mount=type=cache,target=/root/.cache/pip uv pip install -r requirements.txt --system
COPY . .
ENV PYTHONPATH=/app/src
ENV PORT=8080
COPY start.sh /start.sh
RUN chmod +x /start.sh
# run start script which execs gunicorn
CMD ["/start.sh"]
