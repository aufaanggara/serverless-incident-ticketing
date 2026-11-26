# Serverless Security Incident Ticketing System (Track C)

Sistem tiket insiden keamanan berbasis AWS Serverless (Lambda Function URL, AWS Lambda Python, DynamoDB/S3) untuk proyek individu Komputasi Awan. Sistem ini dirancang untuk melaporkan dan melacak insiden keamanan dengan prinsip *blue team* (*least privilege*, logging, dan validasi input).

## Architecture
![Architecture Diagram](docs/architecture.png)

Alur utama: `Client → Lambda Function URL → AWS Lambda (Python) → DynamoDB (fallback: S3)`

> **Catatan Kendala AWS Learner Lab:** Karena izin `dynamodb:CreateTable` dan akses API Gateway dibatasi di lingkungan sandbox, endpoint menggunakan **Lambda Function URL** dan penyimpanan menggunakan lapisan abstraksi yang mendukung **S3** sebagai *fallback*.

## Repository Structure
```text
.
├── docs/
│   ├── architecture.png
│   └── Design_Brief_Incident_Ticketing.docx
├── evidence/
│   └── (screenshot & log pengujian AWS)
├── src/
│   └── lambda_function.py
└── README.md
```

## API Endpoints
| Method | Endpoint | Fungsi | Status Sukses |
| :--- | :--- | :--- | :--- |
| `POST` | `/incidents` | Membuat tiket insiden baru | `201` |
| `GET` | `/incidents` | Melihat semua tiket | `200` |
| `GET` | `/incidents/{id}` | Melihat detail satu tiket | `200` |
| `PUT` | `/incidents/{id}` | Mengubah `status` atau `severity` | `200` |
| `DELETE` | `/incidents/{id}` | Menghapus tiket | `200` |

## Deployment Plan
1. **Storage Setup:** Membuat tabel DynamoDB `incidents` (partition key: `incident_id`), atau S3 Bucket di region `us-east-1` sebagai *fallback* di AWS Learner Lab jika `dynamodb:CreateTable` ditolak.
2. **Lambda Function:** Deploy `src/lambda_function.py` (Runtime Python 3.12) menggunakan IAM `LabRole`.
3. **Environment Variables:** Tambahkan variabel berikut pada konfigurasi Lambda:
   - `STORAGE_BACKEND`: `s3` (atau `dynamodb` jika tersedia)
   - `BUCKET_NAME`: `<nama-bucket>`
4. **Endpoint Exposure:** Aktifkan **Lambda Function URL** (`Auth type: NONE`) sebagai pengganti API Gateway.
5. **Verification & Monitoring:** Uji endpoint menggunakan `curl` / Postman dan pantau log eksekusi serta error melalui Amazon CloudWatch.

## Quick Test
```bash
# Health check
curl -X GET <LAMBDA_FUNCTION_URL>

# Create incident
curl -X POST <LAMBDA_FUNCTION_URL>/incidents \
  -H "Content-Type: application/json" \
  -d '{"title":"Phishing Email","description":"Suspicious login link","severity":"high","reported_by":"admin"}'
```