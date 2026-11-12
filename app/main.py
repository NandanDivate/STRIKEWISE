"""NIFTY Options Pricing API — FastAPI application entry point.

A quantitative options pricing service that estimates theoretical premiums
for NIFTY options using the Black-Scholes-Merton model.
"""

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.core.errors import register_exception_handlers

API_DESCRIPTION = """
### Quantitative Options Pricing & Risk Engine for NIFTY 50

A production-grade options pricing service and quantitative risk engine implementing the European Black-Scholes-Merton model with continuous dividend yield, 5 analytical Greeks, and high-precision SciPy Brent root-finding.

---

### Author & Developer Information
- **Developer:** **Nandan Divate**
- **GitHub Profile:** [github.com/NandanDivate](https://github.com/NandanDivate)
- **Project Repository:** [STRIKEWISE on GitHub](https://github.com/NandanDivate/STRIKEWISE)
- **LinkedIn Profile:** [Nandan Divate on LinkedIn](https://www.linkedin.com/in/nandandivate)

---

### Core Capabilities
- **Black-Scholes-Merton Pricing:** Continuous dividend yield with strict ACT/365 day-count convention.
- **Analytical Greeks:** Real-time Delta, Gamma, Theta (per-day), Vega (1% IV shift), and Rho.
- **Reverse Spot Solver:** SciPy Brent method (`brentq`) with machine precision ($10^{-8}$ tolerance).
- **Scenario Analysis:** Conservative, Base, and Optimistic IV projections with lower-bound clamping.
- **Dual-Mode Consumption:** Run as an asynchronous REST API or import directly via `import strikewise`.

---

> **Disclaimer:** All estimates produced by this API are theoretical, based on the Black-Scholes-Merton model under stated assumptions. They do not constitute financial advice and do not guarantee any executable price or profit.
"""

app = FastAPI(
    title="STRIKEWISE — NIFTY Options Pricing API",
    description=API_DESCRIPTION,
    version="0.1.0",
    contact={
        "name": "Nandan Divate",
        "url": "https://github.com/NandanDivate",
        "email": "nandan.divate25@gmail.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)

# CORS middleware — restricted origins from settings, not wildcard
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Register custom exception handlers
register_exception_handlers(app)

# Include API v1 router
app.include_router(v1_router, prefix="/api/v1")


@app.get(
    "/health",
    summary="Root Health Check",
    description="Returns service status and version at the root level.",
    tags=["Health"],
)
async def root_health() -> dict:
    """Root-level health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "service": "NIFTY Options Pricing API",
    }

