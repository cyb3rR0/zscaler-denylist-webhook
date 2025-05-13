MIT License – use freely for internal or demonstration purposes.

# Zscaler Denylist Automation with a Webhook

This project is a secure, containerized Python webhook for automating updates to a Zscaler Internet Access (ZIA) denylist.

It receives pre-approved domain block requests (e.g., from ServiceNow) and performs the following:
- Validates the domain input
- Authenticates with Zscaler OneAPI using OAuth 2.0
- Adds the domain to the denylist (if not already present)
- Activates the change
- Logs all actions
- Protects against rate limits and race conditions

> **Built for reliability, security, and clean integration into CI/CD pipelines.**

---

## 🧱 Project Structure

.
├── app/
│ ├── init.py
│ ├── webhook_server.py # FastAPI webhook endpoint
│ └── update_denylist.py # Core logic (validation, ZIA API calls, activation)
├── requirements.txt
├── Dockerfile
├── Makefile
├── .dockerignore
├── .gitignore
└── README.md

# ----------------------------------------------------------------------------
---

## 🚀 Quick Start

### 🐳 Build and Run in Docker

```bash
# Build the image
docker build -t zscaler-denylist-webhook .

# Run the container
docker run -p 8080:8080 \
  -e VAULT_ADDR=http://your-vault-server:8200 \
  -e VAULT_TOKEN=your-vault-token \
  zscaler-denylist-webhook


make install      # Install Python dependencies
make run          # Run the FastAPI app (no --reload)
make run-dev      # Run with reload for development
make lint         # Run code formatters and linters
make test         # Placeholder for test suite
make clean        # Clean up environment
```


## Vault must contain a secret at secret/data/zscaler like:

```bash
{
  "VANITY_DOMAIN": "yourcompany",
  "CLIENT_ID": "your-client-id",
  "CLIENT_SECRET": "your-client-secret"
}
```

✅ Highlights

    - Secure Vault-based secret management

    - Rate-limit + race-condition safe

    - FastAPI-powered webhook

    - Hardened Dockerfile (non-root user, no dev tools)

    - Container-ready for CI/CD or cloud deployment

    - Makefile for local and containerized usage

 # Author

### Romel Altidor
Information Security | Cloud Security | DevSecOps |