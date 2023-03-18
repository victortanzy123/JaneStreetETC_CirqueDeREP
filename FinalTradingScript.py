

#!/usr/bin/python
# ~~~~~==============   HOW TO RUN   ==============~~~~~
# 1) Configure things in CONFIGURATION section
# 2) Change permissions: chmod +x bot.py
# 3) Run in loop: while true; do ./bot.py; sleep 1; done

from __future__ import print_function
import time
import sys
import socket
import json

# ~~~~~============== CONFIGURATION  ==============~~~~~
# replace REPLACEME with your team name!
team_name = "CIRQUEDEREP"
# This variable dictates whether or not the bot is connecting to the prod
# or test exchange. Be careful with this switch!
test_mode = True

# This setting changes which test exchange is connected to.
# 0 is prod-like
# 1 is slower
# 2 is empty
test_exchange_index = 0
prod_exchange_hostname = "production"

port = 25000 + (test_exchange_index if test_mode else 0)
exchange_hostname = "test-exch-" + \
    team_name if test_mode else prod_exchange_hostname

# declare global variables for ticker price history and order id storage
valbz = []
vale = []
xlf = []
bond = []
gs = []
ms = []
wfc = []
orderid = 0
marketServerStatus = 1

# ~~~~~============== NETWORKING CODE ==============~~~~~


def connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((exchange_hostname, port))
    return s.makefile("rw", 1)


def write_to_exchange(exchange, obj):
    json.dump(obj, exchange)
    exchange.write("\n")


def read_from_exchange(exchange):
    return json.loads(exchange.readline())


def mean(l):
    return sum(l)//len(l)


def XLVSignal(XLVPrice, BondPrice, GSPrice, MSPrice, WFCPrice):

    gap = 30
    width = -1

    XLVMean = mean(XLVPrice[width:])
    bondMean = mean(BondPrice[width:])
    gsMean = mean(GSPrice[width:])
    msMean = mean(MSPrice[width:])
    wfcMean = mean(WFCPrice[width:])

    fairValue = (3*bondMean + 2*gsMean + 3*msMean + 2*wfcMean)/10

    if (fairValue - gap) > XLVMean:
        # print("Fairvalue: %d  -- Mean: %d -- LONG\n", fairValue, XLVMean)
        return ["long", XLVMean, bondMean, gsMean, msMean, wfcMean]
    elif (fairValue + gap) < XLVMean:
        # print("Fairvalue: %d  -- Mean: %d -- SHORT\n", fairValue, XLVMean)
        return ["short", XLVMean, bondMean, gsMean, msMean, wfcMean]
    else:
        return ["null", XLVMean, bondMean, gsMean, msMean, wfcMean]

# ~~~~~============== MAIN LOOP ==============~~~~~


def mainFunction(marketInfo):
    global marketServerStatus
    if (marketInfo["symbol"] == "BOND"):
        bond.append(marketInfo["price"])

    if(marketInfo["symbol"] == "VALBZ"):
        valbz.append(marketInfo["price"])

    if(marketInfo["symbol"] == "VALE"):
        vale.append(marketInfo["price"])

    if (marketInfo["symbol"] == "XLF"):
        xlf.append(marketInfo["price"])

    if (marketInfo["symbol"] == "GS"):
        gs.append(marketInfo["price"])

    if (marketInfo["symbol"] == "MS"):
        ms.append(marketInfo["price"])

    if (marketInfo["symbol"] == "WFC"):
        wfc.append(marketInfo["price"])


def ADRTrade(exchange, valePrice, valbzPrice):
    global orderid
    if (mean(valePrice) - mean(valbzPrice) > 10):
        # create liquidity
        # buy valbz
        orderid += 1
        write_to_exchange(exchange, {"type": "add", "order_id": orderid, "symbol": "VALBZ", "dir": "BUY",
                                     "price": mean(valbzPrice)+1, "size": 10})
        # convert underlying asset
        orderid += 1
        write_to_exchange(exchange, {"type": "convert", "order_id": orderid, "symbol": "VALE", "dir": "BUY",
                                     "size": 10})
        # sell vale
        orderid += 1
        write_to_exchange(exchange, {"type": "add", "order_id": orderid, "symbol": "VALE", "dir": "SELL",
                                     "price": mean(valePrice)-1, "size": 10})
    else:
        orderid += 1
        write_to_exchange(exchange, {"type": "add", "order_id": orderid, "symbol": "VALE", "dir": "BUY",
                                     "price": mean(valePrice) + 1, "size": 10})
        orderid += 1
        write_to_exchange(exchange, {"type": "convert", "order_id": orderid, "symbol": "VALBZ", "dir": "BUY",
                                     "size": 10})
        # sell vale
        orderid += 1
        write_to_exchange(exchange, {"type": "add", "order_id": orderid, "symbol": "VALBZ", "dir": "SELL",
                                     "price": mean(valbzPrice) - 1, "size": 10})


