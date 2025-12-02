# Smart Plant Advisor Backend API (snapshot)

Base URL: `http://<host>:8000`

> `/upload_image` requires `python-multipart` installed.

## Plants
### POST /plants
- Body: `{"nickname": string|null}`
- 200:
```json
{ "id": 1, "nickname": "Fern", "species": null }
```

### GET /plants
- List all plants.

### GET /plants/by-nickname/{nickname}
- Returns plant by nickname if exists.

### GET /plants/by-status
- Query param: `status` (e.g., `normal`, `stressed`, `slow`, `stagnant`).
- Returns plants whose latest AnalysisResult has the status.

## Raw data
### GET /plants/{id}/raw-data
- Query: `sensor_type` (temperature|light|soil_moisture|weight), `page` (default 1), `page_size` (default 25)
- Returns recent records (paged), including timestamp and value.

### GET /plants/{id}/raw-data/export
- Query: `sensor_type`, `date` or `start_time`/`end_time`
- Response: `text/csv` with columns `time,sensor_type,value,unit`

## Sensor & Weight ingest
### POST /sensor
- Body:
```json
{ "plant_id": 1, "temperature": 23.5, "light": 120.0, "soil_moisture": 45.0, "timestamp": "2025-11-22T02:00:00Z" }
```
- Validates plant exists; inserts sensor record.
- 200: `{"status": "ok", "record_id": 10, "timestamp": "2025-11-22T02:00:00Z"}`

### POST /weight
- Body: `{"plant_id": 1, "weight": 123.4, "timestamp": "2025-11-22T02:00:00Z"}`
- 200: `{"status": "ok", "id": 5}`

## Images
### POST /upload_image
- Multipart form: `plant_id` (int), `image` (file)
- Uploads to Supabase Storage (`plant-images` by default) and stores public URL.
- 200:
```json
{
  "status": "ok",
  "plant_id": 1,
  "image_id": 3,
  "file_path": "https://<supabase>/storage/v1/object/public/plant-images/1/<filename>.jpg"
}
```

## Analysis & Reporting
### GET /analysis/{plant_id}
- Aggregates last 7 days sensor averages; returns latest image info and growth analysis.
- 200:
```json
{
  "plant_id": 1,
  "growth_status": "normal",
  "growth_rate_3d": 3.2,
  "sensor_summary_7d": {
    "avg_temperature": 23.5,
    "avg_light": 120.0,
    "avg_soil_moisture": 45.0
  },
  "stress_factors": []
}
```

### GET /report/{plant_id}
- Runs analysis, calls LLM, stores AnalysisResult with text fields.
- 200:
```json
{
  "plant_id": 1,
  "analysis": { "...": "..." },
  "report": {
    "growth_overview": "...",
    "environment_assessment": "...",
    "suggestions": "...",
    "full_analysis": "...",
    "trigger": "manual"
  },
  "analysis_result_id": 7
}
```

### POST /watering-trigger/{plant_id}
- Triggers LLM report + dream generation for a watering event (uses latest sensor/weight/image; sets `trigger="watering"`).
- 200: `{"status": "ok"}`

### GET /reports/{plant_id}
- Query `limit` (default 20). Lists recent AnalysisResult rows.

## Dream Garden
### POST /dreams
- Body: `{"plant_id": 1}`
- Backend pulls latest sensor/weight rows and latest analysis for `health_status`, calls CN dream workflow, re-uploads Coze image to Supabase (`dream-images`), stores public URL and description.
- 200:
```json
{
  "id": 2,
  "plant_id": 1,
  "file_path": "https://<supabase>/storage/v1/object/public/dream-images/1/<timestamp>.png",
  "description": "dream description or null",
  "created_at": "2025-11-22T02:00:00Z",
  "environment": {
    "temperature": 23.5,
    "light": 120.0,
    "moisture": 55.1,
    "weight": 470.3
  }
}
```

### GET /dreams/{plant_id}
- Lists dream images for a plant (includes environment block and description).

## Metrics (soil moisture returned as %)
### GET /metrics/{plant_id}
- Returns live metrics (now/averages/trends) for temp, soil, light, weight.

### GET /plants/{plant_id}/latest-summary
- Returns latest sensor snapshot and latest suggestions:
```json
{
  "plant_id": 1,
  "sensors": {
    "temperature": { "value": 23.5, "timestamp": "2025-11-22T02:00:00Z" },
    "light": { "value": 120.0, "timestamp": "2025-11-22T02:00:00Z" },
    "soil_moisture": { "value": 55.1, "timestamp": "2025-11-22T02:00:00Z" },
    "weight": { "value": 470.3, "timestamp": "2025-11-22T02:00:00Z" }
  },
  "suggestions": "text or null"
}
```

### GET /metrics/{plant_id}/daily-7d
- Returns daily aggregates for the last 7 days (temperature, soil_moisture %, light, weight).

### GET /metrics/{plant_id}/hourly-24h
- Returns hourly aggregates for the last 24 hours (temperature, soil_moisture %, light, weight).

## Growth Analytics
### GET /plants/{plant_id}/growth-analytics
- Query: `days` (default 7)
- Returns daily reference weight (algorithm), actual weight averages, growth_rate_3d series, stress scores.
```json
{
  "plant_id": 1,
  "days": 7,
  "daily_weight": [
    { "date": "2025-11-22", "actual_weight": 468.5, "reference_weight": 470.0 }
  ],
  "growth_rate_3d": [
    { "date": "2025-11-22", "growth_rate_pct": 2.0 }
  ],
  "stress_scores": { "temperature": 1.2, "humidity": 3.5, "light": 2.1, "growth": 0.8 }
}
```

## Alerts
### GET /alerts?limit=20
- Query params: `limit` (default 20), optional `plant_id`, `analysis_result_id`.
- Returns recent alerts (message + created_at).

### POST /alerts
- Body: `{"message": "string", "plant_id": int|null, "analysis_result_id": int|null}`

### DELETE /alerts/{id}

## Scheduler
### GET /scheduler/jobs
- Returns registered jobs with status and next run.
### POST /scheduler/jobs/{id}/pause
### POST /scheduler/jobs/{id}/resume
### POST /scheduler/jobs/{id}/run-now
- Manual runs are logged to `scheduler_job_runs`.
### GET /scheduler/logs
- Optional `limit` (default 50). Each item:
```json
{
  "id": 1,
  "jobKey": "daily_analysis",
  "jobName": "每日植物分析",
  "status": "success",
  "message": "Daily analysis completed",
  "startedAt": "2024-11-28T08:00:00Z",
  "finishedAt": "2024-11-28T08:02:15Z",
  "durationSeconds": 135
}
```

## System / Admin
### GET /admin/stats
- Counts: plants, sensor_records, weight_records, images, analysis_results, timestamps of first/last sensor data.

### GET /system/overview
- Counts across plants/images/sensor/analysis/dreams.

### GET /dashboard/system-overview
- Summary for dashboard (abnormal_plants = latest analysis per plant with growth_status == 'stressed'):
```json
{ "total_plants": 4, "active_last_24h": 3, "abnormal_plants": 1, "dreams_generated_today": 8 }
```

## Health
### GET /
- `{"status": "backend ok", "db": "connected"}`
