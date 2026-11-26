#!/usr/bin/env bash
# (Opsional / tahap lanjutan) Metric filter + alarm untuk validasi gagal, dan notifikasi SNS ke email.
# Jika layanan ditolak di Learner Lab, catat sebagai "future improvement".
set -euo pipefail
source "$(dirname "$0")/config.sh"
EMAIL="${1:?pakai: ./scripts/05_monitoring.sh email@kamu.com}"
LOG_GROUP="/aws/lambda/$FUNCTION_NAME"
TOPIC_ARN="$(aws sns create-topic --name incident-alerts --query TopicArn --output text)"
aws sns subscribe --topic-arn "$TOPIC_ARN" --protocol email --notification-endpoint "$EMAIL"
aws logs put-metric-filter --log-group-name "$LOG_GROUP" --filter-name ValidationFailed \
  --filter-pattern '{ $.event = "validation_failed" }' \
  --metric-transformations metricName=ValidationFailed,metricNamespace=IncidentAPI,metricValue=1
aws cloudwatch put-metric-alarm --alarm-name incident-api-validation-spike \
  --namespace IncidentAPI --metric-name ValidationFailed --statistic Sum --period 60 \
  --evaluation-periods 1 --threshold 5 --comparison-operator GreaterThanOrEqualToThreshold \
  --treat-missing-data notBreaching --alarm-actions "$TOPIC_ARN"
echo "Konfirmasi email langganan SNS di inbox kamu."
