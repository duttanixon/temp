import os
import random
from pathlib import Path
from typing import List, Tuple, Optional
from locust import HttpUser, task, between, tag, LoadTestShape
import json
import re
from datetime import datetime, timedelta, timezone

# Load .env (prefer .env, fallback to .env.example) ---------------------------------
try:
    from dotenv import load_dotenv  # type: ignore
    env_path = Path(__file__).with_name('.env')
    example_path = Path(__file__).with_name('.env.example')
    if env_path.exists():
        load_dotenv(env_path)
    elif example_path.exists():
        load_dotenv(example_path)
except Exception:
    pass

# Configuration ----------------------------------------------------------------------
API_PREFIX = os.getenv("API_PREFIX", "/api/v1")
USERNAME = os.getenv("LOCUST_USERNAME")
PASSWORD = os.getenv("LOCUST_PASSWORD")
API_KEY = os.getenv("API_KEY")  # Optional X-API-KEY

TARGET_LIST_FILE = os.getenv("TARGET_LIST_FILE", "target_endpoints.txt")
MIXED_LIST_FILE = os.getenv("MIXED_LIST_FILE", "mixed_endpoints.txt")

WAIT_MIN = float(os.getenv("LOCUST_WAIT_MIN", 0.1))
WAIT_MAX = float(os.getenv("LOCUST_WAIT_MAX", 0.5))

PARAMS_FILE = os.getenv("PARAMS_FILE", "params.json")
PARAM_VALUES = {}
PLACEHOLDER_PATTERN = re.compile(r"{([a-zA-Z_][a-zA-Z0-9_]*)}")
FULL_PLACEHOLDER_PATTERN = re.compile(r"^{([a-zA-Z_][a-zA-Z0-9_]*)}$")

def load_params():
    global PARAM_VALUES
    p = Path(__file__).with_name(PARAMS_FILE)
    if p.exists():
        try:
            data = json.loads(p.read_text())
            # Ensure values are lists
            PARAM_VALUES = {k: (v if isinstance(v, list) else [v]) for k, v in data.items()}
        except Exception:
            PARAM_VALUES = {}
    else:
        PARAM_VALUES = {}

# Endpoint list parsing ---------------------------------------------------------------
# Supported line formats:
# /api/v1/path
# APIKEY /api/v1/path
# POST /api/v1/path {"json":"body"}
# APIKEY POST /api/v1/path {"json":"body"}
# Body portion must be valid JSON and separated by a space.
# Placeholders like {device_id} substituted from params.json.

HTTP_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH"}
# Change endpoint tuple shape to (method, path, needs_api_key, body)
EndpointDef = Tuple[str, str, bool, Optional[dict]]

def parse_endpoint_line(raw: str) -> Optional[EndpointDef]:
    tokens = raw.split()
    if not tokens:
        return None
    needs_key = False
    idx = 0
    if tokens[idx].upper() in ("APIKEY", "[APIKEY]"):
        needs_key = True
        idx += 1
        if idx >= len(tokens):
            return None
    method = "GET"
    if tokens[idx].upper() in HTTP_METHODS:
        method = tokens[idx].upper()
        idx += 1
        if idx >= len(tokens):
            return None
    # Reconstruct remainder for path + optional JSON
    remainder = " ".join(tokens[idx:])
    body_dict = None
    # If there is a space then a '{' indicating JSON body
    if " {" in remainder:
        path_part, json_part = remainder.split(" {", 1)
        path = path_part.strip()
        json_text = "{" + json_part  # add back stripped '{'
        try:
            body_dict = json.loads(json_text)
        except Exception:
            body_dict = None
    else:
        path = remainder.strip()
    if not path.startswith('/'):
        path = '/' + path
    return (method, path, needs_key, body_dict)

