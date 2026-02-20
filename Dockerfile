FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash claude

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY autonomy-loop.py tools.py ./

RUN mkdir -p workspace memory logs && chown -R claude:claude /app

USER claude

CMD ["python3", "autonomy-loop.py"]
