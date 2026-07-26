from flask import Flask, jsonify, render_template_string
from ib_insync import *
import asyncio
import threading
import time
import random
import os

RUN_MAIN = os.environ.get("WERKZEUG_RUN_MAIN") == "true"

app = Flask(__name__)

candles = []
current_candle = None

# =========================================
# Thread مع event loop خاص
# =========================================
def price_updater():
    global current_candle

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    ib = IB()

    client_id = random.randint(1, 9999)
    print("ClientID:", client_id)

    ib.connect('127.0.0.1', 4001, clientId=client_id)

    contract = Stock('AAPL', 'SMART', 'USD')
    ib.qualifyContracts(contract)

    ticker = ticks = ib.reqTickByTickData(contract, "Last", 0, True)

    while True:
        ib.sleep(1)

        if len(ticks) == 0:
           continue

price = ticks[-1].price

        if price is None or price == 0:
            continue

        print("PRICE:", price)

        now = int(time.time())
        minute = now - (now % 60)

        if current_candle is None:
            current_candle = {
                "time": minute,
                "open": price,
                "high": price,
                "low": price,
                "close": price
            }

        elif minute != current_candle["time"]:
            candles.append(current_candle)
            current_candle = {
                "time": minute,
                "open": price,
                "high": price,
                "low": price,
                "close": price
            }

        else:
            current_candle["high"] = max(current_candle["high"], price)
            current_candle["low"] = min(current_candle["low"], price)
            current_candle["close"] = price


# تشغيل الثريد مرة وحدة فقط
if RUN_MAIN:
    threading.Thread(target=price_updater, daemon=True).start()

# =========================================
# API
# =========================================
@app.route("/data")
def data():
    return jsonify(candles[-100:])

# =========================================
# الواجهة (شموع)
# =========================================
@app.route("/")
def index():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
</head>
<body style="background:#111;">

<div id="chart" style="height:600px;"></div>

<script>
const chart = LightweightCharts.createChart(document.getElementById('chart'), {
    layout: { background: { color: '#111' }, textColor: '#DDD' }
});

const candleSeries = chart.addCandlestickSeries();

async function loadData() {
    const res = await fetch('/data');
    const data = await res.json();
    candleSeries.setData(data);
}

setInterval(loadData, 1000);
</script>

</body>
</html>
""")

# =========================================
# تشغيل
# =========================================
if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)
