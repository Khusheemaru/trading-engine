import config
import websocket, json
from strategy import MeanReversionStrategy
import random
from database import DatabaseHandler
import redis

# --- INITIALIZE ---
db = DatabaseHandler()
db.connect()

try:
    r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=config.REDIS_DB)
    print(">> REDIS CONNECTED TO LIVE DASHBOARD FEED")
except Exception as e:
    print(f"!! REDIS ERROR: {e}")

strategies = {
    "FAKEPACA": MeanReversionStrategy("FAKEPACA")
}

def on_open(ws):
    print(">> connection opened")
    auth_data = {
        "action": "auth",
        "key": config.API_KEY,
        "secret": config.SECRET_KEY
    }
    ws.send(json.dumps(auth_data))
    
    # Subscribe to TRADES and BARS
    listen_message = {
        "action": "subscribe",
        "trades": ["FAKEPACA"],
        "bars": ["*"] # This requests the minute candles
    }
    ws.send(json.dumps(listen_message))

def on_message(ws, message):
    data = json.loads(message)

    if isinstance(data, list):
        for item in data:
            
            # --- CASE A: TRADE (Live Price Ticks) ---
            if item.get('T') == 't':
                symbol = item['S']
                price = item['p']

                # 1. Cache to Redis
                try:
                    r.set(f"price:{symbol}", price)
                    # print(f"   [REDIS] Updated {symbol} -> ${price}") 
                except Exception as e:
                    print(f"   [REDIS ERROR] {e}")

                # 2. Strategy Logic
                if symbol in strategies:
                    bot = strategies[symbol]

                    # Simulation Logic
                    if random.randint(1, 100) > 98: # Made crash rarer (2%) so it's less spammy
                        print('   📉 SIMULATING CRASH...')
                        price = price * 0.90

                    decision = bot.on_tick(price)

                    if decision["signal"] != "WAITING_FOR_DATA":
                        if decision["is_hot"]:
                            print(f"🔥 ALERT [{symbol}]: {decision['signal']} @ ${price} (SMA: {decision['sma']})")
                            db.insert_signal(decision['symbol'], decision['signal'], decision['price'], decision['sma'])
                    else:
                        print(f"[{symbol}] WAITING_FOR_DATA ({len(bot.history)}/20)...")

            # --- CASE B: BAR (OHLC Candle Data) ---
            elif item.get('T') == 'b':
                print(f"   [BAR] 📊 New Candle for {item['S']}")
                
                # Fix Timestamp (Remove 'Z' for Postgres)
                raw_time = item['t']
                clean_time = raw_time.replace("Z", "") 

                try:
                    query = """
                        INSERT INTO market_bars (symbol, open, high, low, close, volume, timestamp)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    db.cur.execute(query, (
                        item['S'], item['o'], item['h'], item['l'], item['c'], item['v'], clean_time
                    ))
                    # print("   >> [DB] Saved Bar Successfully")
                except Exception as e:
                    print(f"!! [DB ERROR] Saving Bar: {e}")

socket = 'wss://stream.data.alpaca.markets/v2/test'
ws = websocket.WebSocketApp(socket, on_open=on_open, on_message=on_message)
ws.run_forever()