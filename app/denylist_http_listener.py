from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel
from update_denylist import update_denylist
import os
import logging
import hvac

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# --- FastAPI App ---
app = FastAPI()

# --- Request Model ---
class URLRequest(BaseModel):
    url: str

# --- Global Vars (loaded from Vault at startup) ---
WEBHOOK_SECRET = ""
TRUSTED_IPS = []

# --- Vault Loader ---
def load_secrets_from_vault():
    vault_addr = os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
    vault_token = os.getenv("VAULT_TOKEN")

    if not vault_token:
        raise Exception("VAULT_TOKEN is missing")

    client = hvac.Client(url=vault_addr, token=vault_token)

    if not client.is_authenticated():
        raise Exception("Vault auth failed")

    secret_data = client.secrets.kv.v2.read_secret_version(path="webhook")
    data = secret_data["data"]["data"]

    return {
        "WEBHOOK_SECRET": data["WEBHOOK_SECRET"],
        "TRUSTED_IPS": data.get("TRUSTED_IPS", "")
    }

# --- Load Secrets at Startup ---
@app.on_event("startup")
def startup_event():
    global WEBHOOK_SECRET, TRUSTED_IPS
    secrets = load_secrets_from_vault()
    WEBHOOK_SECRET = secrets["WEBHOOK_SECRET"]
    TRUSTED_IPS = [ip.strip() for ip in secrets["TRUSTED_IPS"].split(",")] if secrets["TRUSTED_IPS"] else []
    logging.info("Secrets loaded from Vault")

# --- POST Endpoint ---
@app.post("/zscaler/denylist")
async def webhook(req: URLRequest, x_api_key: str = Header(...), request: Request = None):
    client_ip = request.client.host

    # IP Whitelist Check
    if TRUSTED_IPS and client_ip not in TRUSTED_IPS:
        logging.warning(f"Blocked request from unauthorized IP: {client_ip}")
        raise HTTPException(status_code=403, detail="Unauthorized IP")

    # API Key Check
    if x_api_key != WEBHOOK_SECRET:
        logging.warning(f"Unauthorized access attempt from {client_ip}")
        raise HTTPException(status_code=403, detail="Forbidden")

    # Denylist update attempt
    try:
        logging.info(f"Received request from {client_ip} to block URL: {req.url}")
        update_denylist(req.url)
        return {"status": "ok", "message": f"{req.url} added to Zscaler denylist"}
    except Exception as e:
        logging.error(f"Error while processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

