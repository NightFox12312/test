##fill in your API keys here to be accessed by other scripts
API_KEY = 'h10P0js0bzg9lW5d1teGdESXWjM2P1qEOFQi2lO3jM7Gj42aczksWIv9s3K5fp4J'
API_SECRET = 'Ef6qW6V3XW3rowd5nEcF1xe7rcWgnJJcDqKwKzNjNzPBSFBz3aJ4sGWItXMPUOfV'

################## settings, these are very strategy dependant ensure you have enough data for your chosen strategy ##################################
order_Size = 5  ## As % of account, i.e 2.5 = 2.5%
leverage = 13
buffer = '8 day ago'  ## Buffer of candle sticks be careful if you don't provide enough the bot will throw an error
Interval = '1m'  ##candle sticks you want to trade
Max_Number_Of_Trades = 8  ## How many positions we can have open at once
use_trailing_stop = 1  ##If on we will use our TP value as the Activation price for a trailing stop loss
trailing_stop_callback = 0.1  ##trailing stop percent, this is .1% range is [.1% - 5%] .ie [0.1 - 5] (increments of .1 only)**
use_market_orders = True
trading_threshold = 0.1  ## %, i.e 0.1 = 0.1%

## New vars needed for the gui, running script from terminal will also need these now
strategy = 'breakout'
TP_SL_choice = 'en'
SL_mult = 6.18
TP_mult = 3.82

##Trade All Coins if True, can also specify a list of coins to trade instead. Example: symbol = ['ETHUSDT','BTCUSDT'] & set Trade_All_Coins = False
Trade_All_Coins = True
symbol = ['AAVEUSDT', 'APEUSDT', 'API3USDT', 'AUDIOUSDT', 'AVAXUSDT', 'AXSUSDT', 'BAKEUSDT', 'DYDXUSDT', 'ENSUSDT', 'LITUSDT', 'NEARUSDT', 'RAYUSDT', 'PEOPLEUSDT', 'RUNEUSDT']  ## If Trade_All_Coins is False then we list the coins we want to trade here, otherwise the bot will automatically get all coins and trade them

