# STRIKEWISE — NIFTY Options Pricing & Quantitative Risk API

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Tests](https://img.shields.io/badge/tests-75%20passed-brightgreen)](#running-tests)
[![Coverage](https://img.shields.io/badge/coverage-89%25-brightgreen)](#running-tests)
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/NandanDivate/STRIKEWISE)

A high-performance quantitative options pricing service and developer library for Indian index options (**NIFTY 50**). Implements European Black-Scholes-Merton with continuous dividend yield, 5 analytical Greeks, and high-precision numerical root-finding using SciPy's Brent method.

> **⚠️ Disclaimer:** All estimates produced by this engine are theoretical, based on the Black-Scholes-Merton model under stated assumptions. They do not constitute financial advice and do not guarantee any executable price or profit.

---

## ⚡ 60-Second Developer Quickstart

STRIKEWISE can be consumed in two ways:
1. **As a Python Library** — Import directly into your trading bots, backtesting scripts, or pandas pipelines (zero HTTP overhead).
2. **As an Asynchronous REST API** — Run locally, in Docker, or on the cloud with interactive OpenAPI docs.

---

### Option 1: Use as a Python Library

#### Installation
```bash
# Direct from GitHub:
pip install git+https://github.com/NandanDivate/STRIKEWISE.git

# Or local editable clone:
git clone https://github.com/NandanDivate/STRIKEWISE.git
cd STRIKEWISE
pip install -e .
```

#### Code Example
```python
import strikewise

# 1. Price a NIFTY 24,500 Call Option (CE)
call_premium = strikewise.call_price(
    spot=24450.0,
    strike=24500.0,
    time_to_expiry_years=0.05,  # ~18 days ACT/365
    risk_free_rate=0.07,        # 7.0% annual rate
    dividend_yield=0.012,       # 1.2% dividend yield
    volatility=0.14,            # 14.0% annualized IV
)
print(f"Call Premium: ₹{call_premium:.2f}")

# 2. Calculate Analytical Greeks
greeks = strikewise.calculate_greeks(
    spot=24450.0,
    strike=24500.0,
    time_to_expiry_years=0.05,
    risk_free_rate=0.07,
    dividend_yield=0.012,
    volatility=0.14,
    option_type="CE",
)
print(f"Delta: {greeks.delta:.4f}")
print(f"Gamma: {greeks.gamma:.6f}")
print(f"Theta/day: ₹{greeks.theta_per_day:.2f}")
print(f"Vega (1% IV move): ₹{greeks.vega:.2f}")
print(f"Rho: ₹{greeks.rho:.2f}")

# 3. Solve for Required Spot Price (Reverse Solver via SciPy Brent)
# "What spot does NIFTY need to hit for this Call to reach ₹250?"
required_spot, status, msg = strikewise.solve_required_spot(
    strike=24500.0,
    time_to_expiry_years=0.05,
    risk_free_rate=0.07,
    dividend_yield=0.012,
    volatility=0.14,
    option_type="CE",
    target_premium=250.0,
)
print(f"Required Spot: ₹{required_spot:.2f} (Status: {status})")
```

---

### Option 2: Use as a REST API

#### Start the Server Locally
```bash
git clone https://github.com/NandanDivate/STRIKEWISE.git
cd STRIKEWISE
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Interactive Swagger UI documentation is available at: **`http://127.0.0.1:8000/docs`**

#### cURL Example: Calculate Option Greeks
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/options/greeks" \
     -H "Content-Type: application/json" \
     -d '{
       "spot_price": 24500.0,
       "strike_price": 24500.0,
       "time_to_expiry_years": 0.05,
       "risk_free_rate": 0.07,
       "dividend_yield": 0.012,
       "volatility": 0.14,
       "option_type": "CE"
     }'
```

#### Python `requests` Example: Scenario & P&L Estimation
```python
import requests

payload = {
    "option_type": "CE",
    "strike_price": 24500.0,
    "expiry_date": "2026-11-20T10:00:00Z",
    "current_spot_price": 24450.0,
    "target_spot_price": 24700.0,
    "current_option_price": 180.0,
    "evaluation_time": "2026-11-15T10:00:00Z",
    "risk_free_rate": 7.0,
    "dividend_yield": 1.2,
    "implied_volatility": 14.0,
    "quantity": 50,
}

response = requests.post("http://127.0.0.1:8000/api/v1/options/estimate", json=payload)
data = response.json()

print(f"Base Estimate: ₹{data['base_estimate']['estimated_premium']:.2f}")
print(f"Projected ROI: {data['base_estimate']['roi_percent']:.2f}%")
print(f"Projected Gross P&L: ₹{data['base_estimate']['gross_pnl']:.2f}")
```

---

## 🚀 One-Click Cloud Deployment (Render)

Deploy this API to **Render** in 2 minutes for free:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/NandanDivate/STRIKEWISE)

1. Click the **Deploy to Render** button above (or create a new **Web Service** on [dashboard.render.com](https://dashboard.render.com) connected to your repository).
2. Render detects [`render.yaml`](render.yaml) automatically.
3. Once deployed, access the interactive Swagger UI at:
   `https://<your-render-subdomain>.onrender.com/docs`

---

## 🐳 Docker Deployment

Run with Docker Compose:
```bash
docker-compose up --build -d
```

Or standalone Docker:
```bash
docker build -t strikewise:latest .
docker run -d -p 8000:8000 --name strikewise strikewise:latest
```

---

## 📊 Core Features

- **Option Premium Estimation**: Estimates theoretical European option premiums at user-defined target spot prices.
- **Analytical Greeks**: Delta, Gamma, Theta (per calendar day), Vega (per 1% IV shift), and Rho with verified units.
- **SciPy Brent Root Solver**: Inverse solver to compute the exact underlying spot price required to reach a target premium with $10^{-8}$ machine precision.
- **Scenario Analysis**: Conservative (-2% IV), Base, and Optimistic (+2% IV) scenario projections with automatic IV lower-bound clamping.
- **Target Price Calculator**: Computes required exit option premium given an entry cost and desired target profit percentage.
- **P&L & ROI Projections**: Computes gross projected profit/loss and return on investment based on trade quantity.
- **ACT/365 Day-Count Convention**: Strict timezone-aware time utilities preventing calendar misalignment.
- **Pluggable Market Data Adapters**: Includes offline manual mode and live DhanHQ API v2 provider adapter.

---

## 🏛️ Architecture & Clean Design

STRIKEWISE follows a clean, layered modular monolith pattern:

```
┌────────────────────────────────────────────────────────┐
│                   API Layer (FastAPI)                  │
│       Input Validation (Pydantic v2) & Error Wrapping  │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                      Service Layer                     │
│    Orchestration: Pricing, Scenarios, P&L, Time Utils  │
└─────────────┬────────────────────────────┬─────────────┘
              │                            │
┌─────────────▼───────────────┐ ┌──────────▼─────────────┐
│       Pricing Engine        │ │  Market Data Provider  │
│ BSM, Greeks, SciPy Brent    │ │ Manual & DhanHQ Adapters│
└─────────────────────────────┘ └────────────────────────┘
```

- **Routes (`app/api/v1/`)**: HTTP schemas and request validation only; no calculations.
- **Services (`app/services/`)**: Orchestration of pricing, time offsets, and scenario comparison.
- **Pricing Engine (`app/pricing/` & `strikewise/`)**: Pure, side-effect-free mathematical functions.
- **Market Data (`app/market_data/`)**: Abstract adapter interface for live and offline feeds.

---

## 🧪 Running Tests

STRIKEWISE has a complete automated test suite with **75 tests** covering mathematical edge cases, root-solving limits, and API integration:

```bash
# Run all tests
pytest tests/ -v

# Run with test coverage report
pytest --cov=app --cov=strikewise --cov-report=term-missing
```

---

## 📐 Mathematical Assumptions

- **Pricing Model**: European Black-Scholes-Merton with continuous dividend yield:
  $$\begin{aligned}
  d_1 &= \frac{\ln(S/K) + (r - q + \frac{1}{2}\sigma^2)T}{\sigma\sqrt{T}} \\
  d_2 &= d_1 - \sigma\sqrt{T} \\
  \text{Call} &= S e^{-qT} N(d_1) - K e^{-rT} N(d_2) \\
  \text{Put} &= K e^{-rT} N(-d_2) - S e^{-qT} N(-d_1)
  \end{aligned}$$
- **Day-Count Convention**: ACT/365 ($T = \text{seconds} / (365 \times 86400)$).
- **Greeks Units**:
  - **Delta**: $\partial V / \partial S$ (unitless).
  - **Gamma**: $\partial^2 V / \partial S^2$ (per spot point).
  - **Theta**: Premium change per calendar day ($\Theta_{\text{annual}} / 365$).
  - **Vega**: Premium change for a 1 percentage point IV shift ($\mathcal{V}_{\text{annual}} \times 0.01$).
  - **Rho**: Premium change for a 1 percentage point interest rate shift ($\rho_{\text{annual}} \times 0.01$).
- **Put Price Ceiling**: Enforces $\lim_{S \to 0} \text{Put}(S) = K e^{-rT}$. Target premiums exceeding this upper bound are flagged as unattainable.

---

## 📄 License

Licensed under the **Apache License, Version 2.0** (the "License"). You may obtain a copy of the License in the [LICENSE](LICENSE) file or at:

http://www.apache.org/licenses/LICENSE-2.0

Copyright (c) 2026 Nandan Divate.
