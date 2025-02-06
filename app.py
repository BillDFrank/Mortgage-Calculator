# app.py
from flask import Flask, render_template_string, request, redirect, url_for, flash
import math
import json
import uuid
import plotly.graph_objs as go
import plotly.offline as pyo

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Needed for flashing messages

# Global dictionary to store scenarios (in-memory, not persistent)
SCENARIOS = {}

# HTML template (using Flask's render_template_string for a self-contained example)
HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Mortgage Calculator</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
      body {
        font-family: Arial, sans-serif;
        background-color: #f4f4f4;
        color: #333;
        transition: background-color 0.3s, color 0.3s;
      }
      .dark-mode {
        background-color: #333;
        color: #f4f4f4;
      }
      .container { max-width: 1000px; margin: auto; padding: 20px; }
      input, select { padding: 5px; margin: 5px 0; width: 100%; }
      .row { display: flex; flex-wrap: wrap; }
      .col-50 { flex: 0 0 50%; padding: 10px; }
      .toggle-btn { position: fixed; top: 10px; right: 10px; padding: 10px; }
      table, th, td { border: 1px solid #aaa; border-collapse: collapse; padding: 5px; }
      table { width: 100%; margin-top: 20px; }
      .message { color: red; }
    </style>
  </head>
  <body id="body">
    <button class="toggle-btn" onclick="toggleDarkMode()">Toggle Dark/Light Mode</button>
    <div class="container">
      <h1>Mortgage Calculator (Euros)</h1>
      {% with messages = get_flashed_messages() %}
        {% if messages %}
          <ul class="message">
          {% for msg in messages %}
            <li>{{ msg }}</li>
          {% endfor %}
          </ul>
        {% endif %}
      {% endwith %}
      <form method="POST" action="{{ url_for('index') }}">
        <div class="row">
          <div class="col-50">
            <label>House Price (€)</label>
            <input type="number" step="0.01" name="house_price" value="{{ scenario.house_price if scenario.house_price is not none else '' }}">
          </div>
          <div class="col-50">
            <label>Down Payment (€)</label>
            <input type="number" step="0.01" name="down_payment" value="{{ scenario.down_payment if scenario.down_payment is not none else '' }}">
          </div>
          <div class="col-50">
            <label>Loan Term (years)</label>
            <input type="number" step="0.01" name="loan_term" value="{{ scenario.loan_term if scenario.loan_term is not none else '' }}">
          </div>
          <div class="col-50">
            <label>Interest Rate (%)</label>
            <input type="number" step="0.01" name="interest_rate" value="{{ scenario.interest_rate if scenario.interest_rate is not none else '' }}">
          </div>
          <div class="col-50">
            <label>Monthly Payment (€)</label>
            <input type="number" step="0.01" name="monthly_payment" value="{{ scenario.monthly_payment if scenario.monthly_payment is not none else '' }}">
          </div>
          <div class="col-50">
            <label>Bank Spread (%) (optional)</label>
            <input type="number" step="0.01" name="bank_spread" value="{{ scenario.bank_spread if scenario.bank_spread is not none else '' }}">
          </div>
          <div class="col-50">
            <label>Bank Insurances (monthly, €) (optional)</label>
            <input type="number" step="0.01" name="bank_insurances" value="{{ scenario.bank_insurances if scenario.bank_insurances is not none else '' }}">
          </div>
          <div class="col-50">
            <label>Additional Monthly Payment (€) (optional)</label>
            <input type="number" step="0.01" name="extra_monthly" value="{{ scenario.extra_monthly if scenario.extra_monthly is not none else '' }}">
          </div>
          <div class="col-50">
            <label>Additional Annual Payment (€) (optional)</label>
            <input type="number" step="0.01" name="extra_annual" value="{{ scenario.extra_annual if scenario.extra_annual is not none else '' }}">
          </div>
          <div class="col-50">
            <label>Loan Type</label>
            <select name="loan_type" id="loan_type" onchange="toggleAdjustableFields()">
              <option value="fixed" {% if scenario.loan_type=='fixed' %}selected{% endif %}>Fixed Rate</option>
              <option value="adjustable" {% if scenario.loan_type=='adjustable' %}selected{% endif %}>Adjustable (2-Stage)</option>
            </select>
          </div>
          <div class="col-50" id="adjustable_fields" style="display: {% if scenario.loan_type=='adjustable' %}block{% else %}none{% endif %};">
            <label>Fixed Period (years)</label>
            <input type="number" step="0.01" name="fixed_period" value="{{ scenario.fixed_period if scenario.fixed_period is not none else '' }}">
            <label>Adjusted Interest Rate (%)</label>
            <input type="number" step="0.01" name="adjusted_interest_rate" value="{{ scenario.adjusted_interest_rate if scenario.adjusted_interest_rate is not none else '' }}">
          </div>
        </div>
        <button type="submit" name="action" value="simulate">Simulate Mortgage</button>
        <button type="submit" name="action" value="save">Save Scenario</button>
      </form>
      
      {% if results %}
      <h2>Results</h2>
      <p><strong>Calculated Field:</strong> {{ results.calculated_field }}</p>
      <p><strong>Calculated Value:</strong> {{ results.calculated_value|round(2) }} </p>
      <p><strong>Total Cost:</strong> €{{ results.total_cost|round(2) }}</p>
      <p><strong>Total Interest Paid:</strong> €{{ results.total_interest|round(2) }}</p>
      <p><strong>Mortgage Duration (months):</strong> {{ results.duration }}</p>
      
      <h3>Amortization Schedule</h3>
      <table>
        <tr>
          <th>Month</th>
          <th>Payment (€)</th>
          <th>Extra Payment (€)</th>
          <th>Interest (€)</th>
          <th>Principal (€)</th>
          <th>Remaining Balance (€)</th>
        </tr>
        {% for row in results.amortization %}
        <tr>
          <td>{{ row.month }}</td>
          <td>{{ row.payment|round(2) }}</td>
          <td>{{ row.extra|round(2) }}</td>
          <td>{{ row.interest|round(2) }}</td>
          <td>{{ row.principal|round(2) }}</td>
          <td>{{ row.balance|round(2) }}</td>
        </tr>
        {% endfor %}
      </table>
      
      <h3>Impact of Different Interest Rates on Monthly Payment</h3>
      <div id="plot_div">{{ plot_div|safe }}</div>
      {% endif %}
      
      {% if saved_scenarios %}
      <h2>Saved Scenarios</h2>
      <ul>
        {% for sid, s in saved_scenarios.items() %}
          <li><a href="{{ url_for('load_scenario', scenario_id=sid) }}">{{ sid }}</a> : {{ s }}</li>
        {% endfor %}
      </ul>
      {% endif %}
      
    </div>
    
    <script>
      function toggleDarkMode() {
        document.getElementById("body").classList.toggle("dark-mode");
      }
      function toggleAdjustableFields() {
        var loanType = document.getElementById("loan_type").value;
        document.getElementById("adjustable_fields").style.display = (loanType == "adjustable") ? "block" : "none";
      }
    </script>
  </body>
</html>
"""

def parse_float(field):
    try:
        return float(field)
    except (ValueError, TypeError):
        return None

def effective_interest_rate(interest_rate, bank_spread):
    # Both in percentages: combine them and convert to monthly decimal
    rate = parse_float(interest_rate)
    spread = parse_float(bank_spread) if bank_spread is not None else 0
    if rate is None:
        return None
    return (rate + spread) / 100 / 12

def calculate_monthly_payment(P, monthly_rate, n):
    # Standard annuity formula for fixed rate
    if monthly_rate == 0:
        return P / n
    return P * monthly_rate * (1 + monthly_rate)**n / ((1 + monthly_rate)**n - 1)

def solve_for_unknown(data):
    """
    Determine which field (house_price, down_payment, loan_term, interest_rate, monthly_payment) is missing.
    Compute that missing field using the standard annuity formula.
    Note: For interest rate and loan term, a numerical method is used.
    Returns a dict with keys:
      - calculated_field: name of field calculated
      - calculated_value: computed value
    """
    # Extract values
    house_price = parse_float(data.get("house_price"))
    down_payment = parse_float(data.get("down_payment"))
    loan_term = parse_float(data.get("loan_term"))
    interest_rate = parse_float(data.get("interest_rate"))
    monthly_payment = parse_float(data.get("monthly_payment"))
    bank_spread = parse_float(data.get("bank_spread"))
    
    # Count how many of these are None:
    inputs = {
        "house_price": house_price,
        "down_payment": down_payment,
        "loan_term": loan_term,
        "interest_rate": interest_rate,
        "monthly_payment": monthly_payment
    }
    missing = [k for k, v in inputs.items() if v is None]
    if len(missing) > 1:
        raise ValueError("Please leave exactly one field empty (except bank spread and bank insurances) to calculate it automatically.")
    if len(missing) == 0:
        # Nothing to calculate
        return None
    unknown = missing[0]
    # P = principal = house_price - down_payment
    if unknown != "house_price" and house_price is None:
        raise ValueError("House price must be provided if the unknown field is not house price.")
    if unknown != "down_payment" and down_payment is None:
        raise ValueError("Down payment must be provided if the unknown field is not down payment.")
    if unknown != "loan_term" and loan_term is None:
        raise ValueError("Loan term must be provided if the unknown field is not loan term.")
    if unknown != "interest_rate" and interest_rate is None:
        raise ValueError("Interest rate must be provided if the unknown field is not interest rate.")
    if unknown != "monthly_payment" and monthly_payment is None:
        raise ValueError("Monthly payment must be provided if the unknown field is not monthly payment.")
    
    # Determine principal and number of months
    if unknown == "house_price":
        # house_price = down_payment + principal, where principal = monthly_payment * ((1+r)^n - 1)/(r*(1+r)^n)
        r = effective_interest_rate(interest_rate, bank_spread)
        n = int(loan_term * 12)
        principal = monthly_payment * ((1+r)**n - 1) / (r * (1+r)**n) if r != 0 else monthly_payment * n
        calc = down_payment + principal
    elif unknown == "down_payment":
        r = effective_interest_rate(interest_rate, bank_spread)
        n = int(loan_term * 12)
        principal = monthly_payment * ((1+r)**n - 1) / (r * (1+r)**n) if r != 0 else monthly_payment * n
        calc = house_price - principal
    elif unknown == "loan_term":
        # Solve for n from: monthly_payment = P * r(1+r)^n / ((1+r)^n -1)
        r = effective_interest_rate(interest_rate, bank_spread)
        P = house_price - down_payment
        if monthly_payment <= P * r:
            raise ValueError("Monthly payment too low to ever pay the interest!")
        n = math.log(monthly_payment / (monthly_payment - P * r)) / math.log(1+r)
        calc = n / 12  # in years
    elif unknown == "interest_rate":
        # Solve for r given monthly_payment = P * r(1+r)^n/((1+r)^n-1)
        # Use Newton-Raphson method
        P = house_price - down_payment
        n = int(loan_term * 12)
        def f(r):
            if r == 0:
                return monthly_payment - P / n
            return monthly_payment - (P * r * (1+r)**n)/((1+r)**n - 1)
        def fprime(r):
            if r == 0:
                return -P * n / (n**2)
            # derivative approximated numerically
            h = 1e-6
            return (f(r+h)-f(r-h))/(2*h)
        r_guess = 0.01  # initial guess (monthly rate)
        for i in range(100):
            f_val = f(r_guess)
            fp = fprime(r_guess)
            if fp == 0:
                break
            r_new = r_guess - f_val/fp
            if abs(r_new - r_guess) < 1e-8:
                r_guess = r_new
                break
            r_guess = r_new
        # Subtract bank spread to return the pure interest rate
        calc = r_guess * 12 * 100 - (bank_spread if bank_spread is not None else 0)
    elif unknown == "monthly_payment":
        r = effective_interest_rate(interest_rate, bank_spread)
        n = int(loan_term * 12)
        P = house_price - down_payment
        calc = calculate_monthly_payment(P, r, n)
    else:
        calc = None
    return {"calculated_field": unknown, "calculated_value": calc}

def simulate_amortization(data, computed_monthly_payment):
    """
    Simulate the amortization schedule month by month.
    Supports a two-stage adjustable loan:
      - For fixed loans: use the given interest rate throughout.
      - For adjustable loans: use the initial rate for the 'fixed_period' (in years)
        then switch to the adjusted rate.
    Additional monthly and annual extra payments are added to each month.
    Bank insurances are added to the monthly payment but are not subtracted from the principal.
    Returns a tuple: (amortization schedule list, total interest paid, total cost, duration in months)
    """
    house_price = parse_float(data.get("house_price"))
    down_payment = parse_float(data.get("down_payment"))
    loan_term = parse_float(data.get("loan_term"))
    interest_rate = parse_float(data.get("interest_rate"))
    bank_spread = parse_float(data.get("bank_spread"))
    monthly_payment = parse_float(data.get("monthly_payment"))
    bank_insurances = parse_float(data.get("bank_insurances")) or 0
    extra_monthly = parse_float(data.get("extra_monthly")) or 0
    extra_annual = parse_float(data.get("extra_annual")) or 0
    loan_type = data.get("loan_type", "fixed")
    fixed_period = parse_float(data.get("fixed_period")) if data.get("fixed_period") else None
    adjusted_interest_rate = parse_float(data.get("adjusted_interest_rate")) if data.get("adjusted_interest_rate") else None

    # Principal is:
    principal = house_price - down_payment
    balance = principal
    schedule = []
    total_interest = 0
    month = 0
    n = int(loan_term * 12)
    
    # Pre-calculate monthly interest rates for each stage:
    if loan_type == "adjustable" and fixed_period is not None and adjusted_interest_rate is not None:
        fixed_months = int(fixed_period * 12)
        r_fixed = effective_interest_rate(interest_rate, bank_spread)
        r_adjusted = (adjusted_interest_rate + (bank_spread if bank_spread else 0)) / 100 / 12
    else:
        fixed_months = n
        r_fixed = effective_interest_rate(interest_rate, bank_spread)
        r_adjusted = r_fixed

    # If monthly_payment is not computed (because it was auto-calculated), use the computed value.
    if monthly_payment is None:
        monthly_payment = computed_monthly_payment

    # Amortization simulation:
    while balance > 0.01 and month < 1000:  # safeguard to avoid infinite loops
        month += 1
        # Determine the current monthly interest rate:
        current_r = r_fixed if month <= fixed_months else r_adjusted
        interest = balance * current_r
        principal_payment = monthly_payment - interest
        extra = extra_monthly
        # Add annual extra payment in the month corresponding to year-end (approximately)
        if month % 12 == 0:
            extra += extra_annual
        # Ensure we do not pay more than the remaining balance:
        if principal_payment + extra > balance:
            principal_payment = balance
            extra = 0
            payment = balance + interest
        else:
            payment = monthly_payment
        balance = balance - (principal_payment + extra)
        total_interest += interest
        schedule.append({
            "month": month,
            "payment": payment,
            "extra": extra,
            "interest": interest,
            "principal": principal_payment + extra,
            "balance": max(balance, 0)
        })
    duration = month
    # Total cost includes all payments and bank insurances:
    total_payments = sum([row["payment"] + bank_insurances for row in schedule])
    total_cost = total_payments
    return schedule, total_interest, total_cost, duration

def generate_interest_rate_graph(data, computed_payment):
    """
    Generate a Plotly graph that shows the impact of varying the interest rate on monthly payment.
    We vary the interest rate ±2% around the provided interest_rate.
    """
    base_interest = parse_float(data.get("interest_rate"))
    if base_interest is None:
        base_interest = 1.0
    rates = [base_interest + delta for delta in [i/4.0 for i in range(-8,9)]]
    payments = []
    house_price = parse_float(data.get("house_price"))
    down_payment = parse_float(data.get("down_payment"))
    loan_term = parse_float(data.get("loan_term"))
    bank_spread = parse_float(data.get("bank_spread"))
    P = house_price - down_payment
    n = int(loan_term * 12)
    for r in rates:
        monthly_r = (r + (bank_spread if bank_spread else 0)) / 100 / 12
        pay = calculate_monthly_payment(P, monthly_r, n)
        payments.append(pay)
    trace = go.Scatter(x=rates, y=payments, mode='lines+markers', name='Monthly Payment')
    layout = go.Layout(title='Impact of Interest Rate on Monthly Payment',
                       xaxis=dict(title='Interest Rate (%)'),
                       yaxis=dict(title='Monthly Payment (€)'))
    fig = go.Figure(data=[trace], layout=layout)
    div = pyo.plot(fig, output_type='div', include_plotlyjs=False)
    return div

@app.route('/', methods=['GET', 'POST'])
def index():
    results = None
    plot_div = None
    scenario = {
        "house_price": None,
        "down_payment": None,
        "loan_term": None,
        "interest_rate": None,
        "monthly_payment": None,
        "bank_spread": None,
        "bank_insurances": None,
        "extra_monthly": None,
        "extra_annual": None,
        "loan_type": "fixed",
        "fixed_period": None,
        "adjusted_interest_rate": None
    }
    if request.method == 'POST':
        form = request.form
        # Build scenario dict for saving/loading
        for key in scenario.keys():
            scenario[key] = form.get(key) if form.get(key) != "" else None
        
        action = form.get("action")
        # If the action is "save", store the scenario and redirect
        if action == "save":
            scenario_id = str(uuid.uuid4())[:8]
            SCENARIOS[scenario_id] = scenario.copy()
            flash(f"Scenario saved with ID: {scenario_id}")
            return redirect(url_for('index'))
        # For simulation:
        try:
            unknown_result = solve_for_unknown(form)
        except Exception as e:
            flash(str(e))
            unknown_result = None

        # If monthly_payment was the unknown, use computed value; else use the provided value.
        computed_monthly_payment = None
        if unknown_result and unknown_result["calculated_field"] == "monthly_payment":
            computed_monthly_payment = unknown_result["calculated_value"]
            form = request.form.copy()
            form = form.to_dict()
            form["monthly_payment"] = computed_monthly_payment
        else:
            computed_monthly_payment = parse_float(form.get("monthly_payment"))
        
        schedule, total_interest, total_cost, duration = simulate_amortization(form, computed_monthly_payment)
        # Generate graph:
        plot_div = generate_interest_rate_graph(form, computed_monthly_payment)
        results = {
            "calculated_field": unknown_result["calculated_field"] if unknown_result else "None",
            "calculated_value": unknown_result["calculated_value"] if unknown_result else 0,
            "amortization": schedule,
            "total_interest": total_interest,
            "total_cost": total_cost,
            "duration": duration
        }
    return render_template_string(HTML_TEMPLATE, results=results, plot_div=plot_div, scenario=scenario, saved_scenarios=SCENARIOS)

@app.route('/load/<scenario_id>')
def load_scenario(scenario_id):
    scenario = SCENARIOS.get(scenario_id)
    if not scenario:
        flash("Scenario not found.")
        return redirect(url_for('index'))
    # Pre-populate the form with saved scenario data by rendering the template with scenario values.
    return render_template_string(HTML_TEMPLATE, results=None, plot_div=None, scenario=scenario, saved_scenarios=SCENARIOS)

if __name__ == '__main__':
    app.run(debug=True)