def bondTrading(exchange):
    global orderid
    orderid += 1
    write_to_exchange(exchange, {"type": "add", "order_id": orderid, "symbol": "BOND", "dir": "BUY",
                                 "price": 999, "size": 10})

    write_to_exchange(exchange, {"type": "add", "order_id": orderid, "symbol": "BOND", "dir": "SELL",
                                 "price": 1001, "size": 10})


def XLVTrading(exchange):
    global orderid
    XLVStuff = XLVSignal(xlf, bond, gs, ms, wfc)
    if(XLVStuff[0] == 'long'):
        orderid += 1
        write_to_exchange(exchange, {"type": "add", "order_id": orderid, "symbol": "XLF", "dir": "BUY",
                                     "price": XLVStuff[1], "size": 500})
        orderid += 1
        write_to_exchange(exchange, {
                          "type": "convert", "order_id": orderid, "symbol": "XLF", "dir": "SELL", "size": 500})

        orderid += 1

        write_to_exchange(exchange, {"type": "add", "order_id": orderid, "symbol": "BOND", "dir": "SELL",
                                     "price": XLVStuff[2], "size": 150})
        orderid += 1
        write_to_exchange(exchange, {"type": "add", "order_id": orderid, "symbol": "GS", "dir": "SELL",
                                     "price": XLVStuff[3], "size": 100})
        orderid += 1
        write_to_exchange(exchange, {"type": "add", "order_id": orderid, "symbol": "MS", "dir": "SELL",
                                     "price": XLVStuff[4], "size": 150})
        orderid += 1
        write_to_exchange(exchange, {"type": "add", "order_id": orderid, "symbol": "WFC", "dir": "SELL",
                                     "price": XLVStuff[5], "size": 100})

    if(XLVStuff[0] == 'short'):

        orderid += 1

        write_to_exchange(exchange, {"type": "add", "order_id": orderid, "symbol": "BOND", "dir": "BUY",
                                     "price": XLVStuff[2], "size": 150})
        orderid += 1
        write_to_exchange(exchange, {"type": "add", "order_id": orderid, "symbol": "GS", "dir": "BUY",
                                     "price": XLVStuff[3], "size": 100})
        orderid += 1
        write_to_exchange(exchange, {"type": "add", "order_id": orderid, "symbol": "MS", "dir": "BUY",
                                     "price": XLVStuff[4], "size": 150})
        orderid += 1
        write_to_exchange(exchange, {"type": "add", "order_id": orderid, "symbol": "WFC", "dir": "BUY",
                                     "price": XLVStuff[5], "size": 100})

        orderid += 1
        write_to_exchange(exchange, {
                          "type": "convert", "order_id": orderid, "symbol": "XLF", "dir": "BUY", "size": 500})
        orderid += 1
        write_to_exchange(exchange, {"type": "add", "order_id": orderid, "symbol": "XLF", "dir": "SELL",
                                     "price": XLVStuff[1], "size": 500})


def main():
    global orderid
    exchange = connect()
    write_to_exchange(exchange, {"type": "hello", "team": team_name.upper()})
    hello_from_exchange = read_from_exchange(exchange)
    # A common mistake people make is to call write_to_exchange() > 1
    # time for every read_from_exchange() response.
    # Since many write messages generate marketdata, this will cause an
    # exponential explosion in pending messages. Please, don't do that!
    print("The exchange replied:", hello_from_exchange, file=sys.stderr)
    while True:
        message = read_from_exchange(exchange)
        print(message)
        if message["type"] == "close":
            print("The round has ended")
            break
        if message['type'] == 'trade':
            mainFunction(message)
            bondTrading(exchange)
            if(message['symbol'] in ['XLF', 'WFC', 'MS', 'GS', 'BOND']):
                if(len(bond) > 5 and len(ms) > 5 and len(wfc) > 5 and len(gs) > 5 and len(xlf) > 5):
                    XLVTrading(exchange)
            if(len(valbz) >= 10 and len(vale) >= 10):
                ADRTrade(exchange, vale[-10:], valbz[-10:])

        time.sleep(0.01)


if __name__ == "__main__":
    main()
