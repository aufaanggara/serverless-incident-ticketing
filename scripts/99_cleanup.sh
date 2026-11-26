#!/usr/bin/env bash
# Amankan / bersihkan setelah screenshot selesai.
#   ./scripts/99_cleanup.sh secure  -> Function URL diubah ke AWS_IAM (tidak publik lagi)
#   ./scripts/99_cleanup.sh all     -> hapus Function URL, Lambda, dan tabel DynamoDB
set -euo pipefail
source "$(dirname "$0")/config.sh"
case "${1:-secure}" in
  secure) aws lambda update-function-url-config --function-name "$FUNCTION_NAME" --auth-type AWS_IAM ;;
  all)
    aws lambda delete-function-url-config --function-name "$FUNCTION_NAME" || true
    aws lambda delete-function --function-name "$FUNCTION_NAME" || true
    aws dynamodb delete-table --table-name "$TABLE_NAME" || true ;;
  *) echo "pakai: secure | all"; exit 1 ;;
esac
