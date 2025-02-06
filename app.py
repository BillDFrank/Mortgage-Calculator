# app.py
from flask import Flask, render_template_string, request, redirect, url_for, flash
import math
import uuid
import plotly.graph_objs as go
import plotly.offline as pyo

app = Flask(__name__)
# Replace with a securely generated key
app.secret_key = 'your_generated_secret_key'

# Global dictionary to store scenarios (in-memory, not persistent)
SCENARIOS = {}

# HTML template using Materialize CSS
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>Mortgage Calculator</title>
    <!-- Materialize CSS -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/materialize/1.0.0/css/materialize.min.css">
    <!-- Material Icons -->
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    <style>
      html, body {
        margin: 0;
        padding: 0;
      }
      body {
        padding-top: 0;
      }
      .dark-mode {
        background-color: #424242 !important;
        color: #fff !important;
      }
      .dark-mode .card {
        background-color: #616161;
        color: #fff;
      }
      .dark-mode .card .card-content, .dark-mode .card .card-title, .dark-mode label, .dark-mode p {
        color: #fff !important;
      }
      .red-border input:not([readonly]),
      .red-border textarea:not([readonly]) {
        border-bottom: 2px solid red !important;
        box-shadow: 0 1px 0 0 red !important;
      }
      .green-border input:not([readonly]),
      .green-border textarea:not([readonly]) {
        border-bottom: 2px solid green !important;
        box-shadow: 0 1px 0 0 green !important;
      }
      .toggle-table {
        margin-bottom: 15px;
      }
      .results-card {
        margin-bottom: 15px;
      }
      nav {
        margin-bottom: 0;
      }
      /* Ensure the amortization table is displayed initially */
      #amortization_table {
        display: block;
      }
    </style>
  </head>
  <body id="body">
    <!-- Navbar fixed at top -->
    <nav class="blue">
      <div class="nav-wrapper container">
        <a href="#" class="brand-logo">Mortgage Calculator</a>
        <ul id="nav-mobile" class="right">
          <li><a href="#" onclick="toggleDarkMode()"><i class="material-icons">brightness_6</i></a></li>
        </ul>
      </div>
    </nav>
    
    <div class="container" style="margin-top: 0;">
      {% with messages = get_flashed_messages() %}
        {% if messages %}
          <div class="card-panel red lighten-2">
            <ul>
              {% for msg in messages %}
                <li>{{ msg }}</li>
              {% endfor %}
            </ul>
          </div>
        {% endif %}
      {% endwith %}
      
      <div class="row">
        <!-- Left Column: Inputs -->
        <div class="col s12 m6">
          <div class="card">
            <div class="card-content">
              <span class="card-title">Mortgage Inputs (Euros)</span>
              <form method="POST" action="{{ url_for('index') }}">
                <div class="row">
                  <!-- Required fields with dynamic borders -->
                  <div class="input-field col s12 {% if field_status.house_price %}{{ 'red-border' if field_status.house_price=='red' else 'green-border' }}{% endif %}">
                    <input id="house_price" type="number" step="0.01" name="house_price" value="{{ scenario.house_price if scenario.house_price is not none else '' }}">
                    <label for="house_price">House Price (€)</label>
                  </div>
                  <div class="input-field col s12 {% if field_status.down_payment %}{{ 'red-border' if field_status.down_payment=='red' else 'green-border' }}{% endif %}">
                    <input id="down_payment" type="number" step="0.01" name="down_payment" value="{{ scenario.down_payment if scenario.down_payment is not none else '' }}">
                    <label for="down_payment">Down Payment (€)</label>
                  </div>
                  <div class="input-field col s12 {% if field_status.loan_term %}{{ 'red-border' if field_status.loan_term=='red' else 'green-border' }}{% endif %}">
                    <input id="loan_term" type="number" step="0.01" name="loan_term" value="{{ scenario.loan_term if scenario.loan_term is not none else '' }}">
                    <label for="loan_term">Loan Term (years)</label>
                  </div>
                  <div class="input-field col s12 {% if field_status.interest_rate %}{{ 'red-border' if field_status.interest_rate=='red' else 'green-border' }}{% endif %}">
                    <input id="interest_rate" type="number" step="0.001" name="interest_rate" value="{{ scenario.interest_rate if scenario.interest_rate is not none else '' }}">
                    <label for="interest_rate">Interest Rate (%)</label>
                  </div>
                  <div class="input-field col s12 {% if field_status.monthly_payment %}{{ 'red-border' if field_status.monthly_payment=='red' else 'green-border' }}{% endif %}">
                    <input id="monthly_payment" type="number" step="0.01" name="monthly_payment" value="{{ scenario.monthly_payment if scenario.monthly_payment is not none else '' }}">
                    <label for="monthly_payment">Monthly Payment (€)</label>
                  </div>
                  <!-- Optional fields -->
                  <div class="input-field col s12">
                    <input id="bank_spread" type="number" step="0.01" name="bank_spread" value="{{ scenario.bank_spread if scenario.bank_spread is not none else '' }}">
                    <label for="bank_spread">Bank Spread (%) (optional)</label>
                  </div>
                  <div class="input-field col s12">
                    <input id="bank_insurances" type="number" step="0.01" name="bank_insurances" value="{{ scenario.bank_insurances if scenario.bank_insurances is not none else '' }}">
                    <label for="bank_insurances">Bank Insurances (monthly, €) (optional)</label>
                  </div>
                  <div class="input-field col s12">
                    <input id="extra_monthly" type="number" step="0.01" name="extra_monthly" value="{{ scenario.extra_monthly if scenario.extra_monthly is not none else '' }}">
                    <label for="extra_monthly">Additional Monthly Payment (€) (optional)</label>
                  </div>
                  <div class="input-field col s12">
                    <input id="extra_annual" type="number" step="0.01" name="extra_annual" value="{{ scenario.extra_annual if scenario.extra_annual is not none else '' }}">
                    <label for="extra_annual">Additional Annual Payment (€) (optional)</label>
                  </div>
                  <div class="input-field col s12">
                    <input id="extra_fee_rate" type="number" step="0.01" name="extra_fee_rate" value="{{ scenario.extra_fee_rate if scenario.extra_fee_rate is not none else '' }}">
                    <label for="extra_fee_rate">Extra Payment Fee (%) (optional)</label>
                    <span class="helper-text">Average fee in Portugal is around 2.5%</span>
                  </div>
                  <!-- Loan Type: Fixed, Adjustable (2-Stage), Full Variable -->
                  <div class="input-field col s12">
                    <select name="loan_type" id="loan_type" onchange="toggleAdjustableFields()">
                      <option value="fixed" {% if scenario.loan_type=='fixed' %}selected{% endif %}>Fixed Rate</option>
                      <option value="adjustable" {% if scenario.loan_type=='adjustable' %}selected{% endif %}>Adjustable (2-Stage)</option>
                      <option value="full_variable" {% if scenario.loan_type=='full_variable' %}selected{% endif %}>Full Variable</option>
                    </select>
                    <label>Loan Type</label>
                  </div>
                  <!-- Adjustable fields (appear only for Adjustable) -->
                  <div class="input-field col s12" id="adjustable_fields" style="display: {% if scenario.loan_type=='adjustable' %}block{% else %}none{% endif %};">
                    <input id="fixed_period" type="number" step="0.01" name="fixed_period" value="{{ scenario.fixed_period if scenario.fixed_period is not none else '' }}">
                    <label for="fixed_period">Fixed Period (years)</label>
                    <input id="adjusted_interest_rate" type="number" step="0.001" name="adjusted_interest_rate" value="{{ scenario.adjusted_interest_rate if scenario.adjusted_interest_rate is not none else '' }}">
                    <label for="adjusted_interest_rate">Adjusted Interest Rate (%)</label>
                  </div>
                  <!-- Table View: Monthly or Yearly -->
                  <div class="input-field col s12">
                    <select name="table_view" id="table_view">
                      <option value="monthly" {% if scenario.get('table_view','monthly')=='monthly' %}selected{% endif %}>Monthly Table</option>
                      <option value="yearly" {% if scenario.get('table_view','monthly')=='yearly' %}selected{% endif %}>Yearly Table</option>
                    </select>
                    <label>Table View</label>
                  </div>
                </div>
                <div class="row">
                  <div class="col s12">
                    <button class="btn waves-effect waves-light" type="submit" name="action" value="simulate">
                      Simulate Mortgage <i class="material-icons right">trending_up</i>
                    </button>
                    <button class="btn waves-effect waves-light" type="submit" name="action" value="save">
                      Save Scenario <i class="material-icons right">save</i>
                    </button>
                  </div>
                </div>
              </form>
            </div>
          </div>
        </div>
        
        <!-- Right Column: Results -->
        <div class="col s12 m6">
          {% if results %}
          <div class="card results-card">
            <div class="card-content">
              <span class="card-title">Results</span>
              <p><strong>Calculated Field:</strong> {{ results.calculated_field }}</p>
              <p><strong>Calculated Value:</strong> {{ results.calculated_value|round(4) }}</p>
              <p><strong>Total Cost:</strong> €{{ results.total_cost|round(2) }}</p>
              <p><strong>Total Interest Paid:</strong> €{{ results.total_interest|round(2) }}</p>
              <p><strong>Mortgage Duration:</strong> {{ results.duration }} months</p>
            </div>
          </div>
          <!-- Toggle for Table -->
          <div class="card results-card">
            <div class="card-content">
              <button class="btn-flat toggle-table" id="toggleTableBtn">Toggle Amortization Table</button>
              <div id="amortization_table">
                <table class="striped responsive-table">
                  <thead>
                    <tr>
                      <th>{{ "Year" if table_view=='yearly' else "Month" }}</th>
                      <th>Payment (€)</th>
                      <th>Extra (€)</th>
                      <th>Fee (€)</th>
                      <th>Interest (€)</th>
                      <th>Principal (€)</th>
                      <th>Balance (€)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {% for row in results.amortization %}
                    <tr>
                      <td>{{ row.period }}</td>
                      <td>{{ row.payment|round(2) }}</td>
                      <td>{{ row.extra|round(2) }}</td>
                      <td>{{ row.fee|round(2) }}</td>
                      <td>{{ row.interest|round(2) }}</td>
                      <td>{{ row.principal|round(2) }}</td>
                      <td>{{ row.balance|round(2) }}</td>
                    </tr>
                    {% endfor %}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
          <!-- Graphs at the bottom -->
          <div class="card results-card">
            <div class="card-content">
              <span class="card-title">Interest Rate Impact</span>
              <div id="plot_div">{{ plot_div|safe }}</div>
            </div>
          </div>
          <div class="card results-card">
            <div class="card-content">
              <span class="card-title">Amortization Graph</span>
              <div id="amortization_div">{{ amortization_div|safe }}</div>
            </div>
          </div>
          {% endif %}
        </div>
      </div>
      
      {% if saved_scenarios %}
      <div class="card">
        <div class="card-content">
          <span class="card-title">Saved Scenarios</span>
          <ul class="collection">
            {% for sid, s in saved_scenarios.items() %}
              <li class="collection-item">
                <a href="{{ url_for('load_scenario', scenario_id=sid) }}">{{ sid }}</a> : {{ s }}
              </li>
            {% endfor %}
          </ul>
        </div>
      </div>
      {% endif %}
    </div>
    
    <!-- Materialize and jQuery -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/materialize/1.0.0/js/materialize.min.js"></script>
    <script>
      document.addEventListener('DOMContentLoaded', function() {
        var elemsSelect = document.querySelectorAll('select');
        M.FormSelect.init(elemsSelect);
      });
      function toggleDarkMode() {
        document.getElementById("body").classList.toggle("dark-mode");
      }
      function toggleAdjustableFields() {
        var loanType = document.getElementById("loan_type").value;
        document.getElementById("adjustable_fields").style.display = (loanType == "adjustable") ? "block" : "none";
      }
      // Use jQuery to toggle the table with a slide effect
      $(document).ready(function(){
        $("#toggleTableBtn").click(function(){
          $("#amortization_table").slideToggle();
        });
      });
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
    rate = parse_float(interest_rate)
    spread = parse_float(bank_spread) if bank_spread is not None else 0
    if rate is None:
        return None
    return (rate + spread) / 100 / 12


