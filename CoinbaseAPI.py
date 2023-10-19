from dotenv import dotenv_values
import http.client, time, json, hmac, hashlib
import argparse
import logging


class CoinbaseAPI:
    def __init__(self):
        config = dotenv_values(".env")

        self.conn = http.client.HTTPSConnection("api.coinbase.com")
        self.apiKey = config['CB_API_KEY']
        self.apiSecret = config['CB_API_SECRET']

        parser = argparse.ArgumentParser()
        parser.add_argument(
            '-d', '--debug',
            help="Print debugging statements",
            action="store_const", dest="loglevel", const=logging.DEBUG,
            default=logging.WARNING,
        )
        parser.add_argument(
            '-v', '--verbose',
            help="Print verbosely",
            action="store_const", dest="loglevel", const=logging.INFO,
        )
        args = parser.parse_args()
        logging.basicConfig(level=args.loglevel)

        
        logging.info(" - - - Coinbase Client Ready - - - ")

    def getOpenOrders(self):
        method = "GET"
        path = "/api/v3/brokerage/orders/historical/batch"
        params = "?order_status=OPEN"
        payload = ""
        return self.sendRequest(method, path, params, payload)

    def getAccounts(self):
        method = "GET"
        path = "/api/v3/brokerage/accounts"
        params = ""
        payload = ""
        return self.sendRequest(method, path, params, payload)

    def getMarketPrices (self, market: str):
        method = "GET"
        path = "/api/v3/brokerage/best_bid_ask"
        params = "?product_ids=" + market
        payload = ""
        return self.sendRequest(method, path, params, payload)
    
    def getMarkets (self):
        method = "GET"
        path = "/api/v3/brokerage/products"
        params = ""
        payload = ""
        return self.sendRequest(method, path, params, payload)

    def sendRequest(self, method: str, path: str, params: str, payload: str):
        signedHeaders = self.getSignedHeader(method, path, payload)
        self.conn.request("GET", path + params, payload, signedHeaders)
        res = self.conn.getresponse()
        data = res.read()
        return json.loads(data.decode('utf-8'))

    def getSignedHeader(self, method: str, requestPath: str, body: str):
        if self.apiKey is None or self.apiSecret is None:
            print(" - - - Can't sign header - - - ")
            return {}
        currTime = int(time.time()) # Get unix time
        sigString = str(currTime) + method + requestPath + body
        signature = hmac.new(self.apiSecret.encode('utf-8'), sigString.encode('utf-8'), digestmod=hashlib.sha256).digest()
        headers = {
            "Content-Type": "application/json",
            "CB-ACCESS-KEY": self.apiKey,
            "CB-ACCESS-SIGN": signature.hex(),
            "CB-ACCESS-TIMESTAMP": currTime
        }

        return headers
