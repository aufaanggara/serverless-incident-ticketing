#!/usr/bin/env bash
# Uji seluruh endpoint CRUD. Pemakaian: ./scripts/04_test_crud.sh   (Function URL diambil otomatis)
set -euo pipefail
source "$(dirname "$0")/config.sh"
URL="$(aws lambda get-function-url-config --function-name "$FUNCTION_NAME" --query FunctionUrl --output text)"
URL="${URL%/}"
show() { echo; echo "### $1"; }

show "Health check (GET /)";            curl -s -w '\nHTTP %{http_code}\n' "$URL/"
show "CREATE (POST /incidents)"
CREATED="$(curl -s -X POST "$URL/incidents" -H 'Content-Type: application/json' \
  -d '{"title":"Phishing Email","description":"Suspicious login link","severity":"high","reported_by":"admin"}')"
echo "$CREATED"
ID="$(echo "$CREATED" | python3 -c 'import sys,json;print(json.load(sys.stdin)["incident_id"])')"
show "READ ALL (GET /incidents)";       curl -s -w '\nHTTP %{http_code}\n' "$URL/incidents"
show "READ ONE (GET /incidents/$ID)";   curl -s -w '\nHTTP %{http_code}\n' "$URL/incidents/$ID"
show "UPDATE (PUT /incidents/$ID)";     curl -s -w '\nHTTP %{http_code}\n' -X PUT "$URL/incidents/$ID" \
  -H 'Content-Type: application/json' -d '{"status":"investigating"}'
show "VALIDASI (severity salah -> 400)"; curl -s -w '\nHTTP %{http_code}\n' -X POST "$URL/incidents" \
  -H 'Content-Type: application/json' -d '{"title":"x","severity":"super"}'
show "DELETE (DELETE /incidents/$ID)";  curl -s -w '\nHTTP %{http_code}\n' -X DELETE "$URL/incidents/$ID"
show "READ setelah delete (404)";       curl -s -w '\nHTTP %{http_code}\n' "$URL/incidents/$ID"
