# Porto Transport API

Unofficial REST API for public transport data for the city of Porto, Portugal. This API provides access to STCP (Sociedade de Transportes Colectivos do Porto) transit data including information regarding: routes, stops, trips, bus gps positions as well as scheduled and real-time arrival time.


The aim of this API is to provide better usability and more data than the source information. While this API uses STCP data as its foundation, some data is calculated or derived from processing the source data rather than being directly provided by STCP. See the [Data Processing](#data-processing) section for details.


## Table of Contents

- [Features](#features)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Setup](#setup)
- [Data Setup](#data-setup)
  - [Download GTFS Data](#download-gtfs-data)
  - [Populate Database](#populate-database)
- [Running the API](#running-the-api)
  - [Development Server](#development-server)
- [API Documentation](#api-documentation)
- [API Endpoints](#api-endpoints)
  - [Stops](#stops)
  - [Routes](#routes)
  - [Trips](#trips)
  - [Buses](#buses)
  - [Service Days](#service-days)
- [Response Format](#response-format)
  - [Single Item Response](#single-item-response)
  - [Paginated Response](#paginated-response)
- [Background Tasks](#background-tasks)
- [Technologies](#technologies)
- [Data Sources](#data-sources)
- [Data Processing](#data-processing)
  - [Calculated/Derived Data](#calculatedderived-data)
  - [Direct STCP Data](#direct-stcp-data)
- [Acknowledgments](#acknowledgments)

## Features

- **GTFS Data Integration**: Loads and normalizes GTFS (General Transit Feed Specification) data from STCP
- **Real-time Bus Tracking**: Fetches real-time bus positions from FIWARE platform
- **RESTful API**: Standard REST API with pagination and structured responses.
- **Scheduled Arrivals**: Scheduled arrivals for all stops with filtering by lines and other parameters.
- **Real-time Arrivals**: Real-time arrival information fetched on-demand from STCP API (with some calculated fields)
- **Route Information**: Access route details, shapes, and stops grouped by direction
- **Trip Information**: Get trip details, shapes, and stops
- **Service Days**: Query service day information
- **Standardized Responses**: Consistent response format across all endpoints with timestamps and links

## Installation

### Prerequisites

- Python 3.9 or higher
- pip

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd porto-transport-api
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Data Setup

### Download GTFS Data

Download the latest STCP GTFS feed:
```bash
python scripts/download_gtfs.py
```

This will download the GTFS files to `data/raw/stcp/`.

### Populate Database

Load GTFS data into the database:
```bash
python scripts/populate_stcp.py
```

This script will populate the database with:
1. Agencies/Service Providers
2. Stops
3. Service days
4. Routes
5. Trips
6. Shapes
7. Trip shapes
8. Route shapes
9. Route stops
10. Trip stops
11. Scheduled arrivals


## Running the API

### Development Server

Usingthe provided run script:
```bash
python run.py
```

Using FastAPI CLI:
```bash
fastapi dev app/main.py
```

Using uvicorn :
```bash
uvicorn app.main:app --reload
```


## API Documentation

Once the server is running, interactive API documentation is available at:
- **Swagger UI**: `http://localhost:8000/docs`

## API Endpoints

### Stops

- `GET /api/v1/stcp/stops` - List all stops (paginated, filterable by zone_id)
- `GET /api/v1/stcp/stops/{stop_id}` - Get stop details
- `GET /api/v1/stcp/stops/{stop_id}/scheduled` - Get scheduled arrivals for a stop (paginated, filterable by route_id and service_id)
- `GET /api/v1/stcp/stops/{stop_id}/realtime` - Get real-time arrivals for a stop (fetched on-demand from STCP API, with calculated fields)

### Routes

- `GET /api/v1/stcp/routes` - List all routes (paginated)
- `GET /api/v1/stcp/routes/{route_id}` - Get route details
- `GET /api/v1/stcp/routes/{route_id}/shapes` - Get route shapes (calculated from trip shapes)
- `GET /api/v1/stcp/routes/{route_id}/stops` - Get route stops grouped by direction

### Trips

- `GET /api/v1/stcp/trips` - List all trips (filterable by route_id, service_id, direction_id, etc)
- `GET /api/v1/stcp/trips/{trip_id}` - Get trip details
- `GET /api/v1/stcp/trips/{trip_id}/shapes` - Get trip shapes (derived from GTFS shapes data)
- `GET /api/v1/stcp/trips/{trip_id}/stops` - Get trip stops

### Buses

- `GET /api/v1/stcp/buses` - List all buses (filterable by route_id and direction_id)
- `GET /api/v1/stcp/buses/{vehicle_id}` - Get bus details

### Service Days

- `GET /api/v1/stcp/service-days` - List all service days
- `GET /api/v1/stcp/service-days/{id}` - Get service day by ID (service_id) or type (service_type)

## Response Format

All API responses follow a standardized format:

### Single Item Response
```json
{
  "data": {
    "id": "...",
    ...
  },
  "timestamp": "",
  "links": {
    "self": "/api/v1/endpoint",
    "related": {
      ...
    }
  }
}
```

### Paginated Response
```json
{
  "data": [...],
  "page": {
    "size": ,
    "totalElements": ,
    "totalPages": ,
    "number": 
  },
  "links": {
    "self": "...",
    "first": "...",
    "next": "...",
    "prev": "...",
    "last": "..."
  },
  "timestamp": ""
}
```

## Background Tasks

The API runs a background task that updates bus positions every 15 seconds (this value can be changed in the .env) from STCP. Bus data is stored in the database and updated periodically.

**Note**: Real-time arrivals are fetched on-demand from the STCP API and are not stored in the database.

## Technologies

- **FastAPI**: Modern, fast web framework for building APIs with Python
- **Pydantic**: Data validation and serialization using Python type annotations
- **SQLite**: Lightweight database storage
- **httpx**: Async HTTP client for external API calls
- **Python-dotenv**: Environment variable management

## Data Sources

- [**GTFS Feed**](https://opendata.porto.digital/dataset/horarios-paragens-e-rotas-em-formato-gtfs-stcp): STCP static transit data (routes, stops, schedules)
- [**FIWARE**](https://broker.fiware.urbanplatform.portodigital.pt/v2/): Real-time bus position data
- [**STCP API**](https://stcp.pt/api/): Real-time arrival information

All of the source data from STCP is available under a Creative Commons Zero (CC0) license.

## Data Processing

While this API uses STCP data as its foundation, some data is calculated or derived rather than being directly provided by STCP:

### Calculated/Derived Data

1. **Trip Shapes**: Trip shapes are derived from GTFS `shapes.txt` data by linking trips to their corresponding shape IDs. The shape points are then assembled and ordered by sequence to form the complete trip path.

2. **Route Shapes**: Route shapes are calculated by aggregating trip shapes. The system identifies all trips for a given route and direction, then extracts the associated shape from the GTFS data. This allows routes to have shape representations even when not explicitly defined in the GTFS feed.

3. **Real-time Arrival Fields**: Some fields in real-time arrival responses are calculated or matched rather than coming directly from the STCP API:
   - **`stop_sequence`**: Not provided by the STCP API. Calculated by matching the real-time arrival with scheduled arrivals from the GTFS data, finding the closest scheduled arrival time within a 60-second tolerance.
   - **`trip_number`**: Not provided by the STCP API. Derived by matching the real-time arrival with scheduled trip data to identify the corresponding trip number.

4. **Scheduled Arrivals**: While based on GTFS `stop_times.txt` data, scheduled arrivals are calculated by combining stop times with trip information (route, direction, service day) to provide a complete arrival context.

### Direct STCP Data

The following data comes directly from STCP sources without calculation:
- Stops (from GTFS)
- Routes (from GTFS)
- Trips (from GTFS)
- Service days (from GTFS)
- Bus positions (from FIWARE platform)
- Real-time arrival times and basic trip information (from STCP API)

## Acknowledgments

- STCP (Sociedade de Transportes Colectivos do Porto) for providing the bus transit data
