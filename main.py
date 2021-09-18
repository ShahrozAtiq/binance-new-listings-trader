import requests
import time
import hmac
import hashlib

# Set up the API endpoints for Binance and Gate.io
binance_api_endpoint = 'https://api.binance.com/api/v3'
gateio_api_endpoint = 'https://api.gateio.ws/api/v4'

# Set up your API keys and other credentials for Binance and Gate.io
binance_api_key = 'YOUR_BINANCE_API_KEY'
binance_api_secret = 'YOUR_BINANCE_API_SECRET'
gateio_api_key = 'YOUR_GATEIO_API_KEY'
gateio_api_secret = 'YOUR_GATEIO_API_SECRET'

# Set up a list to store the symbols of new listings
new_listings = []

while True:
    # Make a request to Binance's API to get the latest listings
    response = requests.get(f'{binance_api_endpoint}/exchange-api/v1/public/asset-service/product/get-products')

    # If the request is successful, parse the response for new listings
    if response.status_code == 200:
        data = response.json()
        for product in data['data']:
            if product['newListing'] == True and product['symbol'] not in new_listings:
                new_listings.append(product['symbol'])
                print(f'New listing detected on Binance: {product["symbol"]}')
                # Query the Gate.io API to check if the new listing is available on the exchange
                gateio_response = requests.get(f'{gateio_api_endpoint}/spot/currency_pairs')
                if gateio_response.status_code == 200:
                    gateio_data = gateio_response.json()
                    for currency_pair in gateio_data:
                        if currency_pair['id'] == product['symbol'].replace('_', '').lower():
                            # Calculate the amount of the new token to buy based on your available balance
                            binance_account_response = requests.get(f'{binance_api_endpoint}/account',
                                                                     headers={'X-MBX-APIKEY': binance_api_key},
                                                                     params={'timestamp': int(time.time() * 1000)},
                                                                     data={'recvWindow': 5000})
                            if binance_account_response.status_code == 200:
                                binance_account_data = binance_account_response.json()
                                for balance in binance_account_data['balances']:
                                    if balance['asset'] == currency_pair['base']:
                                        amount_to_buy = float(balance['free']) * 0.9 / float(currency_pair['rate'])

                                        # Place a buy order on Gate.io for the new token
                                        nonce = int(time.time() * 1000)
                                        signature = hmac.new(gateio_api_secret.encode('utf-8'),
                                                             f'{nonce}POST/api/v4/spot/orders'.encode('utf-8'),
                                                             hashlib.sha512).hexdigest()
                                        headers = {'API-Key': gateio_api_key, 'API-Signature': signature,
                                                   'Content-Type': 'application/json'}
                                        data = {'currency_pair': currency_pair['id'],
                                                'type': 'buy',
                                                'amount': amount_to_buy,
                                                'price': currency_pair['rate']}
                                        gateio_order_response = requests.post(f'{gateio_api_endpoint}/spot/orders',
                                                                             headers=headers,
                                                                             json=data,
                                                                             params={'timestamp': nonce})
                                        if gateio_order_response.status_code == 200:
                                            print(f'Buy order placed on Gate.io for {amount_to_buy} {currency_pair["base"]} at {currency_pair["rate"]} {currency_pair["quote"]}')
                                        else:
                                            print(f'Error placing buy order on Gate.io: {gateio_order_response.text}')
                               
