# Load testing with Locust

This folder contains a Locust setup to stress test the FastAPI backend.

## Configuration
Copy `.env.example` to `.env` and fill credentials:

```
cp locust/.env.example locust/.env
```

Edit `locust/.env`:
- LOCUST_USERNAME / LOCUST_PASSWORD (required) used for /auth/login to get JWT
- API_KEY optional; sent only for endpoints tagged with APIKEY in list files
- TARGET_LIST_FILE, MIXED_LIST_FILE point to endpoint list files (default provided)
- PARAMS_FILE (default params.json) supplies placeholder pools

## Dynamic Path Parameters
Put placeholder value arrays in `params.json` (or file set by PARAMS_FILE). Example:
```
{
  "customer_id": ["uuid1", "uuid2"],
  "device_id": ["uuidA"],
  "solution_id": ["uuidS1", "uuidS2"]
}
```
Any `{customer_id}` in endpoint paths is replaced at request time with a random value from the list. If a placeholder lacks values, that request is skipped (to avoid 404 noise).

## Endpoint Lists
`target_endpoints.txt` and `mixed_endpoints.txt` include one path per line. Prefix with `APIKEY` (or `[apikey]`) to attach `X-API-KEY` header.

## Install
```
pip install -r locust/requirements.txt
```

## Run Web UI
```
locust -f locust/locustfile.py --host http://localhost:8000
```
Open http://localhost:8089 and start test.

## Run Headless Examples
Focused target list, 100 users, spawn 10/s for 5m:
```
locust -f locust/locustfile.py --headless -u 100 -r 10 --run-time 5m -t 5m --host http://localhost:8000 -T target
```
Mixed list with step shape (enable in .env):
```
USE_SHAPE=1 locust -f locust/locustfile.py --host http://localhost:8000 -T mixed
```

Tag selection:
- `-T target` only target list task
- `-T mixed` only mixed list task
- `-T health` simple health checks

## Adding Endpoints
Edit `target_endpoints.txt` or `mixed_endpoints.txt`. Use `APIKEY` prefix for endpoints needing X-API-KEY.

## Notes
- Update `params.json` with real UUIDs before testing.
- Reload requires restart to pick new param values (loaded on start).
- JWT acquired once per simulated user at start.
- If credentials invalid test will fail early.
- Step load shape is optional (USE_SHAPE=1). Otherwise specify users/spawn rate via CLI.
