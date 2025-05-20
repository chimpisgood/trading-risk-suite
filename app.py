from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # change this in production

DATA_FILE = 'data.json'
USERNAME = 'partner'
PASSWORD = 'securepassword'

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"daily_loss_limit": 500, "max_contracts": 5, "intra_day_drawdown": 300}
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == USERNAME and request.form['password'] == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    data = load_data()
    if request.method == 'POST':
        data['daily_loss_limit'] = float(request.form['daily_loss_limit'])
        data['max_contracts'] = int(request.form['max_contracts'])
        data['intra_day_drawdown'] = float(request.form['intra_day_drawdown'])
        save_data(data)
    return render_template('dashboard.html', data=data)

@app.route('/api/check-risk')
def check_risk():
    data = load_data()
    return jsonify(data)

@app.route('/api/validate-trade', methods=['POST'])
def validate_trade():
    data = load_data()
    req = request.get_json()

    # Expected: {"contracts": 3, "loss_today": 250, "drawdown": 180}
    contracts = req.get('contracts', 0)
    loss_today = req.get('loss_today', 0)
    drawdown = req.get('drawdown', 0)

    if contracts > data['max_contracts']:
        return jsonify({"allowed": False, "reason": "Contract size exceeds limit"})
    if loss_today > data['daily_loss_limit']:
        return jsonify({"allowed": False, "reason": "Daily loss limit exceeded"})
    if drawdown > data['intra_day_drawdown']:
        return jsonify({"allowed": False, "reason": "Intra-day drawdown limit exceeded"})

    return jsonify({"allowed": True})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

