import base64
import html
import json
import os
import requests
from flask import Flask, request, render_template

app = Flask(__name__)

# -------- ORG / APP SETTINGS (Using Environment Variables) --------
LOGIN_URL = os.getenv("SF_LOGIN_URL", "https://login.salesforce.com")
API_VERSION = os.getenv("SF_API_VERSION", "v64.0")
CLIENT_ID = os.getenv("SF_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("SF_CLIENT_SECRET", "")
USERNAME = os.getenv("SF_USERNAME", "")
PASSWORD = os.getenv("SF_PASSWORD", "")

CONFIG_API_NAME = os.getenv("CONFIG_API_NAME", "customercall_transcript_schema")
ML_MODEL = os.getenv("ML_MODEL", "llmgateway__OpenAIGPT4Omni_08_06")

FIELD_API = {
    "first": os.getenv("FIELD_FIRST", "First_Name"),
    "last": os.getenv("FIELD_LAST", "Last_Name")
}

# -------- Helpers --------
def headers_json(tok: str):
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}

def ssot_base(inst: str) -> str:
    return f"{inst}/services/data/{API_VERSION}/ssot/document-processing"

# -------- Auth --------
def oauth_login():
    token_url = f"{LOGIN_URL}/services/oauth2/token"
    data = {
        "grant_type": "password",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "username": USERNAME,
        "password": PASSWORD,
    }
    r = requests.post(token_url, data=data)
    if r.status_code != 200:
        raise Exception(f"Login failed: {r.text}")
    j = r.json()
    return j.get("access_token"), j.get("instance_url")

# -------- Document AI Extraction --------
def _has_nonempty_inner(body: dict) -> bool:
    data_list = body.get("data")
    if isinstance(data_list, list) and data_list:
        inner_str = data_list[0].get("data")
        if not inner_str:
            return False
        try:
            parsed = json.loads(html.unescape(inner_str))
            return isinstance(parsed, dict) and len(parsed) > 0
        except Exception:
            return False
    return False

def build_min_schema() -> str:
    props = {
        FIELD_API["first"]: {"type": "string"},
        FIELD_API["last"]: {"type": "string"}
    }
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "ContactFields",
        "type": "object",
        "properties": props,
        "required": []
    }
    return json.dumps(schema)

def extract_with_config(instance_url: str, token: str, file_b64: str) -> dict:
    url = f"{ssot_base(instance_url)}/actions/extract-data"
    
    # Step 1: Try with config
    payload1 = {
        "idpConfigurationIdOrName": CONFIG_API_NAME,
        "files": [{"data": file_b64, "mimeType": "application/pdf"}]
    }
    r1 = requests.post(url, headers=headers_json(token), data=json.dumps(payload1))
    if r1.status_code in (200, 201) and _has_nonempty_inner(r1.json()):
        return r1.json()

    # Step 2: Fallback to schema
    payload2 = {
        "schemaConfig": build_min_schema(),
        "mlModel": ML_MODEL,
        "files": [{"data": file_b64, "mimeType": "application/pdf"}]
    }
    r2 = requests.post(url, headers=headers_json(token), data=json.dumps(payload2))
    if r2.status_code in (200, 201) and _has_nonempty_inner(r2.json()):
        return r2.json()

    raise Exception("Extraction returned empty JSON or failed. Check document and schema.")

def parse_extracted_values(extract_body: dict) -> dict:
    data_list = extract_body.get("data")
    if isinstance(data_list, list) and data_list:
        inner_str = data_list[0].get("data")
        if inner_str:
            inner = json.loads(html.unescape(inner_str))
            if isinstance(inner, dict):
                flat = {}
                for k, v in inner.items():
                    if isinstance(v, dict) and "value" in v:
                        flat[k.lower()] = v.get("value")
                    else:
                        flat[k.lower()] = v
                return flat
    return {}

# -------- Web Routes --------
@app.route("/", methods=["GET", "POST"])
def index():
    extracted_data = None
    error_message = None

    if request.method == "POST":
        if "document" not in request.files:
            error_message = "No file uploaded."
        else:
            file = request.files["document"]
            if file.filename == "":
                error_message = "No file selected."
            else:
                try:
                    # Convert file to base64 directly from memory
                    file_bytes = file.read()
                    file_b64 = base64.b64encode(file_bytes).decode("utf-8")

                    token, instance_url = oauth_login()
                    body = extract_with_config(instance_url, token, file_b64)
                    flat = parse_extracted_values(body)

                    extracted_data = {
                        "first_name": flat.get(FIELD_API["first"].lower(), "Not Found"),
                        "last_name": flat.get(FIELD_API["last"].lower(), "Not Found"),
                        "raw_data": str(flat) # X-Ray Vision Debug Data
                    }
                except Exception as e:
                    error_message = str(e)

    return render_template("index.html", data=extracted_data, error=error_message)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
