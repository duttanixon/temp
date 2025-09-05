import os
import random
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from locust import HttpUser, task, between, tag  # added tag
from dotenv import load_dotenv
import yaml  # type: ignore

# Load env -----------------------------------------------------------------
try:
    env_path = Path(__file__).with_name('.env')
    if env_path.exists():
        load_dotenv(env_path)
except Exception:
    pass

API_PREFIX = os.getenv("API_PREFIX", "/api/v1")
USERNAME = os.getenv("LOCUST_USERNAME")
PASSWORD = os.getenv("LOCUST_PASSWORD")
API_KEY = os.getenv("API_KEY")

WAIT_MIN = float(os.getenv("LOCUST_WAIT_MIN", 0.1))
WAIT_MAX = float(os.getenv("LOCUST_WAIT_MAX", 0.5))

PARAMS_FILE = os.getenv("PARAMS_FILE", "params.json")
ENDPOINTS_FILE = os.getenv("ENDPOINTS_FILE", "endpoints.yml")

# ---------------------------------------------------------------------------
# Utility loading
# ---------------------------------------------------------------------------

def load_params() -> Dict[str, List[str]]:
    p = Path(__file__).with_name(PARAMS_FILE)
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text())
        return {k: (v if isinstance(v, list) else [v]) for k, v in data.items()}
    except Exception:
        return {}

def load_endpoints() -> List[Dict[str, Any]]:
    p = Path(__file__).with_name(ENDPOINTS_FILE)
    if not p.exists():
        return []
    try:
        data = yaml.safe_load(p.read_text())
        if not isinstance(data, list):
            return []
        # Normalize defaults
        for ep in data:
            ep.setdefault('method', 'GET')
            ep.setdefault('weight', 1)
            ep.setdefault('needs_api_key', False)
        return data
    except Exception:
        return []

# ---------------------------------------------------------------------------
# Placeholder substitution (simple, no regex required)
# ---------------------------------------------------------------------------
DYNAMIC_KEYS = {"today_date", "yesterday_date", "now_iso", "three_weeks_ago_iso"}

def dynamic_values() -> Dict[str, str]:
    now_dt = datetime.now(timezone.utc)
    return {
        "today_date": now_dt.strftime('%Y-%m-%d'),
        "yesterday_date": (now_dt - timedelta(days=1)).strftime('%Y-%m-%d'),
        "now_iso": now_dt.isoformat().replace('+00:00', 'Z'),
        "three_weeks_ago_iso": (now_dt - timedelta(days=21)).replace(hour=0, minute=0, second=0, microsecond=0).isoformat().replace('+00:00', 'Z'),
    }

def substitute_scalar(value: str, params: Dict[str, List[str]], dyn: Dict[str, str]):
    if not isinstance(value, str):
        return value
    # Exact placeholder in braces
    if value.startswith('{') and value.endswith('}') and value.count('{') == 1 and value.count('}') == 1:
        key = value[1:-1]
        if key in dyn:
            return dyn[key]
        values = params.get(key)
        if not values:
            return value  # leave unreplaced (request may fail) to surface config issues
        # If plural key (endswith 's') always return full list
        if key.endswith('s'):
            return values
        return random.choice(values)
    # Inline replacements (simple scan)
    out = value
    for key, dyn_val in dyn.items():
        out = out.replace(f'{{{key}}}', dyn_val)
    for key, values in params.items():
        if f'{{{key}}}' in out:
            rep = random.choice(values) if not key.endswith('s') else json.dumps(values)
            out = out.replace(f'{{{key}}}', rep)
    return out

def substitute_body(body: Any, params: Dict[str, List[str]], dyn: Dict[str, str]):
    if body is None:
        return None
    if isinstance(body, dict):
        return {k: substitute_body(v, params, dyn) for k, v in body.items()}
    if isinstance(body, list):
        return [substitute_body(v, params, dyn) for v in body]
    if isinstance(body, str):
        val = substitute_scalar(body, params, dyn)
        # If we inserted a JSON array string via inline replacement (for plural) try to parse
        if isinstance(val, str) and val.startswith('[') and val.endswith(']'):
            try:
                return json.loads(val)
            except Exception:
                return val
        return val
    return body

def substitute_path(path: str, params: Dict[str, List[str]], dyn: Dict[str, str]):
    out = path
    for key, dyn_val in dyn.items():
        out = out.replace(f'{{{key}}}', dyn_val)
    for key, values in params.items():
        if f'{{{key}}}' in out:
            replacement = random.choice(values)
            out = out.replace(f'{{{key}}}', replacement)
    return out

# ---------------------------------------------------------------------------
# Locust user
# ---------------------------------------------------------------------------
class FastAPIUser(HttpUser):
    wait_time = between(WAIT_MIN, WAIT_MAX)
    # class-level caches
    params: Dict[str, List[str]] = {}
    endpoints: List[Dict[str, Any]] = []
    weighted_indices: List[int] = []

    @classmethod
    def build_weighted_indices(cls):
        cls.weighted_indices = []
        for idx, ep in enumerate(cls.endpoints):
            cls.weighted_indices.extend([idx] * int(ep.get('weight', 1)))

    @classmethod
    def reload_config(cls):
        cls.params = load_params()
        cls.endpoints = load_endpoints()
        cls.build_weighted_indices()

    def ensure_loaded(self):
        if not type(self).endpoints:  # load once per worker
            type(self).reload_config()

    def on_start(self):
        self.ensure_loaded()
        if not (USERNAME and PASSWORD):
            raise RuntimeError("LOCUST_USERNAME and LOCUST_PASSWORD must be set")
        with self.client.post(f"{API_PREFIX}/auth/login", data={"username": USERNAME, "password": PASSWORD}, catch_response=True) as r:
            if r.status_code == 200:
                self.token = r.json().get('access_token')
            else:
                r.failure(f"Login failed: {r.status_code} {r.text}")
                self.token = None

    def auth_headers(self, needs_api_key: bool = False):
        h = {"Content-Type": "application/json"}
        if getattr(self, 'token', None):
            h['Authorization'] = f"Bearer {self.token}"
        if needs_api_key and API_KEY:
            h['X-API-KEY'] = API_KEY
        return h

    @tag("mixed")
    @task
    def hit_endpoint(self):
        self.ensure_loaded()
        if not self.weighted_indices:
            return
        idx = random.choice(self.weighted_indices)
        ep = self.endpoints[idx]

        dyn = dynamic_values()
        path = substitute_path(ep['path'], self.params, dyn)
        method = ep.get('method', 'GET').upper()
        needs_api_key = ep.get('needs_api_key', False)
        body = substitute_body(ep.get('body'), self.params, dyn)
        headers = self.auth_headers(needs_api_key)

        if method == 'GET':
            self.client.get(path, headers=headers)
        elif method == 'POST':
            self.client.post(path, json=body, headers=headers)
        elif method == 'PUT':
            self.client.put(path, json=body, headers=headers)
        elif method == 'DELETE':
            self.client.delete(path, headers=headers)
        else:
            self.client.request(method, path, json=body, headers=headers)
