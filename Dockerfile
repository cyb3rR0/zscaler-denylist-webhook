# ---- Base Image ----
    FROM python:3.11-slim

    # ---- Metadata (Optional) ----
    LABEL maintainer="yourname@example.com"
    LABEL description="Zscaler Denylist Webhook with Vault integration"
    
    # ---- Set Working Directory ----
    WORKDIR /app
    
    # ---- System Dependencies (Optional: make, build tools) ----
    RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        make \
        && rm -rf /var/lib/apt/lists/*
    
    # ---- Copy Code and Config ----
    COPY . .
    
    # ---- Install Python Dependencies ----
    RUN pip install --upgrade pip && pip install -r requirements.txt
    
    # ---- Expose Port ----
    EXPOSE 8080
    
    # ---- Default Command ----
    CMD ["make", "run"]
    