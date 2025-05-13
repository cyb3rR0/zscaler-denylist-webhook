# ---- Base Image ----
FROM python:3.11-slim

# ---- Metadata ----
LABEL maintainer="romelaltidor@protonmail.com"
LABEL description="Zscaler Denylist Webhook with Vault integration"

# ---- Set Working Directory ----
WORKDIR /app

# ---- Install System Dependencies, Then Clean ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    make \
    && pip install --upgrade pip \
    && apt-get purge -y --auto-remove build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /root/.cache

# ---- Copy Files ----
COPY . .

# ---- Install Python Dependencies ----
RUN pip install --no-cache-dir -r requirements.txt

# ---- Create Non-root User ----
RUN addgroup --system app && adduser --system --ingroup app appuser
USER appuser

# ---- Expose App Port ----
EXPOSE 8080

# ---- Default Entrypoint ----
CMD ["make", "run"]

    
