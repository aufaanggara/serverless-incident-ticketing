import json
import os
import uuid
from datetime import datetime, timezone
import boto3

STORAGE_BACKEND = os.environ.get("STORAGE_BACKEND", "s3")  # "s3" atau "dynamodb"
BUCKET_NAME = os.environ.get("BUCKET_NAME", "")

VALID_SEVERITY = {"low", "medium", "high", "critical"}
VALID_STATUS = {"open", "investigating", "resolved"}

s3 = boto3.client("s3")


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def save_incident(incident):
    if STORAGE_BACKEND == "s3" and BUCKET_NAME:
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=f"incidents/{incident['incident_id']}.json",
            Body=json.dumps(incident),
            ContentType="application/json",
        )
    return incident


def lambda_handler(event, context):
    http = event.get("requestContext", {}).get("http", {})
    method = http.get("method", "GET")
    path = http.get("path", "/")

    # Health check / Function test
    if method == "GET" and path == "/":
        return response(200, {"message": "Incident Ticketing API is active", "storage": STORAGE_BACKEND})

    # Create incident (POST /incidents)
    if method == "POST" and path == "/incidents":
        try:
            body = json.loads(event.get("body") or "{}")
        except json.JSONDecodeError:
            return response(400, {"error": "Invalid JSON body"})

        severity = body.get("severity", "low")
        status = body.get("status", "open")

        if severity not in VALID_SEVERITY or status not in VALID_STATUS:
            return response(400, {"error": "Invalid severity or status"})

        now = datetime.now(timezone.utc).isoformat()
        incident = {
            "incident_id": str(uuid.uuid4()),
            "title": str(body.get("title", ""))[:100],
            "description": str(body.get("description", ""))[:1000],
            "severity": severity,
            "status": status,
            "reported_by": str(body.get("reported_by", "anonymous")),
            "created_at": now,
            "updated_at": now,
        }

        save_incident(incident)
        return response(201, incident)

    # Placeholder untuk GET /incidents, PUT /incidents/{id}, DELETE /incidents/{id}
    return response(200, {"message": f"Route {method} {path} ready for implementation"})