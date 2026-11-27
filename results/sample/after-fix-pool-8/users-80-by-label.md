| Label | Samples | Errors | Error % | Avg ms | Min ms | Max ms | p50 ms | p90 ms | p95 ms | p99 ms | Throughput/s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| GET /api/dashboard | 2118 | 0 | 0.00 | 168 | 49 | 387 | 166 | 262 | 294 | 347 | 23.91 |
| GET /api/reports/claims-summary | 1406 | 0 | 0.00 | 290 | 110 | 613 | 280 | 420 | 465 | 532 | 15.86 |
| GET /api/reports/claims-summary (before export) | 598 | 0 | 0.00 | 288 | 109 | 611 | 280 | 418 | 459 | 531 | 6.80 |
| GET /api/reports/exports/{exportId} | 1724 | 0 | 0.00 | 121 | 9 | 333 | 120 | 215 | 246 | 294 | 19.84 |
| GET /api/reports/exports/{exportId}/download | 569 | 0 | 0.00 | 182 | 66 | 393 | 181 | 267 | 295 | 359 | 6.63 |
| POST /api/auth/login | 1063 | 0 | 0.00 | 148 | 32 | 375 | 146 | 248 | 277 | 324 | 11.83 |
| POST /api/reports/claims-summary/export | 593 | 0 | 0.00 | 145 | 27 | 342 | 144 | 238 | 269 | 326 | 6.77 |
| TX01_Login | 1063 | 0 | 0.00 | 148 | 32 | 375 | 146 | 248 | 277 | 324 | 11.79 |
| TX02_Dashboard | 2118 | 0 | 0.00 | 168 | 49 | 387 | 166 | 262 | 294 | 347 | 23.91 |
| TX03_Claims_Summary | 1406 | 0 | 0.00 | 290 | 110 | 613 | 280 | 420 | 465 | 532 | 15.86 |
| TX04_Export_Report | 569 | 0 | 0.00 | 970 | 279 | 1657 | 980 | 1313 | 1407 | 1494 | 6.59 |
| ALL REQUESTS | 8071 | 0 | 0.00 | 185 | 9 | 613 | 173 | 317 | 372 | 474 | 89.66 |
