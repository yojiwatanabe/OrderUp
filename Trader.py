from typing import TypedDict
from xmlrpc.client import Boolean
from CoinbaseAPI import CoinbaseAPI
from mysql import connector
from dotenv import dotenv_values
from datetime import date, datetime
import argparse
import logging
import csv, time

# The order class represents an order and associated actions
class Order(TypedDict):
    marketPair: str
    price: str
    amount: str
    timeCreated: int
    timeExpiry: int


# The OrderUp class is the agent responsible for maintaining and executing orders
class OrderUp():
    def __init__(self) -> None:
        self.orderList = []
        self.coinbaseClient = CoinbaseAPI()
        self.database = self.connectToDb()
        if self.database is not None:
            self.database.autocommit = True # type: ignore
        self.insertOrderBase = """
                        INSERT INTO OrderUpDb.openOrders
                        (timeExpire, marketPair, price, amount)
                        VALUES ("%(timeExpire)s", "%(marketPair)s", %(price)s, %(amount)s)
                        """
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '-d', '--debug',
            help="Print lots of debugging statements",
            action="store_const", dest="loglevel", const=logging.DEBUG,
            default=logging.WARNING,
        )
        parser.add_argument(
            '-v', '--verbose',
            help="Be verbose",
            action="store_const", dest="loglevel", const=logging.INFO,
        )
        args = parser.parse_args()
        logging.basicConfig(level=args.loglevel)

        return

    def __del__(self) -> None: 
        if self.database: self.database.close() 
        return

    def createOrder(self, pair: str, price: str, amount: str, expiry: str) -> None:
        if not self.isDbConnected() or self.database == None:
            print("Failed to create order")
            return
        datetime.utcnow()
        currTime = int(round(time.time() * 1000))
        newOrderValues = {
            "marketPair": pair,
            "timeExpire" : expiry,
            "price": price,
            "amount": amount
        }
        newOrderStatement = self.insertOrderBase % newOrderValues
        
        logging.debug(str(datetime.now()) + "about to execute insert SQL statement")
        logging.info(str(datetime.now())+ "new order:\n" + newOrderStatement)

        dbCursor = self.database.cursor()
        dbCursor.execute(newOrderStatement)

        newOrderValues["id"] = str(dbCursor.lastrowid)
        dbCursor.close()

        self.orderList.append(newOrderValues)
        logging.debug("order created successfully")
        return

    # Runs on startup - checks the DB for open orders and loads them to the local list
    def updateOrders(self, pair: str | None = None) -> None:
        self.isDbConnected()
        return
    
    # Runs on-demand - checks the DB for open orders, reconciliates with the local orders list
    def checkOrders(self, pair: str | None = None):
        # TODO 
        return
    
    # Connect to the MySQL DB and throw an error if not successful
    def connectToDb(self) -> connector.pooling.PooledMySQLConnection | connector.MySQLConnection | None:
        config = dotenv_values(".env")
        db_user = config['DB_USER']
        db_pass = config['DB_PASS']
        
        try:
            database = connector.connect(user=db_user, password=db_pass,
                                host='localhost',
                                database='OrderUpDB')
        except connector.Error as err:
            logging.error("MySQL Connector: something went wrong: {}".format(err))
            return None
        except:
            logging.error("Uncaught error, no connection to DB.")
            return None

        logging.debug(" - - - Connected to DB - - - ")

        return database

    # Returns true if the database is connected, otherwise retry to connect
    def isDbConnected(self) -> Boolean:
        if self.database == None:
            logging.warning("Not connected to DB, trying to reconnect...")
            self.database = self.connectToDb()
            logging.warning("Failed to reconnect, giving up on updating orders.")
            if self.database == None:
                return False

        if ~self.database.is_connected():
            # The client is useless without the DB, keep retrying to connect
            try:
                self.database.reconnect(attempts=10, delay=0)
            except connector.Error as err:
                logging.warning("MySQL Connector: something went wrong: {}".format(err))
                return False
            except:
                logging.warning("Uncaught error, no connection to DB.")
                return False

        if self.database == None:
            return False

        logging.info("Connected to DB")
        return True

    # Fetch market data from Coinbase, export response to a file "markets.csv"
    def exportMarkets(self) -> None:
        marketData = self.coinbaseClient.getMarkets()['products']
        keys = marketData[0].keys()
        with open('markets.csv', 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(marketData)

        return
    


if __name__ == "__main__":
    # exportMarkets(coinbaseClient)
    client = OrderUp()
    # print(traderClient.coinbaseClient.getMarketPrices("BTC-USDC"))
    client.createOrder("BTC-USDC", "30000.00", "1.2345", str(datetime.now()))