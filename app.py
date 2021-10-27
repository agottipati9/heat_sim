from flask import Flask, render_template, request, redirect, url_for
import numpy as np
import pandas as pd
import json
import plotly
import plotly.express as px
import plotly.subplots as sp
import plotly.graph_objects as go
from plotly.subplots import make_subplots


app = Flask(__name__)

@app.route('/')
def entry():
    return redirect('/home')

@app.route('/home', methods=["GET"])
def home():
  return render_template('index.html')

@app.route('/simulate', methods=["POST", "GET"])
def simulate():
  app.logger.info("ENTERING SIMULATE: Received POST Request.")
  if request.method == 'POST':
    error = None
    try:
      # Parse Data and Create Plots
      df, time_constant, flow_peak = simulate_heat_transfer(request)
      heat_fig = px.line(df, x='Time (s)', y=['Heat (kJ)', 'Heat Peak (kJ)'], title='Heat Captured vs. Time')
      flow_fig = px.line(df, x='Time (s)', y=['Heat_Flow (J/s)'], title='Heat Flow vs. Time')
      # Combine into Single Plot
      fig = make_subplots(rows=2, cols=1, subplot_titles=('Heat Captured vs. Time', 'Heat Flow vs. Time'), vertical_spacing=0.5)
      for d in heat_fig.data:
        fig.add_trace((go.Scatter(x=d['x'], y=d['y'], name=d['name'])), row=1, col=1)
        fig.update_xaxes(title_text="Time (s)", row=1, col=1)
        fig.update_yaxes(title_text="Stored Heat (kJ)", row=1, col=1)
      for d in flow_fig.data:
        fig.add_trace((go.Scatter(x=d['x'], y=d['y'],  name=d['name'])), row=2, col=1)
        fig.update_xaxes(title_text="Time (s)", row=2, col=1)
        fig.update_yaxes(title_text="Heat Flow (J/s)", row=2, col=1)
      graph = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
      app.logger.info("EXITING SIMULATE: Rendering Simulations.")
      return render_template('plot.html', graph=graph, time_constant=time_constant, flow_peak=flow_peak)
    except Exception as e:
      app.logger.error(f"EXITING SIMULATE: Error occurred while simulating data.\n{e}")
      return redirect('/home')
  else:
    app.logger.error("EXITING SIMULATE: Client did not POST to /simulate.")
    return redirect('/home')


def simulate_heat_transfer(request):
  # Parse Data
  T = float(request.form['T'])  # Assumed ambient temperature in C
  dT = float(request.form['dT'])  # Captured Heat from Solar Panel 250 watts to 400 watts per hour -> 250 J/h -> 4.16/s
  r = float(request.form['r'])  # Thermal Resistance of Pump C/J
  m = float(request.form['m'])  # Mass of Tank in kg
  cp = float(request.form['cp'])  # Specific heat of tank for volume in joules
  time = int(request.form['time'])  # Number of seconds to simulate
  # Calculate Heat Capacitance of Tank in KJ/C
  c = m * cp / 1000
  # Simulate Captured Heat and Heat Flow Over Time
  time = np.linspace(0, time)
  Q = (0 - r*dT)*(np.exp(-time/(r*c))) + dT*r + T  # Change in temperature based on heat capacitance with assumed started temp = 0
  H = c * Q  # Convert Temperature to heat energy
  qt = (dT / r)*(np.exp(-time/(r*c)))  # Heat flow
  thermal_time_constant = r*c
  stored_heat_peak = c*Q[-1] * np.ones(H.shape)
  peak_heat_flow = dT/r
  # Package data
  data = pd.DataFrame({'Heat (kJ)': H, 
                       'Heat Peak (kJ)': stored_heat_peak,
                       'Heat_Flow (J/s)': qt,
                       'Time (s)': time
  })
  return data, thermal_time_constant, peak_heat_flow

if __name__ == "__main__":
  app.run(host='localhost', port=8000, debug=True)