def load_endpoint_list(path: str) -> List[EndpointDef]:
    results: List[EndpointDef] = []
    p = Path(__file__).with_name(path)
    if not p.exists():
        return results
    for line in p.read_text().splitlines():
        raw = line.strip()
        if not raw or raw.startswith('#'):
            continue
        ep = parse_endpoint_line(raw)
        if ep:
            results.append(ep)
    return results

TARGET_ENDPOINTS = load_endpoint_list(TARGET_LIST_FILE)
MIXED_ENDPOINTS = load_endpoint_list(MIXED_LIST_FILE)

def substitute_placeholders(path: str) -> str | None:
    """Return path with placeholders replaced using PARAM_VALUES or dynamic values.
    Dynamic supported: {today_date}, {yesterday_date} (UTC dates YYYY-MM-DD).
    If any non-dynamic placeholder lacks values, return None to skip the request."""
    today = datetime.now(timezone.utc).date()
    yesterday = today - timedelta(days=1)
    dynamic_map = {
        "today_date": today.strftime("%Y-%m-%d"),
        "yesterday_date": yesterday.strftime("%Y-%m-%d"),
    }
    missing = False
    def repl(m):
        key = m.group(1)
        if key in dynamic_map:
            return dynamic_map[key]
        values = PARAM_VALUES.get(key)
        if not values:
            nonlocal missing
            missing = True
            return m.group(0)
        return random.choice(values)
    new_path = PLACEHOLDER_PATTERN.sub(repl, path)
    if missing:
        return None
    return new_path

# NEW: JSON body placeholder substitution (supports full placeholder -> list expansion + dynamic values)

def substitute_body_placeholders(obj):
    """Recursively replace placeholder tokens in JSON body.
    Dynamic placeholders supported:
      {today_date}, {yesterday_date} -> YYYY-MM-DD
      {now_iso} -> current UTC timestamp (ISO 8601, Z)
      {three_weeks_ago_iso} -> UTC timestamp 21 days ago (ISO 8601, Z, start of day)
    If a string value is exactly a single placeholder (e.g. "{device_ids}") and the
    corresponding param value is a list with >1 items, the entire list is inserted.
    If only one value is present and the key name is plural (ends with 's'), a *list* is still returned
    to satisfy schemas expecting arrays (prevents 422 when only one device_id provided).
    Returns (new_obj, missing_flag)."""
    missing = False

    # Pre-compute dynamic values once
    now_dt = datetime.now(timezone.utc)
    three_weeks_ago = (now_dt - timedelta(days=21)).replace(hour=0, minute=0, second=0, microsecond=0)
    dynamic_map = {
        "today_date": now_dt.strftime("%Y-%m-%d"),
        "yesterday_date": (now_dt - timedelta(days=1)).strftime("%Y-%m-%d"),
        "now_iso": now_dt.isoformat().replace('+00:00', 'Z'),
        "three_weeks_ago_iso": three_weeks_ago.isoformat().replace('+00:00', 'Z'),
    }

    def _sub(o, parent_key: Optional[str] = None):
        nonlocal missing
        if isinstance(o, dict):
            return {k: _sub(v, k) for k, v in o.items()}
        if isinstance(o, list):
            return [_sub(v, parent_key) for v in o]
        if isinstance(o, str):
            full = FULL_PLACEHOLDER_PATTERN.match(o)
            if full:
                key = full.group(1)
                # Dynamic placeholder
                if key in dynamic_map:
                    return dynamic_map[key]
                values = PARAM_VALUES.get(key)
                if not values:
                    missing = True
                    return o
                # If multiple values, return full list
                if len(values) > 1:
                    return values
                # If only one value but field expects list (heuristic: plural key OR parent_key plural) return list
                if len(values) == 1 and (key.endswith('s') or (parent_key and parent_key.endswith('s'))):
                    return values
                return values[0]
            # Partial replacement inside string (may mix static + placeholders)
            def repl(m):
                key = m.group(1)
                if key in dynamic_map:
                    return dynamic_map[key]
                values = PARAM_VALUES.get(key)
                if not values:
                    nonlocal missing
                    missing = True
                    return m.group(0)
                return random.choice(values)
            return PLACEHOLDER_PATTERN.sub(repl, o)
        return o

    return _sub(obj), missing

