
FROM python:3.11-slim
WORKDIR /app
# uvインストール
RUN pip install uv
COPY requirements.txt ./
# BuildKitのキャッシュ活用（uvはpip互換キャッシュを利用）
RUN --mount=type=cache,target=/root/.cache/pip uv pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
