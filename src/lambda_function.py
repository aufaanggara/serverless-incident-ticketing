"""Serverless Security Incident Ticketing System - Lambda handler (Track C).

Dipanggil lewat Lambda Function URL (payload format v2).
Penyimpanan: DynamoDB (nama tabel dari env TABLE_NAME, default "incidents").
Akses AWS memakai execution role (LabRole di Learner Lab), tanpa access key di kode.
"""
import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TABLE_NAME = os.environ.get("TABLE_NAME", "incidents")
_table = None

VALID_SEVERITY = {"low", "medium", "high", "critical"}
VALID_STATUS = {"open", "investigating", "resolved"}
CREATE_FIELDS = {"title", "description", "severity", "status", "reported_by"}
UPDATE_FIELDS = {"title", "description", "severity", "status"}
MAX_LEN = {"title": 100, "description": 1000, "reported_by": 100}
UUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")


def get_table():
    global _table
    if _table is None:
        _table = boto3.resource("dynamodb").Table(TABLE_NAME)
    return _table


def response(status, body):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def log_event(kind, **data):
    """Log terstruktur (JSON) ke CloudWatch, bahan metric filter / alarm."""
    logger.info(json.dumps({"event": kind, **data}))


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def validate(body, allowed, required=()):
    """Return pesan error, atau None kalau input valid."""
    if not isinstance(body, dict):
        return "Body harus berupa objek JSON"
    unknown = set(body) - allowed
    if unknown:
        return f"Field tidak dikenal: {sorted(unknown)}"
    for f in required:
        if not str(body.get(f, "")).strip():
            return f"Field wajib diisi: {f}"
    for f, limit in MAX_LEN.items():
        if f in body and (not isinstance(body[f], str) or len(body[f]) > limit):
            return f"{f} harus string, maks. {limit} karakter"
    if "severity" in body and body["severity"] not in VALID_SEVERITY:
        return f"severity harus salah satu dari {sorted(VALID_SEVERITY)}"
    if "status" in body and body["status"] not in VALID_STATUS:
        return f"status harus salah satu dari {sorted(VALID_STATUS)}"
    return None


def create_incident(body):
    err = validate(body, CREATE_FIELDS, required=("title",))
    if err:
        log_event("validation_failed", op="create", reason=err)
        return response(400, {"error": err})
    ts = now_iso()
    item = {
        "incident_id": str(uuid.uuid4()),
        "title": body["title"].strip(),
        "description": body.get("description", ""),
        "severity": body.get("severity", "low"),
        "status": body.get("status", "open"),
        "reported_by": body.get("reported_by", "anonymous"),
        "created_at": ts,
        "updated_at": ts,
    }
    get_table().put_item(Item=item)
    log_event("incident_created", incident_id=item["incident_id"], severity=item["severity"])
    return response(201, item)


def list_incidents():
    result = get_table().scan(Limit=100)
    items = result.get("Items", [])
    return response(200, {"count": len(items), "items": items})


def get_incident(incident_id):
    item = get_table().get_item(Key={"incident_id": incident_id}).get("Item")
    if not item:
        log_event("not_found", op="get", incident_id=incident_id)
        return response(404, {"error": "Incident tidak ditemukan"})
    return response(200, item)


def update_incident(incident_id, body):
    err = validate(body, UPDATE_FIELDS)
    if err or not body:
        err = err or "Tidak ada field yang diubah"
        log_event("validation_failed", op="update", reason=err)
        return response(400, {"error": err})
    body = dict(body, updated_at=now_iso())
    names = {f"#{k}": k for k in body}
    values = {f":{k}": v for k, v in body.items()}
    expr = "SET " + ", ".join(f"#{k} = :{k}" for k in body)
    try:
        res = get_table().update_item(
            Key={"incident_id": incident_id},
            UpdateExpression=expr,
            ExpressionAttributeNames=names,
            ExpressionAttributeValues=values,
            ConditionExpression="attribute_exists(incident_id)",
            ReturnValues="ALL_NEW",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            log_event("not_found", op="update", incident_id=incident_id)
            return response(404, {"error": "Incident tidak ditemukan"})
        raise
    log_event("incident_updated", incident_id=incident_id, fields=sorted(set(body) - {"updated_at"}))
    return response(200, res["Attributes"])


def delete_incident(incident_id):
    try:
        get_table().delete_item(
            Key={"incident_id": incident_id},
            ConditionExpression="attribute_exists(incident_id)",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            log_event("not_found", op="delete", incident_id=incident_id)
            return response(404, {"error": "Incident tidak ditemukan"})
        raise
    log_event("incident_deleted", incident_id=incident_id)
    return response(200, {"message": "Incident dihapus", "incident_id": incident_id})


def lambda_handler(event, context):
    http = event.get("requestContext", {}).get("http", {})
    method = http.get("method", "GET")
    path = http.get("path", "/").rstrip("/") or "/"
    source_ip = http.get("sourceIp", "unknown")
    log_event("request", method=method, path=path, source_ip=source_ip)

    try:
        if path == "/" and method == "GET":
            return response(200, {"message": "Incident Ticketing API is active", "storage": "dynamodb"})

        parts = path.strip("/").split("/")
        if parts[0] != "incidents" or len(parts) > 2:
            return response(404, {"error": "Route tidak ditemukan"})

        if len(parts) == 1:
            if method == "POST":
                try:
                    body = json.loads(event.get("body") or "{}")
                except json.JSONDecodeError:
                    log_event("validation_failed", op="create", reason="invalid_json")
                    return response(400, {"error": "Body bukan JSON yang valid"})
                return create_incident(body)
            if method == "GET":
                return list_incidents()
        else:
            incident_id = parts[1]
            if not UUID_RE.match(incident_id):
                return response(400, {"error": "incident_id tidak valid"})
            if method == "GET":
                return get_incident(incident_id)
            if method == "PUT":
                try:
                    body = json.loads(event.get("body") or "{}")
                except json.JSONDecodeError:
                    return response(400, {"error": "Body bukan JSON yang valid"})
                return update_incident(incident_id, body)
            if method == "DELETE":
                return delete_incident(incident_id)

        return response(405, {"error": "Method tidak diizinkan"})
    except Exception:  # jangan bocorkan detail internal ke client
        logger.exception("unhandled_error")
        return response(500, {"error": "Internal server error"})