def calculate_monthly_payment(P, monthly_rate, n):
    if monthly_rate == 0:
        return P / n
    return P * monthly_rate * (1 + monthly_rate)**n / ((1 + monthly_rate)**n - 1)


def solve_for_unknown(data):
    house_price = parse_float(data.get("house_price"))
    down_payment = parse_float(data.get("down_payment"))
    loan_term = parse_float(data.get("loan_term"))
    interest_rate = parse_float(data.get("interest_rate"))
    monthly_payment = parse_float(data.get("monthly_payment"))
    bank_spread = parse_float(data.get("bank_spread"))

    inputs = {
        "house_price": house_price,
        "down_payment": down_payment,
        "loan_term": loan_term,
        "interest_rate": interest_rate,
        "monthly_payment": monthly_payment
    }
    missing = [k for k, v in inputs.items() if v is None]
    if len(missing) > 1:
        raise ValueError(
            "Please leave exactly one required field empty (for auto-calculation).")
    if len(missing) == 0:
        raise ValueError(
            "Please leave exactly one required field empty so that it can be calculated automatically.")
    unknown = missing[0]

    if unknown == "house_price":
        r = effective_interest_rate(interest_rate, bank_spread)
        n = int(loan_term * 12)
        principal = monthly_payment * \
            ((1+r)**n - 1) / (r * (1+r)**n) if r != 0 else monthly_payment * n
        calc = down_payment + principal
    elif unknown == "down_payment":
        r = effective_interest_rate(interest_rate, bank_spread)
        n = int(loan_term * 12)
        principal = monthly_payment * \
            ((1+r)**n - 1) / (r * (1+r)**n) if r != 0 else monthly_payment * n
        calc = house_price - principal
    elif unknown == "loan_term":
        r = effective_interest_rate(interest_rate, bank_spread)
        P = house_price - down_payment
        if monthly_payment <= P * r:
            raise ValueError("Monthly payment too low to pay the interest!")
        n = math.log(monthly_payment /
                     (monthly_payment - P * r)) / math.log(1+r)
        calc = n / 12
    elif unknown == "interest_rate":
        P = house_price - down_payment
        n = int(loan_term * 12)

        def f(r):
            if r == 0:
                return monthly_payment - P / n
            return monthly_payment - (P * r * (1+r)**n)/((1+r)**n - 1)

        def fprime(r):
            h = 1e-6
            return (f(r+h)-f(r-h))/(2*h)
        r_guess = 0.01
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
        calc = r_guess * 12 * 100 - \
            (bank_spread if bank_spread is not None else 0)
    elif unknown == "monthly_payment":
        r = effective_interest_rate(interest_rate, bank_spread)
        n = int(loan_term * 12)
        P = house_price - down_payment
        calc = calculate_monthly_payment(P, r, n)
    else:
        calc = None
    return {"calculated_field": unknown, "calculated_value": calc}


