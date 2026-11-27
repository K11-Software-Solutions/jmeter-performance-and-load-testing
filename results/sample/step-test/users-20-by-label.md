| Label | Samples | Errors | Error % | Avg ms | Min ms | Max ms | p50 ms | p90 ms | p95 ms | p99 ms | Throughput/s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| GET /api/dashboard | 582 | 0 | 0.00 | 73 | 49 | 214 | 70 | 92 | 106 | 156 | 6.65 |
| GET /api/reports/claims-summary | 406 | 0 | 0.00 | 193 | 113 | 422 | 168 | 296 | 341 | 362 | 4.58 |
| GET /api/reports/claims-summary (before export) | 170 | 0 | 0.00 | 194 | 112 | 385 | 162 | 316 | 337 | 360 | 2.00 |
| GET /api/reports/exports/{exportId} | 506 | 0 | 0.00 | 22 | 8 | 169 | 15 | 42 | 61 | 92 | 5.96 |
| GET /api/reports/exports/{exportId}/download | 167 | 0 | 0.00 | 92 | 66 | 219 | 92 | 108 | 128 | 171 | 1.99 |
| POST /api/auth/login | 296 | 0 | 0.00 | 54 | 34 | 199 | 49 | 71 | 93 | 132 | 3.32 |
| POST /api/reports/claims-summary/export | 170 | 0 | 0.00 | 46 | 26 | 171 | 44 | 77 | 94 | 159 | 2.00 |
| TX01_Login | 296 | 0 | 0.00 | 54 | 34 | 199 | 49 | 71 | 93 | 132 | 3.31 |
| TX02_Dashboard | 582 | 0 | 0.00 | 73 | 49 | 214 | 70 | 92 | 106 | 156 | 6.65 |
| TX03_Claims_Summary | 406 | 0 | 0.00 | 193 | 113 | 422 | 168 | 296 | 341 | 362 | 4.58 |
| TX04_Export_Report | 167 | 0 | 0.00 | 398 | 278 | 626 | 386 | 509 | 537 | 605 | 1.99 |
| ALL REQUESTS | 2297 | 0 | 0.00 | 89 | 8 | 422 | 67 | 187 | 254 | 346 | 25.58 |
