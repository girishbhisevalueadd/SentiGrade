import plotly.graph_objects as go
import os

import plotly.io as pio

# Manually set the executable path (Update with the correct location)
pio.orca.config.executable = r"C:\Users\VivekPol\anaconda3\Scripts\orca.exe"

# Save the config so it's applied in future sessions
pio.orca.config.save()


# Create a sample gauge chart
fig = go.Figure(go.Indicator(
    mode="gauge+number",
    value=34,
    title={'text': "Test Gauge"}))

# Define the output path
output_path = "test_gauge.png"

try:
    # Try saving the image using ORCA
    fig.write_image(output_path, engine="orca")
    print(f"Image saved at: {output_path}, Exists: {os.path.exists(output_path)}")
except Exception as e:
    print(f"Failed to save image: {e}")