def simulate_amortization(data, computed_monthly_payment):
    house_price = parse_float(data.get("house_price"))
    down_payment = parse_float(data.get("down_payment"))
    loan_term = parse_float(data.get("loan_term"))
    interest_rate = parse_float(data.get("interest_rate"))
    bank_spread = parse_float(data.get("bank_spread"))
    monthly_payment = parse_float(data.get("monthly_payment"))
    bank_insurances = parse_float(data.get("bank_insurances")) or 0
    extra_monthly = parse_float(data.get("extra_monthly")) or 0
    extra_annual = parse_float(data.get("extra_annual")) or 0
    extra_fee_rate = parse_float(data.get("extra_fee_rate")) or 0
    loan_type = data.get("loan_type", "fixed")
    fixed_period = parse_float(data.get("fixed_period")) if data.get(
        "fixed_period") else None
    adjusted_interest_rate = parse_float(data.get(
        "adjusted_interest_rate")) if data.get("adjusted_interest_rate") else None
    table_view = data.get("table_view", "monthly")

    principal = house_price - down_payment
    balance = principal
    schedule = []
    total_interest = 0
    total_fee = 0
    month = 0
    n = int(loan_term * 12)

    # Determine interest rate behavior based on loan type:
    if loan_type == "adjustable" and fixed_period is not None and adjusted_interest_rate is not None:
        fixed_months = int(fixed_period * 12)
        r_fixed = effective_interest_rate(interest_rate, bank_spread)
        r_adjusted = (adjusted_interest_rate +
                      (bank_spread if bank_spread else 0)) / 100 / 12
    elif loan_type == "full_variable":
        fixed_months = 0
        r_fixed = effective_interest_rate(interest_rate, bank_spread)
        r_adjusted = r_fixed
    else:
        fixed_months = n
        r_fixed = effective_interest_rate(interest_rate, bank_spread)
        r_adjusted = r_fixed

    if monthly_payment is None:
        monthly_payment = computed_monthly_payment

    monthly_schedule = []
    while balance > 0.01 and month < 1000:
        month += 1
        current_r = r_fixed if month <= fixed_months else r_adjusted
        interest = balance * current_r
        principal_payment = monthly_payment - interest
        extra = extra_monthly
        if month % 12 == 0:
            extra += extra_annual
        fee = extra * (extra_fee_rate / 100) if extra > 0 else 0
        if principal_payment + extra > balance:
            principal_payment = balance
            extra = 0
            fee = 0
            payment = balance + interest
        else:
            payment = monthly_payment
        balance = balance - (principal_payment + extra)
        total_interest += interest
        total_fee += fee
        monthly_schedule.append({
            "month": month,
            "payment": payment,
            "extra": extra,
            "fee": fee,
            "interest": interest,
            "principal": principal_payment + extra,
            "balance": max(balance, 0)
        })

    aggregated_schedule = []
    if table_view == "yearly":
        current_year = 1
        year_data = {"payment": 0, "extra": 0, "fee": 0,
                     "interest": 0, "principal": 0, "balance": None}
        for row in monthly_schedule:
            year_data["payment"] += row["payment"]
            year_data["extra"] += row["extra"]
            year_data["fee"] += row["fee"]
            year_data["interest"] += row["interest"]
            year_data["principal"] += row["principal"]
            year_data["balance"] = row["balance"]
            if row["month"] % 12 == 0:
                aggregated_schedule.append({
                    "period": current_year,
                    "payment": year_data["payment"],
                    "extra": year_data["extra"],
                    "fee": year_data["fee"],
                    "interest": year_data["interest"],
                    "principal": year_data["principal"],
                    "balance": year_data["balance"]
                })
                current_year += 1
                year_data = {"payment": 0, "extra": 0, "fee": 0,
                             "interest": 0, "principal": 0, "balance": None}
        if monthly_schedule[-1]["month"] % 12 != 0:
            aggregated_schedule.append({
                "period": current_year,
                "payment": year_data["payment"],
                "extra": year_data["extra"],
                "fee": year_data["fee"],
                "interest": year_data["interest"],
                "principal": year_data["principal"],
                "balance": year_data["balance"]
            })
    else:
        for row in monthly_schedule:
            row["period"] = row["month"]
            aggregated_schedule.append(row)

    total_payments = sum([row["payment"] for row in monthly_schedule]
                         ) + bank_insurances * len(monthly_schedule)
    total_cost = total_payments + total_fee
    return aggregated_schedule, total_interest, total_cost, month