class FastAPIUser(HttpUser):
    wait_time = between(WAIT_MIN, WAIT_MAX)

    def on_start(self):
        load_params()
        if not (USERNAME and PASSWORD):
            raise RuntimeError("LOCUST_USERNAME and LOCUST_PASSWORD must be set in .env for authentication")
        self.token = None
        # Perform login to obtain JWT
        with self.client.post(
            f"{API_PREFIX}/auth/login",
            data={"username": USERNAME, "password": PASSWORD},
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                self.token = resp.json().get("access_token")
                if not self.token:
                    resp.failure("Login succeeded but no access_token in response")
            else:
                resp.failure(f"Login failed: {resp.status_code} {resp.text}")

    # Header helpers -----------------------------------------------------------------
    def base_headers(self):
        return {"Content-Type": "application/json"}

    def auth_headers(self, needs_api_key: bool = False):
        headers = self.base_headers()
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if needs_api_key and API_KEY:
            headers["X-API-KEY"] = API_KEY
        return headers

    # Tasks -------------------------------------------------------------------------
    @tag("target")
    @task(5)
    def target_endpoints(self):
        if not TARGET_ENDPOINTS:
            return
        method, path, needs_key, body = random.choice(TARGET_ENDPOINTS)
        substituted = substitute_placeholders(path)
        if substituted is None:
            return
        headers = self.auth_headers(needs_key)
        send_body = None
        if body is not None:
            send_body, missing = substitute_body_placeholders(body)
            if missing:
                return
        if method == 'GET':
            self.client.get(substituted, headers=headers)
        elif method == 'POST':
            self.client.post(substituted, json=send_body, headers=headers)
        elif method == 'PUT':
            self.client.put(substituted, json=send_body, headers=headers)
        elif method == 'DELETE':
            self.client.delete(substituted, headers=headers)
        else:
            self.client.request(method, substituted, json=send_body, headers=headers)

    @tag("mixed")
    @task(5)
    def mixed_endpoints(self):
        if not MIXED_ENDPOINTS:
            return
        method, path, needs_key, body = random.choice(MIXED_ENDPOINTS)
        substituted = substitute_placeholders(path)
        if substituted is None:
            return
        headers = self.auth_headers(needs_key)
        send_body = None
        if body is not None:
            send_body, missing = substitute_body_placeholders(body)
            if missing:
                return
        if method == 'GET':
            self.client.get(substituted, headers=headers)
        elif method == 'POST':
            self.client.post(substituted, json=send_body, headers=headers)
        elif method == 'PUT':
            self.client.put(substituted, json=send_body, headers=headers)
        elif method == 'DELETE':
            self.client.delete(substituted, headers=headers)
        else:
            self.client.request(method, substituted, json=send_body, headers=headers)

    # Optional simple health check (useful even if not in lists)
    @tag("health")
    @task(1)
    def health(self):
        self.client.get("/health")

# Optional step load shape -----------------------------------------------------------
if os.getenv("USE_SHAPE", "0") == "1":
    class StepLoadShape(LoadTestShape):
        """Ramps up users in steps to probe capacity.
        Env vars: STEP_TIME, STEP_USERS, SPAWN_RATE, TIME_LIMIT"""
        step_time = int(os.getenv("STEP_TIME", 30))
        step_users = int(os.getenv("STEP_USERS", 25))
        spawn_rate = float(os.getenv("SPAWN_RATE", 10))
        time_limit = int(os.getenv("TIME_LIMIT", 600))

        def tick(self):
            run_time = self.get_run_time()
            if run_time > self.time_limit:
                return None
            step = int(run_time // self.step_time) + 1
            user_count = step * self.step_users
            return (user_count, self.spawn_rate)
