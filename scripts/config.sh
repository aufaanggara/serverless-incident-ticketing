#!/usr/bin/env bash
# Konfigurasi bersama. Jalankan semua script dari AWS CloudShell (region us-east-1).
export AWS_REGION="${AWS_REGION:-us-east-1}"
export AWS_DEFAULT_REGION="$AWS_REGION"
export TABLE_NAME="${TABLE_NAME:-incidents}"
export FUNCTION_NAME="${FUNCTION_NAME:-incident-api}"
export RUNTIME="python3.12"
export ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
export ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/LabRole"