def generate_interest_rate_graph(data, computed_payment):
    base_interest = parse_float(data.get("interest_rate"))
    if base_interest is None:
        base_interest = 1.0
    rates = [base_interest + delta for delta in [i/4.0 for i in range(-8, 9)]]
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
    trace = go.Scatter(x=rates, y=payments,
                       mode='lines+markers', name='Monthly Payment')
    layout = go.Layout(title='Impact of Interest Rate on Monthly Payment',
                       xaxis=dict(title='Interest Rate (%)'),
                       yaxis=dict(title='Monthly Payment (€)'))
    fig = go.Figure(data=[trace], layout=layout)
    # Include Plotly JS from the CDN so the graph renders properly
    div = pyo.plot(fig, output_type='div', include_plotlyjs='cdn')
    return div


def generate_amortization_graph(schedule):
    months = [row['period'] for row in schedule]
    cum_payment = []
    cum_extra = []
    cum_fee = []
    cum_interest = []
    cum_principal = []

    total_payment = total_extra = total_fee = total_interest = total_principal = 0
    remaining_balance = []
    for row in schedule:
        total_payment += row['payment']
        total_extra += row['extra']
        total_fee += row['fee']
        total_interest += row['interest']
        total_principal += row['principal']
        cum_payment.append(total_payment)
        cum_extra.append(total_extra)
        cum_fee.append(total_fee)
        cum_interest.append(total_interest)
        cum_principal.append(total_principal)
        remaining_balance.append(row['balance'])

    traces = [
        go.Scatter(x=months, y=cum_payment, mode='lines+markers',
                   name='Cumulative Payment'),
        go.Scatter(x=months, y=cum_extra, mode='lines+markers',
                   name='Cumulative Extra Payment'),
        go.Scatter(x=months, y=cum_fee, mode='lines+markers',
                   name='Cumulative Extra Fee'),
        go.Scatter(x=months, y=cum_interest, mode='lines+markers',
                   name='Cumulative Interest'),
        go.Scatter(x=months, y=cum_principal, mode='lines+markers',
                   name='Cumulative Principal'),
        go.Scatter(x=months, y=remaining_balance,
                   mode='lines+markers', name='Remaining Balance')
    ]

    layout = go.Layout(title='Amortization Graph (Cumulative Totals & Remaining Balance)',
                       xaxis=dict(title='Period'),
                       yaxis=dict(title='Amount (€)'))
    fig = go.Figure(data=traces, layout=layout)
    div = pyo.plot(fig, output_type='div', include_plotlyjs='cdn')
    return div


