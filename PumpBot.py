from binance.client import Client
from binance.enums import *
import math
import json

def float_to_string(number, precision=10):
    return '{0:.{prec}f}'.format(
        number, prec=precision,
    ).rstrip('0').rstrip('.') or '0'

# read json file
f = open('config.json',)
data = json.load(f)
apiKey = data['apiKey']
apiSecret = data['apiSecret']
profitMargin = float(data['profitMargin']) / 100
percentOfWallet = float(data['percentOfWallet']) / 100
buyLimit = data['buyLimit']
stopLoss = data['stopLoss']
coinPair = data['coinPair']
client = Client(apiKey, apiSecret)

# find amount of bitcoin to use
BTCBalance = float(client.get_asset_balance(asset='BTC')['free'])
BTCtoSell = BTCBalance * percentOfWallet
# nice user message
print(''' ___                                ___           _   
(  _`\                             (  _`\        ( )_ 
| |_) ) _   _   ___ ___   _ _      | (_) )   _   | ,_)
| ,__/'( ) ( )/' _ ` _ `\( '_`\    |  _ <' /'_`\ | |  
| |    | (_) || ( ) ( ) || (_) )   | (_) )( (_) )| |_ 
(_)    `\___/'(_) (_) (_)| ,__/'   (____/'`\___/'`\__)
                         | |                          
                         (_)                          ''')
# wait until coin input
tradingPair = input("Coin pair: ").upper() + coinPair

# get trading pair price
price = float(client.get_avg_price(symbol=tradingPair)['price'])
# calculate amount of coin to buy
amountOfCoin = BTCtoSell / price;

# rounding the coin to the specified lot size
info = client.get_symbol_info(tradingPair)
minQty = float(info['filters'][2]['minQty'])
amountOfCoin = float_to_string(amountOfCoin, int(- math.log10(minQty)))

# ensure buy limit is setup correctly
# find average price in last 30 mins
agg_trades = client.aggregate_trade_iter(symbol=tradingPair, start_str='30 minutes ago UTC')
agg_trade_list = list(agg_trades)
total = 0
for trade in agg_trade_list:
    fvalue = float(trade['p'])
    total = total + fvalue
averagePrice = total / len(agg_trade_list)
minPrice = minQty = float(info['filters'][0]['minPrice'])
averagePrice = float(averagePrice) * buyLimit
averagePrice = float_to_string(averagePrice, int(- math.log10(minPrice)))

# buy order
order = client.order_limit_buy(
    symbol=tradingPair, 
    quantity=amountOfCoin,
    price=averagePrice)
print('Buy order has been made!')
coinOrderInfo           = order["fills"][0]
coinPriceBought         = float(coinOrderInfo['price'])
coinOrderQty            = float(coinOrderInfo['qty'])

# rounding sell price to correct dp
priceToSell = coinPriceBought * profitMargin
roundedPriceToSell = float_to_string(priceToSell, int(- math.log10(minPrice)))

# waits until the buy order has been confirmed 
orders = client.get_open_orders(symbol=tradingPair)
while (client.get_open_orders(symbol=tradingPair) != []):
    print("Waiting for coin to buy...")

# oco order (with stop loss)
order = client.create_oco_order(
    symbol=tradingPair,
    quantity=coinOrderQty,
    side = SIDE_SELL,
    price = roundedPriceToSell,
    stopPrice = float_to_string(stopLoss * coinPriceBought, int(- math.log10(minPrice))),
    stopLimitPrice = float_to_string(stopLoss * coinPriceBought, int(- math.log10(minPrice))),
    stopLimitTimeInForce = TIME_IN_FORCE_GTC
    )
print('Sell order has been made!')