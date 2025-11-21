# Smart Plant Advisor Backend API

Base URL: `http://<host>:8000`

> Note: `/upload_image` requires `python-multipart` installed in the backend environment.

## Plants
- `POST /plants`
  - Body: `{ "nickname": string|null }`
  - Creates a plant; returns plant `id`, `nickname`, `species`.

- `GET /plants`
  - Lists all plants.

## Sensor & Weight
- `POST /sensor`
  - Body: `{ "plant_id": int, "temperature"?: float, "light"?: float, "soil_moisture"?: float, "timestamp"?: ISO8601 }`
  - Validates plant exists; inserts sensor record.

- `POST /weight`
  - Body: `{ "plant_id": int, "weight": float, "timestamp"?: ISO8601 }`
  - Validates plant exists; inserts weight record.

## Images (LLM vision)
- `POST /upload_image`
  - Form-data: `plant_id` (int), `image` (file)
  - Stores file, runs LLM vision stub, records `plant_type`, `leaf_health`, `symptoms`.

## Analysis & Reporting
- `GET /analysis/{plant_id}`
  - Aggregates last 7 days sensor averages; returns latest image info and mock growth analysis.

- `GET /report/{plant_id}`
  - Runs analysis, mock LLM report, stores `AnalysisResult`; returns analysis payload plus short/long report.

## Dream Garden (LLM image generation)
- `POST /dreams`
  - Body: `{ "plant_id": int, "temperature"?: float, "light"?: float, "soil_moisture"?: float, "health_status"?: string }`
  - Creates a dream image using LLM stub; stores path, prompt, info.

- `GET /dreams/{plant_id}`
  - Lists dream images for the plant (most recent first).

## Admin
- `GET /admin/stats`
  - Returns counts of plants, sensor/weight/images/analysis records and first/last sensor timestamps.

## Health
- `GET /`
  - Returns `{ "status": "backend ok", "db": "connected" }`.
