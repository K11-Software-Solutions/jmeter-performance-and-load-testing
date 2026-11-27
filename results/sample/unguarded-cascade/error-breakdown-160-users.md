# 160-user step WITHOUT the If Controller guards: failed samples by code and label

Same mock settings (POOL_SIZE=4, QUEUE_TIMEOUT_MS=2000). Server-side /metrics counted 727 HTTP 503 responses in this step.

| Count | Response code | Label |
|---:|---|---|
| 1042 | 404 | GET /api/reports/exports/{exportId} |
| 679 | 401 | GET /api/reports/exports/{exportId} |
| 242 | 401 | GET /api/dashboard |
| 230 | 503 | GET /api/dashboard |
| 159 | 401 | GET /api/reports/claims-summary |
| 153 | 503 | GET /api/reports/claims-summary |
| 121 | 503 | POST /api/auth/login |
| 98 | 404 | GET /api/reports/exports/{exportId}/download |
| 71 | 401 | GET /api/reports/claims-summary (before export) |
| 71 | 401 | POST /api/reports/claims-summary/export |
| 64 | 401 | GET /api/reports/exports/{exportId}/download |
| 58 | 503 | GET /api/reports/exports/{exportId} |
| 58 | 503 | GET /api/reports/exports/{exportId}/download |
| 57 | 503 | GET /api/reports/claims-summary (before export) |
| 57 | 404 | POST /api/reports/claims-summary/export |
| 50 | 503 | POST /api/reports/claims-summary/export |

**Totals:** 3210 failed of 7158 samples. 401: 1286, 404: 1197, 503: 727
