import config
import websocket, json
from strategy import MeanReversionStrategy
import random


# initialize for the stocks
strategies = {
    "FAKEPACA" : MeanReversionStrategy("FAKEPACA")

}



def on_open(ws):
    print("opened")
    auth_data={
        "action": "auth",
        "key": config.API_KEY,
        "secret": config.SECRET_KEY
    }

    ws.send(json.dumps(auth_data))
    listen_message = {"action":"subscribe",
                      "trades": ["FAKEPACA"],
                      "bars": ['*']}
    ws.send(json.dumps(listen_message))

def on_message(ws, message):
    print('received a message')
    print(message)

    data = json.loads(message)

    if isinstance(data, list):
        for trade in data:
            if trade.get('T') == 't':
                symbol = trade['S']
                price = trade['p']

                if symbol in strategies:
                    bot = strategies[symbol]

                    #FOR TESTING

                    if random.randint(1,10) > 8:
                        print('SIMULATING CRASH...')
                        price = price * 0.90
                        decision = bot.on_tick(price)




                    decision = bot.on_tick(price)

                    if decision["signal"] != "WAITING_FOR_DATA":
                        if decision["is_hot"]:
                            print(f"ALERT[{symbol}]: {decision['signal']} @ ${price} (SMA: {decision['sma']})")
                    else:
                        print(f"       [{symbol}] {decision['signal']} .... ")

socket = 'wss://stream.data.alpaca.markets/v2/test'
ws = websocket.WebSocketApp(socket, on_open=on_open, on_message= on_message )

ws.run_forever()

