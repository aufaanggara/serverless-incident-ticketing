#!/usr/bin/env bash
# Package src/lambda_function.py lalu buat (atau update) fungsi Lambda dengan LabRole.
set -euo pipefail
source "$(dirname "$0")/config.sh"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
(cd "$ROOT/src" && zip -q -j /tmp/function.zip lambda_function.py)

if aws lambda get-function --function-name "$FUNCTION_NAME" >/dev/null 2>&1; then
  aws lambda update-function-code --function-name "$FUNCTION_NAME" --zip-file fileb:///tmp/function.zip
else
  aws lambda create-function \
    --function-name "$FUNCTION_NAME" \
    --runtime "$RUNTIME" \
    --handler lambda_function.lambda_handler \
    --role "$ROLE_ARN" \
    --zip-file fileb:///tmp/function.zip \
    --timeout 10 --memory-size 128 \
    --environment "Variables={TABLE_NAME=$TABLE_NAME}"
fi
aws lambda wait function-active-v2 --function-name "$FUNCTION_NAME"
echo "Lambda $FUNCTION_NAME siap."
