# OrderUp Database

The database will be configured locally and only accessible locally. To use a cloud DB, change the `DB_HOST` value in `.env` to point to your SQL server and ensure permissions are in place (note: OrderUp was built to run locally, use with a cloud DB at your own risk).

## Schema

### openOrders

`OrderUp.openOrders` holds only open and active orders. Expired orders are moved to the `closedOrders` table to keep `openOrders` to maximize speed.

| Field name     | Type        | Explanation                                   |
| -------------- | ----------- | --------------------------------------------- |
| `timeCreated`  | DATETIME(3) | UNIX time in ms, auto-set on row creation     |
| `timeExpire`   | DATETIME(3) | UNIX time in ms                               |
| `marketPair`   | VARCHAR(8)  | Matches Coinbase pair (e.g. BTC-USDC)         |
| `price`        | FLOAT(64)   | In native pair format                         |
| `amount`       | FLOAT(32)   | In native pair format                         |
| `lastModified` | DATETIME(3) | UNIX time in ms, auto-set on row modification |

#### Routines

**CloseOrders** - A routine that triggers after every read to close any orders where `currTime > timeExpire`.

### closedOrders

`OrderUp.closedOrders` holds all orders made inactive for whatever reason, e.g. 100% executed, expired, etc.. The schema is identical to that of `openOrders`.
| Field name    | Type        | Explanation                               |
| ------------- | ----------- | ----------------------------------------- |
| `timeCreated` | DATETIME(3) | UNIX time in ms, auto-set on row creation |
| `timeExpire`  | DATETIME(3) | UNIX time in ms                           |
| `marketPair`  | VARCHAR(8)  | Matches Coinbase pair (e.g. BTC-USDC)     |
| `price`       | FLOAT(64)   | In native pair format                     |
| `amount`      | FLOAT(32)   | In native pair format                     |

## Database User - OUAdmin

OrderUp DB Privileges:
    - SELECT        # Query orders, prices
    - INSERT        # Create orders, price data
    - UPDATE        # Update orders
    - DELETE        # Delete orders
    - EXECUTE       # Run routines
    - EVENT         # Run events
    - TRIGGER       # Run triggers

Global Privileges:
    - SHUTDOWN      # Shut down MySQL on shutdown
    - PROCESS       # Monitor ongoing queries
    - FILE          # Export data

## Setup

1. Create the `OrderUp` database, switch to it:

    ```sql
    CREATE DATABASE OrderUp;
    ```

2. Create the OUAdmin user and set privileges to `OrderUp` and global DBs:

    ```sql
    CREATE USER 'OUAdmin'@'localhost' IDENTIFIED BY 'password';
    ```

    ```sql
    GRANT SELECT, INSERT, UPDATE, DELETE, EXECUTE, EVENT, TRIGGER 
    ON OrderUp.* 
    TO 'OUAdmin'@'localhost';
    ```

    ```sql
    GRANT SHUTDOWN, PROCESS, FILE
    ON *.* 
    TO 'OUAdmin'@'localhost';
    ```

3. Create the `openOrders` and `closedOrders` tables

   ```sql
    CREATE TABLE openOrders (
        id int unsigned AUTO_INCREMENT,
        timeCreated TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP(3),
        timeExpire TIMESTAMP(3),
        marketPair VARCHAR(16),
        price FLOAT(53),
        amount FLOAT(53),
        processing BOOLEAN DEFAULT FALSE,
        lastModified TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id)
    ) CHARSET=utf8 AUTO_INCREMENT=1;
    ```

    ```sql
    CREATE TABLE closedOrders (
        id int unsigned AUTO_INCREMENT,
        openOrderId int unsigned,
        timeCreated TIMESTAMP(3),
        timeExpire TIMESTAMP(3),
        expiryReason ENUM('COMPLETED', 'FAILED', 'TIMEOUT', 'CANCELLED'),
        marketPair VARCHAR(16),
        price FLOAT(53),
        amount FLOAT(53),
        lastModified TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id)
    ) CHARSET=utf8 AUTO_INCREMENT=1;
   ```

4. Test the DB connection using `OrderUp` Python class
5. Set the DB variables in `.env` (create a `.env` file if it doesn't exist)

   ```text
   ... .env contents
   DB_NAME=OrderUp
   DB_USER=OUAdmin
   DB_PASS=<PASSWORD_FROM_STEP_2>
   ```
