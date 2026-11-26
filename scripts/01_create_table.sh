#!/usr/bin/env bash
# Membuat tabel DynamoDB. Di Learner Lab, dynamodb:CreateTable bisa ditolak untuk role voclabs.
# Jika AccessDenied: jalankan `aws configure` dengan kredensial IAM user awsstudent
# (JANGAN commit kredensial), lalu ulangi script ini. Setelah tabel jadi, kembalikan kredensial.
set -euo pipefail
source "$(dirname "$0")/config.sh"
aws sts get-caller-identity
aws dynamodb create-table \
  --table-name "$TABLE_NAME" \
  --attribute-definitions AttributeName=incident_id,AttributeType=S \
  --key-schema AttributeName=incident_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
aws dynamodb wait table-exists --table-name "$TABLE_NAME"
aws dynamodb describe-table --table-name "$TABLE_NAME" \
  --query 'Table.{Name:TableName,Status:TableStatus,Key:KeySchema,Billing:BillingModeSummary.BillingMode}'
