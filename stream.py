import config
import websocket, json

def on_open(ws):
    print("opened")
    auth_data={
        "action": "auth",
        "key": config.API_KEY,
        "secret": config.SECRET_KEY
    }

    ws.send(json.dumps(auth_data))
    listen_message = {"action":"subscribe",
                      "trades": ["AAPL","TSLA","MSFT","NVDA"]}
    ws.send(json.dumps(listen_message))
def on_message(ws, message):
    print('received a message')
    print(message)

socket = 'wss://stream.data.alpaca.markets/v2/iex'
ws = websocket.WebSocketApp(socket, on_open=on_open, on_message= on_message )

ws.run_forever()

