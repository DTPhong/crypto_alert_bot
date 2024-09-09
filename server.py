import requests
import pandas as pd
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, JobQueue
import os
from flask import Flask

# Token API từ BotFather
TELEGRAM_API_TOKEN = '7380740799:AAG0XNobq3aKbzArXumKQvjhmbW7NRhKtgo'

app = Flask(__name__)

@app.route('/')
def home():
    return 'Bot is running'

# Hàm lấy giá Bitcoin từ CoinGecko API
def get_crypto_price():
    url = 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,binancecoin&vs_currencies=usd,vnd'
    response = requests.get(url).json()
    prices = [
        ['BTC', 'bitcoin', response['bitcoin']['usd'], response['bitcoin']['vnd']],
        ['ETH', 'ethereum', response['ethereum']['usd'], response['ethereum']['vnd']],
        ['BNB', 'binancecoin', response['binancecoin']['usd'], response['binancecoin']['vnd']],
    ]
    return prices

# Hàm lấy dữ liệu lịch sử giá Bitcoin từ CoinGecko API
def get_historical_prices(coinid):
    url = ('https://api.coingecko.com/api/v3/coins/'
           + coinid +
           '/market_chart?vs_currency=usd&days=14&interval=daily')
    response = requests.get(url).json()
    prices = [price[1] for price in response['prices']]
    return prices

# Hàm tính RSI
def calculate_rsi(prices, period=14):
    df = pd.DataFrame(prices, columns=['price'])
    delta = df['price'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

# Hàm xử lý lệnh /price
def price(update: Update, context: CallbackContext):
    prices = get_crypto_price()
    text = (f'Giá crypto hiện tại:')
    for price in prices:
        text += f"\n- {price[0]} price: ${price[2]} \n"
        try:
            prices_history = get_historical_prices(price[1])
            rsi_value = calculate_rsi(prices_history)
            text += f" rsi: {rsi_value:.2f}"
            if rsi_value <= 30:
                text += f" đang nhỏ hơn 30 zo mua liền cho mị"
            if rsi_value >= 80:
                text += f" đang lớn hơn 80 hãy chia nhỏ tiền ra để bán"
        except:
            pass
    update.message.reply_text(text)

def send_price_update(context: CallbackContext):
    job = context.job
    prices = get_crypto_price()
    text = (f'Giá crypto hiện tại:')
    for price in prices:
        text += f"\n{price[0]} price: ${price[2]}"
        try:
            prices_history = get_historical_prices(price[1])
            rsi_value = calculate_rsi(prices_history)
            text += f" rsi: {rsi_value:.2f}"
            if rsi_value <= 30:
                text += f" đang nhỏ hơn 30 zo mua liền cho con @phongdt1008"
            if rsi_value >= 80:
                text += f" đang lớn hơn 80 hãy chia nhỏ tiền ra để bán @phongdt1008"
        except:
            pass
    context.bot.send_message(chat_id=job.context, text=text)

def start(update: Update, context: CallbackContext):
    context.job_queue.run_repeating(send_price_update, interval=3600, first=0, context=update.message.chat_id)
    update.message.reply_text('Bot sẽ gửi cập nhật giá Bitcoin mỗi giờ.')

def main():
    updater = Updater(TELEGRAM_API_TOKEN)
    dp = updater.dispatcher
    jq = updater.job_queue

    dp.add_handler(CommandHandler('price', price))
    dp.add_handler(CommandHandler('start', start, pass_job_queue=True))

    updater.start_polling()
    # updater.idle()
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    main()

