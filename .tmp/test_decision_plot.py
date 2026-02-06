import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
from otai_forecast.plots import plot_decision_attributes

# Create test data with decision attributes
test_df = pd.DataFrame({
    'month': range(12),
    'ads_budget': [1000, 1200, 1500, 1800, 2000, 2200, 2500, 2800, 3000, 3200, 3500, 4000],
    'seo_budget': [500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1600],
    'dev_budget': [5000, 5000, 5500, 6000, 6500, 7000, 7500, 8000, 8500, 9000, 9500, 10000],
    'outreach_budget': [1000, 1000, 1200, 1400, 1600, 1800, 2000, 2200, 2400, 2600, 2800, 3000],
    'partner_budget': [500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1600],
    'pro_price_override': [None] * 6 + [5000] * 6,  # Override price in second half
    'ent_price_override': [None] * 12,  # No enterprise override
})

# Create the plot
fig = plot_decision_attributes(test_df)

# Save as HTML to verify
fig.write_html(".tmp/test_decision_attributes_plot.html")

print("Decision attributes plot created successfully!")
print("Plot saved to .tmp/test_decision_attributes_plot.html")
