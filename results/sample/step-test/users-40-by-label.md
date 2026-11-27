| Label | Samples | Errors | Error % | Avg ms | Min ms | Max ms | p50 ms | p90 ms | p95 ms | p99 ms | Throughput/s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| GET /api/dashboard | 1013 | 0 | 0.00 | 185 | 51 | 499 | 169 | 324 | 360 | 439 | 11.43 |
| GET /api/reports/claims-summary | 726 | 0 | 0.00 | 308 | 111 | 669 | 294 | 472 | 511 | 637 | 8.17 |
| GET /api/reports/claims-summary (before export) | 286 | 0 | 0.00 | 302 | 115 | 711 | 292 | 463 | 529 | 661 | 3.25 |
| GET /api/reports/exports/{exportId} | 815 | 0 | 0.00 | 134 | 10 | 507 | 115 | 266 | 320 | 404 | 9.39 |
| GET /api/reports/exports/{exportId}/download | 280 | 0 | 0.00 | 198 | 68 | 543 | 173 | 341 | 403 | 511 | 3.26 |
| POST /api/auth/login | 523 | 0 | 0.00 | 163 | 34 | 443 | 150 | 295 | 329 | 431 | 5.82 |
| POST /api/reports/claims-summary/export | 282 | 0 | 0.00 | 166 | 29 | 496 | 152 | 315 | 373 | 451 | 3.23 |
| TX01_Login | 523 | 0 | 0.00 | 163 | 34 | 443 | 150 | 295 | 329 | 431 | 5.81 |
| TX02_Dashboard | 1013 | 0 | 0.00 | 185 | 51 | 499 | 169 | 324 | 360 | 439 | 11.43 |
| TX03_Claims_Summary | 726 | 0 | 0.00 | 308 | 111 | 669 | 294 | 472 | 511 | 637 | 8.17 |
| TX04_Export_Report | 280 | 0 | 0.00 | 1053 | 278 | 1870 | 1091 | 1427 | 1610 | 1798 | 3.23 |
| ALL REQUESTS | 3925 | 0 | 0.00 | 202 | 10 | 711 | 183 | 369 | 431 | 543 | 43.55 |
