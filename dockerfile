FROM python:3.10-slim

WORKDIR /app

# 依存関係ファイルをコピー
COPY requirements_modified.txt /app/requirements.txt

# 依存関係のインストール
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . /app/

# アプリケーションポートを公開
EXPOSE 5000

# アプリケーションの実行
CMD ["python", "app.py"]