# RoadScope Dashboard

This is the Next.js dashboard for visualizing mapped pothole detections from the backend pipeline.

## Requirements

- Node.js 18+
- A Google Maps JavaScript API key

## Setup

```bash
npm install
cp env.local.example .env.local
```

Edit `.env.local` and set:

```bash
NEXT_PUBLIC_GOOGLE_MAPS_KEY=your_google_maps_key
NEXT_PUBLIC_GOOGLE_MAPS_MAP_ID=
```

`NEXT_PUBLIC_GOOGLE_MAPS_MAP_ID` is optional. If provided, the app uses colored advanced markers. Without it, the app falls back to default Google markers.

## Run

```bash
npm run dev
```

Open http://localhost:3000.

## Data Input

The dashboard auto-loads `public/potholes.csv` if present.

You can also upload CSV files manually from the UI. Expected columns include:

- `latitude`
- `longitude`
- `severity` (`Small`, `Medium`, `Large`)
- `confidence` (0-1 or 0-100)
- Optional identifiers/timestamps (`pothole_id`, `frame_id`, `time`, `detection_time`)
