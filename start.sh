#!/bin/bash
set -e

echo "Starting application..."

# Optionally download GTFS data if AUTO_DOWNLOAD_GTFS is set
if [ "$AUTO_DOWNLOAD_GTFS" = "true" ]; then
    echo "Auto-downloading GTFS data..."
    python scripts/download_gtfs.py || echo "Warning: GTFS download failed, continuing..."
fi

# Optionally populate database if AUTO_POPULATE_DB is set
if [ "$AUTO_POPULATE_DB" = "true" ]; then
    echo "Auto-populating database..."
    python scripts/populate_stcp.py || echo "Warning: Database population failed, continuing to start server..."
else
    echo "Skipping database population (set AUTO_POPULATE_DB=true to enable)"
fi

# Start the API server
echo "Starting API server..."
exec python run.py
