# Smart Plant Advisor Backend API

Base URL: `http://<host>:8000`

> `/upload_image` requires `python-multipart` installed in the backend environment.

## Plants
### POST /plants
- Body (JSON): `{"nickname": string|null}`
- 200 OK (JSON):
```json
{ "id": 1, "nickname": "Fern", "species": null }
```

### GET /plants
- 200 OK (JSON):
```json
[
  { "id": 1, "nickname": "Fern", "species": null }
]
```

## Sensor & Weight
### POST /sensor
- Body (JSON): `{"plant_id": 1, "temperature": 23.5, "light": 120.0, "soil_moisture": 45.0, "timestamp": "2025-11-22T02:00:00Z"}`
- Validates plant exists; inserts sensor record.
- 200 OK (JSON):
```json
{ "status": "ok", "record_id": 10, "timestamp": "2025-11-22T02:00:00Z" }
```
- 400 if plant not found.

### POST /weight
- Body (JSON): `{"plant_id": 1, "weight": 123.4, "timestamp": "2025-11-22T02:00:00Z"}`
- 200 OK (JSON):
```json
{ "status": "ok", "id": 5 }
```
- 400 if plant not found.

## Images (LLM vision)
### POST /upload_image
- Form-data: `plant_id` (int), `image` (file)
- Uploads the file to Supabase Storage (`plant-images` by default) and stores the public URL.
- 200 OK (JSON):
```json
{
  "status": "ok",
  "plant_id": 1,
  "image_id": 3,
  "file_path": "https://<supabase>/storage/v1/object/public/plant-images/1/<filename>.png",
  "vision_result": { "plant_type": "unknown", "leaf_health": "healthy", "symptoms": [] }
}
```

## Analysis & Reporting
### GET /analysis/{plant_id}
- Aggregates last 7 days sensor averages; returns latest image info and mock growth analysis.
- 200 OK (JSON):
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
- Runs analysis, mock LLM report, stores `AnalysisResult`.
- 200 OK (JSON):
```json
{
  "plant_id": 1,
  "analysis": { ...same fields as /analysis... },
  "report": { "short": "Status: normal...", "long": "This is a mock weekly report..." },
  "analysis_result_id": 7
}
```

## Dream Garden (LLM image generation)
### POST /dreams
- Body (JSON): `{"plant_id": 1, "temperature": 23.5, "light": 120.0, "soil_moisture": 45.0, "health_status": "normal"}`
- Generates a mock dream image, uploads to Supabase Storage (`dream-images` by default), stores the public URL.
- 200 OK (JSON):
```json
{
  "id": 2,
  "plant_id": 1,
  "file_path": "https://<supabase>/storage/v1/object/public/dream-images/1/<filename>.png",
  "info": { "temperature": 23.5, "light": 120.0, "soil_moisture": 45.0, "health_status": "normal" },
  "created_at": "2025-11-22T02:00:00Z"
}
```

### GET /dreams/{plant_id}
- 200 OK (JSON):
```json
[
  {
    "id": 2,
    "plant_id": 1,
    "file_path": "https://<supabase>/storage/v1/object/public/dream-images/1/<filename>.png",
    "info": { "temperature": 23.5, "light": 120.0, "soil_moisture": 45.0, "health_status": "normal" },
    "created_at": "2025-11-22T02:00:00Z"
  }
]
```

## Admin
### GET /admin/stats
- 200 OK (JSON):
```json
{
  "total_plants": 1,
  "total_sensor_records": 10,
  "total_weight_records": 3,
  "total_images": 4,
  "total_analysis_results": 5,
  "sensor_first_timestamp": "2025-11-21T00:00:00Z",
  "sensor_last_timestamp": "2025-11-22T02:00:00Z"
}
```

### GET /metrics/{plant_id}
- 200 OK (JSON):
```json
{
  "temperature": {
    "temp_now": 22.5,
    "temp_6h_avg": 21.9,
    "temp_24h_min": 20.1,
    "temp_24h_max": 24.3
  },
  "soil_moisture": {
    "soil_now": 120,
    "soil_24h_min": 90,
    "soil_24h_max": 180,
    "soil_24h_trend": 15
  },
  "light": {
    "light_now": 300,
    "light_1h_avg": 250,
    "light_today_sum": 35.5
  },
  "weight": {
    "weight_now": 123.4,
    "weight_24h_diff": -1.2,
    "water_loss_per_hour": -0.05,
    "hours_since_last_watering": 6.5,
    "weight_drop_since_last_watering": -1.0
  }
}
```

## Health
### GET /
- 200 OK (JSON): `{ "status": "backend ok", "db": "connected" }`
