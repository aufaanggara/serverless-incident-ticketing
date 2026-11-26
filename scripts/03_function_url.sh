#!/usr/bin/env bash
# Membuat Lambda Function URL (endpoint HTTPS). Default AUTH_TYPE=NONE agar bisa dites dengan curl.
# Untuk setelah pengujian: AUTH_TYPE=AWS_IAM ./scripts/03_function_url.sh (atau jalankan 99_cleanup.sh).
set -euo pipefail
source "$(dirname "$0")/config.sh"
AUTH_TYPE="${AUTH_TYPE:-NONE}"

if aws lambda get-function-url-config --function-name "$FUNCTION_NAME" >/dev/null 2>&1; then
  aws lambda update-function-url-config --function-name "$FUNCTION_NAME" --auth-type "$AUTH_TYPE"
else
  aws lambda create-function-url-config --function-name "$FUNCTION_NAME" --auth-type "$AUTH_TYPE"
fi

if [ "$AUTH_TYPE" = "NONE" ]; then
  # Izin invoke publik (hanya untuk pengujian). Error "already exists" boleh diabaikan.
  aws lambda add-permission --function-name "$FUNCTION_NAME" --statement-id FunctionURLAllowPublicAccess \
    --action lambda:InvokeFunctionUrl --principal "*" --function-url-auth-type NONE 2>/dev/null || true
  aws lambda add-permission --function-name "$FUNCTION_NAME" --statement-id FunctionURLAllowInvoke \
    --action lambda:InvokeFunction --principal "*" 2>/dev/null || true
fi
aws lambda get-function-url-config --function-name "$FUNCTION_NAME" \
  --query '{Url:FunctionUrl,Auth:AuthType}'
