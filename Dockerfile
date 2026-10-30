FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc make \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN make -C embedded && python -m dewateriq_backend.cli demo --samples 90
EXPOSE 8501
ENV DEWATERIQ_DB=/app/data/dewateriq.sqlite3
CMD ["streamlit","run","app.py","--server.address=0.0.0.0","--server.port=8501"]
