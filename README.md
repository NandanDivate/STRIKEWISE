# NIFTY Options Pricing API

A quantitative options pricing service that estimates theoretical premiums for NIFTY CE/PE options using the Black-Scholes-Merton model.

> **⚠️ Disclaimer:** All estimates produced by this API are theoretical, based on the Black-Scholes-Merton model under stated assumptions. They do not constitute financial advice and do not guarantee any executable price or profit. Actual option prices may differ due to changes in implied volatility, liquidity, bid-ask spread, market conditions, and other factors.

## Features

- **Option Premium Estimation**: Estimate the theoretical premium of a selected NIFTY option at a user-defined target spot price
- **IV Scenario Analysis**: Conservative, base, and optimistic premium estimates with configurable IV shifts
- **Greeks Calculation**: Delta, Gamma, Theta, Vega, and Rho with documented units
- **Reverse Solver**: Find the required underlying spot for an option to reach a target premium
- **Target Price Calculator**: Calculate the exit premium needed for a desired profit percentage
- **Time Decay Comparison**: Model the effect of time passage on option premium
- **Gross P&L & ROI**: Projected gross profit/loss and return on investment
- **Manual Input Mode**: Works fully without external credentials or market data feeds
- **Replaceable Market Data**: Provider interface for future live data integration

## Non-Features (Explicitly Out of Scope)

- No frontend, dashboard, or charts
- No user accounts, authentication, or subscriptions
- No order placement or automated trading
- No trade recommendations or strike scanning
- No machine learning or price prediction
- No claims of guaranteed prices or profits

## Tech Stack

- **Python 3.11+**
- **FastAPI** — async web framework with automatic OpenAPI docs
- **Pydantic v2** — request/response validation
- **NumPy** — numerical computing
- **SciPy** — statistical distributions and numerical solvers
- **Pytest** — testing framework
- **Docker** — containerization

## Architecture

The API follows a layered modular monolith architecture:

```
API Layer (FastAPI routes) → Service Layer → Pricing Engine
                                          → Market Data Provider
```

- **Routes** validate input and return responses (no calculations)
- **Services** orchestrate pricing, scenarios, and P&L computation
- **Pricing engine** implements BSM, Greeks, solver, scenarios
- **Market data** uses a replaceable provider interface

See [docs/architecture.md](docs/architecture.md) for details.

## Setup

### Prerequisites

- Python 3.11 or newer
- pip

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd STRIKEWISE

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Available variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | NIFTY Options Pricing API | Application name |
| `DEBUG` | false | Debug mode |
| `CORS_ORIGINS` | [] | Allowed CORS origins (JSON list) |

## Running Locally

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

## Running with Docker

```bash
# Build and run
docker-compose up --build

# Or using Docker directly
docker build -t nifty-options-api .
docker run -p 8000:8000 --env-file .env nifty-options-api
```

## API Documentation

Once running, interactive documentation is available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## API Endpoints

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| GET | `/health` | Root health check | ✅ Implemented |
| GET | `/api/v1/health` | API v1 health check with timestamp | ✅ Implemented |
| POST | `/api/v1/options/estimate` | Estimate option premium at target spot | ✅ Implemented |
| POST | `/api/v1/options/target-price` | Calculate required exit premium | ✅ Implemented |
| POST | `/api/v1/options/required-spot` | Reverse-solve required spot | ✅ Implemented |
| POST | `/api/v1/options/greeks` | Calculate option Greeks | ✅ Implemented |

## Example Request

```bash
curl -X GET http://localhost:8000/health
```

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "service": "NIFTY Options Pricing API"
}
```

See [docs/api_examples.md](docs/api_examples.md) for examples of all endpoints.

## Documentation

- **[Beginner's Guide (Days 1–2 Walkthrough)](docs/day_1_2_guide.md)** — Project foundation, architecture, Pydantic schemas, and error handling
- **[Beginner's Guide (Days 3–4 Walkthrough)](docs/day_3_4_guide.md)** — Black-Scholes-Merton math, dividend yield, ACT/365 time utils, and mathematical unit tests
- **[Beginner's Guide (Days 5–6 Walkthrough)](docs/day_5_6_guide.md)** — Core estimation service, analytical Greeks, IV scenario analysis, and gross P&L computation
- **[Beginner's Guide (Days 7–8 Walkthrough)](docs/day_7_8_guide.md)** — Live HTTP API endpoints, reverse spot solving via Brent's method, and integration tests
- **[Architecture Overview](docs/architecture.md)** — System architecture, layering, and data flow
- **[Mathematical Assumptions](docs/assumptions.md)** — BSM model, continuous dividend yield, ACT/365, Greek units
- **[API Examples](docs/api_examples.md)** — Sample cURL requests and JSON responses

## Running Tests

```bash
pytest tests/ -v
```

## Mathematical Assumptions

- **Model**: Black-Scholes-Merton with continuous dividend yield
- **Option style**: European (appropriate for NIFTY options)
- **Day-count convention**: ACT/365
- **Rates**: Continuously compounded (annual percentage in API, decimal internally)
- **IV scenarios**: Absolute percentage-point shifts (not relative)
- **P&L**: Gross only — excludes brokerage, taxes, STT, GST, slippage
- **Quantity**: In option units, not lots (lot size is not hard-coded)

See [docs/assumptions.md](docs/assumptions.md) for the complete list.

## Known Limitations

1. **Theoretical estimates only** — BSM prices can differ significantly from market prices
2. **Constant IV assumption** — real IV changes continuously
3. **European exercise only** — appropriate for NIFTY but not for all markets
4. **Calendar time** — uses calendar days, not trading days
5. **No live data** — manual input mode only in the MVP
6. **Gross figures** — all P&L excludes transaction costs

## Project Structure

```
├── app/
│   ├── main.py                 # FastAPI application
│   ├── api/v1/                 # API endpoints
│   ├── core/                   # Config and error handling
│   ├── pricing/                # BSM engine, Greeks, solver
│   ├── market_data/            # Data provider interface
│   ├── schemas/                # Request/response models
│   └── services/               # Business logic
├── tests/
│   ├── unit/                   # Math unit tests
│   └── integration/            # API tests
├── docs/                       # Documentation
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## License

Private — all rights reserved.

