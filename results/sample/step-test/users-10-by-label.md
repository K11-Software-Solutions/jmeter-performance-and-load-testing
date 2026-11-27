| Label | Samples | Errors | Error % | Avg ms | Min ms | Max ms | p50 ms | p90 ms | p95 ms | p99 ms | Throughput/s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| GET /api/dashboard | 290 | 0 | 0.00 | 68 | 49 | 93 | 68 | 79 | 81 | 87 | 3.29 |
| GET /api/reports/claims-summary | 192 | 0 | 0.00 | 188 | 111 | 360 | 165 | 294 | 326 | 356 | 2.22 |
| GET /api/reports/claims-summary (before export) | 95 | 0 | 0.00 | 183 | 123 | 365 | 159 | 292 | 325 | 365 | 1.16 |
| GET /api/reports/exports/{exportId} | 282 | 0 | 0.00 | 17 | 10 | 45 | 15 | 26 | 27 | 31 | 3.43 |
| GET /api/reports/exports/{exportId}/download | 93 | 0 | 0.00 | 90 | 70 | 109 | 92 | 107 | 108 | 109 | 1.15 |
| POST /api/auth/login | 149 | 0 | 0.00 | 49 | 34 | 126 | 48 | 58 | 60 | 62 | 1.66 |
| POST /api/reports/claims-summary/export | 95 | 0 | 0.00 | 38 | 25 | 47 | 37 | 46 | 47 | 47 | 1.16 |
| TX01_Login | 149 | 0 | 0.00 | 49 | 34 | 126 | 48 | 58 | 60 | 62 | 1.66 |
| TX02_Dashboard | 290 | 0 | 0.00 | 68 | 49 | 93 | 68 | 79 | 81 | 87 | 3.29 |
| TX03_Claims_Summary | 192 | 0 | 0.00 | 188 | 111 | 360 | 165 | 294 | 326 | 356 | 2.22 |
| TX04_Export_Report | 93 | 0 | 0.00 | 363 | 278 | 553 | 340 | 472 | 505 | 553 | 1.14 |
| ALL REQUESTS | 1196 | 0 | 0.00 | 81 | 10 | 365 | 62 | 171 | 223 | 339 | 13.28 |
