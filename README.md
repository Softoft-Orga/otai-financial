# OTAI Financial Simulation Dashboard

A comprehensive financial forecasting dashboard for OTAI, built with Python and Streamlit.

## Features

- Interactive parameter adjustment via sidebar sliders
- Real-time simulation running
- KPI metrics display
- Interactive charts for cash, revenue, users, and leads
- Detailed data tables
- Excel export functionality

## Quick Start

### Using Streamlit Dashboard (Recommended)

1. Install dependencies:
   ```bash
   uv sync
   ```

2. Run the dashboard:
   ```bash
   uv run streamlit run streamlit_app.py
   ```

3. Open your browser and navigate to `http://localhost:8501`

### Using Command Line

Run the basic simulation without the dashboard:
```bash
uv run python -m otai_forecast.run
```

This will generate Excel files with the simulation results and display plots.

## Dashboard Components

### Sidebar Parameters
- **Basic Settings**: Simulation period, costs, starting cash
- **Marketing**: Ad/SEO spend settings and growth rates
- **Pricing**: Pro and Enterprise subscription prices
- **Development**: Team capacity and maintenance requirements
- **Conversion Rates**: Funnel conversion percentages
- **Churn Rates**: Customer churn by tier

### Main View
- **KPIs**: End cash, minimum cash, final user counts, total revenue
- **Charts**:
  - Cash position over time
  - Monthly revenue
  - User growth by tier
  - Leads and website traffic
- **Tables**:
  - Monthly overview summary
  - Detailed finance breakdown
- **Export**: Download results as Excel files

## Optimization

The dashboard includes a simple optimization feature that automatically finds the best policy parameters:

### How it Works
- Uses **Random Search** to try different parameter combinations
- Objective: **Maximize Final Market Cap** while ensuring cash never goes negative
- Market Cap = (Monthly Revenue × 12 × Valuation Multiple) + Cash
- If a parameter set results in negative cash at any point, it's discarded

### Using the Optimizer
1. Scroll to the "Parameter Optimization" section
2. Set the number of iterations (more = better but slower)
3. Click "Run Optimization"
4. View the best parameters and market cap achieved

### Command Line Optimization
You can also run optimizations from the command line:
```bash
uv run python optimize_example.py
```

This will run optimization with visualizations showing the relationship between parameters and market cap.

## Running Tests

Run the test suite:
```bash
uv run python -m unittest discover tests -v
```

## Project Structure

```
otai_financials/
├── otai_forecast/
│   ├── models.py        # Data models and validation
│   ├── compute.py       # Core calculation logic
│   ├── simulator.py     # Simulation engine
│   ├── effects.py       # Feature effects system
│   ├── export.py        # Excel export utilities
│   ├── optimize.py      # Parameter optimization algorithms
│   ├── run.py          # CLI runner
│   └── dashboard.py    # Streamlit dashboard
├── tests/              # Unit tests
├── streamlit_app.py    # Streamlit entry point
├── optimize_example.py # Command-line optimization example
├── main.py            # Entry point
└── README.md
```

## Assumptions

The simulation models a SaaS business with:
- Three user tiers: Free, Pro, and Enterprise
- Marketing channels: Ads, SEO, and Social Media
- Product development roadmap with feature launches
- Partner channel for enterprise sales
- One-time license fee model (no recurring revenue)
