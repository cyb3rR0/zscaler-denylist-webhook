import os
import time
import re
import requests
import hvac
from urllib.parse import urlparse
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception



# --- Vault Integration ---
def get_secrets_from_vault():
    vault_addr = os.getenv("VAULT_ADDR", "http://put_vault_ip_here")
    vault_token = os.getenv("VAULT_TOKEN")

    # Exception to avoid sending unauthenicated request to vault
    if not vault_token:
        raise Exception("Missing VAULT_TOKEN environment variable")

    client = hvac.Client(url=vault_addr, token=vault_token)

    # Prevents pulling secrets without access
    if not client.is_authenticated():
        raise Exception("Vault authentication failed")


    # Just an example, adjust this to the actual path of the secret
    secret_path = "secret/data/zscaler"
    secret_data = client.secrets.kv.v2.read_secret_version(path="zscaler")

    data = secret_data["data"]["data"]

    return {
        "VANITY": data["VANITY_DOMAIN"],
        "CLIENT_ID": data["CLIENT_ID"],
        "CLIENT_SECRET": data["CLIENT_SECRET"],
        "AUDIENCE": "https://api.zscaler.com",
        "BASE_URL": "https://api.zsapi.net/zia/api/v1"
    }



# Custom exception handles
class RateLimitError(Exception): pass
class EditLockError(Exception): pass
class ReadOnlyError(Exception): pass



# --- URL Input Validation ---
def validate_url_input(raw_input):
    url = raw_input.strip().lower() #convert to lowercase and remove white spaces
    if url.startswith("http://") or url.startswith("https://"):
        url = urlparse(url).hostname or "" # pulls out the domain or leaves an empty string
    pattern = re.compile(r"^(?!\-)(?:[a-zA-Z0-9\-]{1,63}\.)+[a-zA-Z]{2,}$") # regex pattern check 
    if not pattern.match(url):
        raise ValueError(f"Invalid domain: '{raw_input}'")
    if len(url) > 255: # Zscaler max length for domain names
        raise ValueError("URL too long")
    return url



# --- API AUTH ---
def get_access_token():
    url = f"https://{VANITY}.zslogin.net/oauth2/v1/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "audience": AUDIENCE
    }

    # Grabbing the ZIA access token to make the api request
    r = requests.post(url, headers=headers, data=data)
    if r.status_code == 200:
        return r.json()["access_token"]
    else:
        raise Exception(f"Token request failed: {r.status_code} {r.text}")



# --- RETRY HANDLER ---
def should_retry(exception):
    return isinstance(exception, (RateLimitError, EditLockError, ReadOnlyError, requests.exceptions.HTTPError))

@retry(wait=wait_exponential(min=2, max=30), stop=stop_after_attempt(5), retry=retry_if_exception(should_retry), reraise=True)
def api_request(method, endpoint, token, json_payload=None):
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    r = requests.request(method, url, headers=headers, json=json_payload)

    if r.status_code == 429: # code 429 is error Zscaler throws for too many api request
        reset = int(r.headers.get("x-ratelimit-reset", 5))
        print(f"[RATE LIMIT] Sleeping for {reset} seconds...")
        time.sleep(reset)
        raise RateLimitError()
    elif r.status_code == 409: # code 409 is ZScaler saying someone else is making edits or configs (race condition expeption)
        print("[EDIT LOCK] Config is locked. Retrying after 5s...")
        time.sleep(5)
        raise EditLockError()
    elif r.status_code == 403 and r.headers.get("x-zscaler-mode") == "read-only": # code 403 means  Zscaler is in maintenance mode
        print("[READ-ONLY MODE] Zscaler is under maintenance. Retrying in 30s...")
        time.sleep(30)
        raise ReadOnlyError()
    elif r.status_code >= 500: # server side error, something on Zscaler's end
        raise requests.exceptions.HTTPError(f"Server error: {r.status_code}")
    elif r.ok:
        return r.json()
    else:
        print(f"[ERROR] {r.status_code} - {r.text}")
        r.raise_for_status()



# --- MAIN TASK: Denylist Update ---
def update_denylist(raw_url_input):
    try:
        cleaned_url = validate_url_input(raw_url_input)
        print(f"[VALIDATION] URL is clean: {cleaned_url}")
    except ValueError as ve:
        print(f"[INVALID INPUT] {ve}")
        return

    token = get_access_token()

    # Step 1: Get current denylist
    current = api_request("GET", "/security/advanced", token)
    denylist = current.get("blacklistUrls", [])

    # Step 2: Check if URL is already present
    if cleaned_url in denylist:
        print(f"[INFO] '{cleaned_url}' is already in the denylist.")
        return

    # Step 3: Add and update
    denylist.append(cleaned_url)
    payload = current
    payload["blacklistUrls"] = denylist

    # Step 4: Push updated denylist with race-condition retry protection
    api_request("PUT", "/security/advanced", token, json_payload=payload)
    print(f"[SUCCESS] '{cleaned_url}' added to the denylist.")

    # Step 5: Activate changes (with built-in handling)
    api_request("POST", "/status/activate", token)
    print("[ACTIVATION] Changes activated successfully.")



# --- Entry Point ---
if __name__ == "__main__":
    url_to_block = input("Enter the domain to block: ").strip()
    update_denylist(url_to_block)
