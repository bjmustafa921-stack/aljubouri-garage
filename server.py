import http.server
import socketserver
import urllib.parse
import datetime
import json
import os

# المنفذ: يقرأ المنفذ تلقائياً عند الرفع للسحاب، أو يستخدم 8000 محلياً
PORT = int(os.environ.get("PORT", 8000))
DATA_FILE = "garage_data.json"

# بيانات الدخول الآمنة
CORRECT_USER = "mustafa_admin"
CORRECT_PASS = "Jubouri#2026@Pass"

TOTAL_CAPACITY = 50
HOURLY_RATE = 2000

is_logged_in = False

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"active_cars": {}, "history": [], "total_revenue": 0}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

db = load_data()

LOGIN_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Al-Jubouri Co. | Operations Portal</title>
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: radial-gradient(circle at top, #1e293b, #0b1329);
            color: #f8fafc;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
        }
        .login-card {
            background: rgba(30, 41, 59, 0.9);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 45px 35px;
            border-radius: 16px;
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.7);
            width: 380px;
            text-align: center;
        }
        .badge {
            display: inline-block;
            background: linear-gradient(135deg, #0284c7, #38bdf8);
            color: #fff;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 2px;
            padding: 5px 14px;
            border-radius: 20px;
            margin-bottom: 12px;
            text-transform: uppercase;
        }
        h1 { font-size: 24px; font-weight: 800; margin: 0 0 5px 0; letter-spacing: 1px; color: #f8fafc; }
        p.sub { font-size: 13px; color: #94a3b8; margin: 0 0 25px 0; }
        .group { text-align: left; margin-bottom: 16px; }
        .group label { display: block; font-size: 12px; color: #94a3b8; margin-bottom: 6px; font-weight: 600; text-transform: uppercase; }
        .group input {
            width: 100%;
            padding: 12px 14px;
            background: #0b1329;
            border: 1px solid #334155;
            border-radius: 8px;
            color: #fff;
            font-size: 14px;
            outline: none;
        }
        .group input:focus { border-color: #38bdf8; }
        .btn-auth {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 15px;
            font-weight: 700;
            cursor: pointer;
            margin-top: 10px;
        }
        .alert-err {
            background: rgba(239, 68, 68, 0.2);
            border: 1px solid #ef4444;
            color: #fca5a5;
            padding: 10px;
            border-radius: 8px;
            font-size: 13px;
            margin-top: 15px;
        }
    </style>
</head>
<body>
    <div class="login-card">
        <span class="badge">Enterprise Suite</span>
        <h1>AL-JUBOURI CO.</h1>
        <p class="sub">Intelligent Garage Management Platform</p>
        <form method="POST">
            <input type="hidden" name="action" value="login">
            <div class="group">
                <label>Operator Username</label>
                <input type="text" name="username" placeholder="mustafa_admin" required>
            </div>
            <div class="group">
                <label>Security Key</label>
                <input type="password" name="password" placeholder="••••••••" required>
            </div>
            <button type="submit" class="btn-auth">System Login</button>
        </form>
        {login_alert}
    </div>
</body>
</html>
"""

DASHBOARD_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Al-Jubouri Co. | Operations Dashboard</title>
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #0b1329;
            color: #f8fafc;
            margin: 0;
            padding: 0;
        }
        .navbar {
            background: #111e38;
            border-bottom: 1px solid #1e293b;
            padding: 16px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .nav-brand { font-size: 18px; font-weight: 800; color: #38bdf8; letter-spacing: 1px; }
        .user-tag { background: #1e293b; padding: 6px 14px; border-radius: 20px; font-size: 13px; color: #cbd5e1; }
        .logout { color: #ef4444; text-decoration: none; font-size: 13px; font-weight: 600; margin-left: 15px; }

        .container { max-width: 1100px; margin: 30px auto; padding: 0 20px; }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 25px;
        }
        .stat-card {
            background: #15223e;
            border: 1px solid #20335e;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }
        .stat-title { font-size: 12px; color: #94a3b8; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px; }
        .stat-value { font-size: 26px; font-weight: 800; margin-top: 8px; color: #38bdf8; }

        .layout { display: grid; grid-template-columns: 340px 1fr; gap: 24px; }
        .panel {
            background: #15223e;
            border: 1px solid #20335e;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }
        h2 { font-size: 16px; margin: 0 0 16px 0; color: #f1f5f9; border-bottom: 1px solid #20335e; padding-bottom: 10px; }
        .input-control {
            width: 100%;
            padding: 12px;
            background: #0b1329;
            border: 1px solid #20335e;
            border-radius: 8px;
            color: #fff;
            margin-bottom: 12px;
            font-size: 14px;
            outline: none;
        }
        .btn-in {
            width: 100%;
            padding: 12px;
            background: #10b981;
            color: #fff;
            border: none;
            border-radius: 8px;
            font-weight: 700;
            cursor: pointer;
            font-size: 14px;
        }
        .btn-in:hover { background: #059669; }

        table { width: 100%; border-collapse: collapse; margin-top: 5px; }
        th, td { padding: 12px 10px; text-align: left; border-bottom: 1px solid #20335e; font-size: 13px; }
        th { color: #94a3b8; font-size: 11px; text-transform: uppercase; font-weight: 600; }
        .btn-out {
            background: #ef4444;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 11px;
            font-weight: bold;
        }
        .btn-out:hover { background: #dc2626; }

        .alert-box {
            padding: 14px 18px;
            background: #1b2f56;
            border-left: 4px solid #38bdf8;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
        }

        .receipt-card {
            background: #1b382b;
            border: 1px solid #10b981;
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .print-btn {
            background: #10b981;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: bold;
            cursor: pointer;
        }
    </style>
</head>
<body>

    <div class="navbar">
        <div class="nav-brand">AL-JUBOURI CO. <span style="font-size: 13px; color: #64748b; font-weight: normal;">| Control Center</span></div>
        <div>
            <span class="user-tag">Operator: mustafa_admin</span>
            <a href="/logout" class="logout">Sign Out</a>
        </div>
    </div>

    <div class="container">
        {action_alert}

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-title">Available Slots</div>
                <div class="stat-value" style="color: #4ade80;">{available_slots} / {total_capacity}</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">Active Vehicles</div>
                <div class="stat-value">{active_count}</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">Today's Revenue</div>
                <div class="stat-value" style="color: #fbbf24;">{revenue} IQD</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">Completed Check-Outs</div>
                <div class="stat-value" style="color: #a78bfa;">{total_exits}</div>
            </div>
        </div>

        <div class="layout">
            <div class="panel">
                <h2>New Vehicle Check-In</h2>
                <form method="POST">
                    <input type="hidden" name="action" value="checkin">
                    <label style="font-size:12px; color:#94a3b8; display:block; margin-bottom:5px;">Vehicle Plate Number</label>
                    <input type="text" name="car_plate" class="input-control" placeholder="e.g. 5421" required autofocus>
                    <button type="submit" class="btn-in">+ Check-In Vehicle</button>
                </form>
            </div>

            <div class="panel">
                <h2>Active Parking Registry ({active_count})</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Plate</th>
                            <th>Entry Time</th>
                            <th>Duration</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {active_rows}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

</body>
</html>
"""

class SmartGarageHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        global is_logged_in
        if self.path == "/logout":
            is_logged_in = False
            self.send_response(302)
            self.send_header("Location", "/")
            self.end_headers()
            return

        if not is_logged_in:
            self.send_page(LOGIN_PAGE.replace("{login_alert}", ""))
        else:
            self.render_dashboard()

    def do_POST(self):
        global is_logged_in, db
        length = int(self.headers.get('content-length', 0))
        post_data = self.rfile.read(length).decode('utf-8')
        params = urllib.parse.parse_qs(post_data)
        action = params.get('action', [''])[0]

        if action == "login":
            user = params.get('username', [''])[0]
            pwd = params.get('password', [''])[0]
            if user == CORRECT_USER and pwd == CORRECT_PASS:
                is_logged_in = True
                self.render_dashboard()
            else:
                alert = "<div class='alert-err'>Invalid Operator Username or Security Key</div>"
                self.send_page(LOGIN_PAGE.replace("{login_alert}", alert))

        elif action == "checkin" and is_logged_in:
            plate = params.get('car_plate', [''])[0].strip().upper()
            if len(db["active_cars"]) >= TOTAL_CAPACITY:
                alert = "<div class='alert-box' style='border-color:#ef4444;'>Garage is full! No slots available.</div>"
            elif plate in db["active_cars"]:
                alert = f"<div class='alert-box' style='border-color:#ef4444;'>Plate #{plate} is already registered inside!</div>"
            else:
                now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                db["active_cars"][plate] = now_str
                save_data(db)
                alert = f"<div class='alert-box'>Vehicle <b>#{plate}</b> registered at {now_str[11:]}. Ticket issued successfully!</div>"
            self.render_dashboard(alert)

        elif action == "checkout" and is_logged_in:
            plate = params.get('car_plate', [''])[0].strip().upper()
            if plate in db["active_cars"]:
                entry_dt = datetime.datetime.strptime(db["active_cars"][plate], "%Y-%m-%d %H:%M:%S")
                exit_dt = datetime.datetime.now()
                total_sec = max(1, (exit_dt - entry_dt).total_seconds())
                hours = max(1, int(total_sec // 3600) + (1 if total_sec % 3600 > 0 else 0))
                cost = hours * HOURLY_RATE

                db["total_revenue"] += cost
                db["history"].append({
                    "plate": plate,
                    "entry": db["active_cars"][plate],
                    "exit": exit_dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "amount": cost
                })
                del db["active_cars"][plate]
                save_data(db)

                receipt = f"""
                <div class="receipt-card">
                    <div>
                        <b style="font-size:16px;">Invoice Generated for Vehicle #{plate}</b><br>
                        <span style="font-size:13px; color:#cbd5e1;">Duration: {int(total_sec // 60)} mins ({hours} Billed Hours) &bull; Total: <b style="color:#4ade80;">{cost:,} IQD</b></span>
                    </div>
                    <button class="print-btn" onclick="window.print()">Print Receipt</button>
                </div>
                """
                self.render_dashboard(receipt)
            else:
                self.render_dashboard()

    def render_dashboard(self, alert=""):
        now = datetime.datetime.now()
        rows = ""
        for plate, entry_time_str in db["active_cars"].items():
            entry_dt = datetime.datetime.strptime(entry_time_str, "%Y-%m-%d %H:%M:%S")
            diff_min = int((now - entry_dt).total_seconds() // 60)
            rows += f"""
            <tr>
                <td><b style="color:#38bdf8; font-size:14px;">#{plate}</b></td>
                <td>{entry_time_str[11:]}</td>
                <td>{diff_min} mins</td>
                <td>
                    <form method="POST" style="margin:0;">
                        <input type="hidden" name="action" value="checkout">
                        <input type="hidden" name="car_plate" value="{plate}">
                        <button type="submit" class="btn-out">Check-Out</button>
                    </form>
                </td>
            </tr>
            """
        if not db["active_cars"]:
            rows = "<tr><td colspan='4' style='text-align:center; color:#64748b; padding:24px;'>No active vehicles inside. Available slots ready.</td></tr>"

        active_count = len(db["active_cars"])
        available_slots = max(0, TOTAL_CAPACITY - active_count)

        html = DASHBOARD_PAGE.replace("{action_alert}", alert)
        html = html.replace("{available_slots}", str(available_slots))
        html = html.replace("{total_capacity}", str(TOTAL_CAPACITY))
        html = html.replace("{active_count}", str(active_count))
        html = html.replace("{revenue}", f"{db['total_revenue']:,}")
        html = html.replace("{total_exits}", str(len(db["history"])))
        html = html.replace("{active_rows}", rows)

        self.send_page(html)

    def send_page(self, content):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

print(f"Al-Jubouri Co. Live on port {PORT}")
with socketserver.TCPServer(("", PORT), SmartGarageHandler) as httpd:
    httpd.serve_forever()