@app.route('/', methods=['GET', 'POST'])
def index():
    results = None
    plot_div = None
    amortization_div = None
    field_status = {
        "house_price": "",
        "down_payment": "",
        "loan_term": "",
        "interest_rate": "",
        "monthly_payment": ""
    }
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
        "extra_fee_rate": None,
        "loan_type": "fixed",
        "fixed_period": None,
        "adjusted_interest_rate": None,
        "table_view": "monthly"
    }
    if request.method == 'POST':
        form = request.form
        for key in scenario.keys():
            scenario[key] = form.get(key) if form.get(key) != "" else None

        if form.get("table_view"):
            scenario["table_view"] = form.get("table_view")

        required_fields = ["house_price", "down_payment",
                           "loan_term", "interest_rate", "monthly_payment"]
        missing_fields = []
        for field in required_fields:
            if not form.get(field) or form.get(field).strip() == "":
                missing_fields.append(field)
        if len(missing_fields) == 1:
            for field in required_fields:
                field_status[field] = "green" if field in missing_fields else ""
        elif len(missing_fields) > 0:
            for field in required_fields:
                field_status[field] = "red" if field in missing_fields else ""
        if len(missing_fields) == 0:
            flash("Please leave exactly one required field empty for auto-calculation.")

        action = form.get("action")
        if action == "save":
            scenario_id = str(uuid.uuid4())[:8]
            SCENARIOS[scenario_id] = scenario.copy()
            flash(f"Scenario saved with ID: {scenario_id}")
            return redirect(url_for('index'))
        try:
            unknown_result = solve_for_unknown(form)
        except Exception as e:
            flash(str(e))
            unknown_result = None

        computed_monthly_payment = None
        if unknown_result and unknown_result["calculated_field"] == "monthly_payment":
            computed_monthly_payment = unknown_result["calculated_value"]
            form = request.form.copy()
            form = form.to_dict()
            form["monthly_payment"] = computed_monthly_payment
        else:
            computed_monthly_payment = parse_float(form.get("monthly_payment"))

        schedule, total_interest, total_cost, duration = simulate_amortization(
            form, computed_monthly_payment)
        plot_div = generate_interest_rate_graph(form, computed_monthly_payment)
        amortization_div = generate_amortization_graph(schedule)
        results = {
            "calculated_field": unknown_result["calculated_field"] if unknown_result else "None",
            "calculated_value": unknown_result["calculated_value"] if unknown_result else 0,
            "amortization": schedule,
            "total_interest": total_interest,
            "total_cost": total_cost,
            "duration": duration
        }
    return render_template_string(HTML_TEMPLATE, results=results, plot_div=plot_div, amortization_div=amortization_div, scenario=scenario, saved_scenarios=SCENARIOS, field_status=field_status, table_view=scenario.get("table_view", "monthly"))


@app.route('/load/<scenario_id>')
def load_scenario(scenario_id):
    scenario = SCENARIOS.get(scenario_id)
    if not scenario:
        flash("Scenario not found.")
        return redirect(url_for('index'))
    return render_template_string(HTML_TEMPLATE, results=None, plot_div=None, amortization_div=None, scenario=scenario, saved_scenarios=SCENARIOS, field_status={})


if __name__ == '__main__':
    app.run(debug=True)
    