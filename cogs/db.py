import sqlite3

import cogs.config as config

conn = sqlite3.connect(config.DATABASE_NAME)

def initializeDB():
    conn.execute('''CREATE TABLE IF NOT EXISTS TRADES
                 (DISCORD_ID TEXT PRIMARY KEY NOT NULL,
                 TICKER TEXT,
                 PRICE TEXT,
                 LEVERAGE TEXT,
                 TYPE TEXT,
                 TP TEXT,
                 SL TEXT,
                 GAIN TEXT,
                 STATUS TEXT);''') # 1 for trade closed, 0 for trade open

    conn.execute('''CREATE TABLE IF NOT EXISTS LIMIT_ORDERS
                 (DISCORD_ID TEXT PRIMARY KEY NOT NULL,
                 TICKET TEXT,
                 LEVERAGE TEXT,
                 TYPE TEXT,
                 ENTRY TEXT,
                 TP TEXT,
                 SL TEXT,
                 STATUS TEXT,
                 ENTRY TEXT);''') # 1 for order placed, 0 for order not placed yet

    conn.commit()

def insert_trade(discord_id, ticker, price, leverage, type, tp, sl):
    sqlite_insert_with_param = """INSERT OR REPLACE INTO 'TRADES'
    ('DISCORD_ID', 'TICKET', 'PRICE', 'LEVERAGE', 'TYPE', 'TP', 'SL', 'GAIN', 'STATUS')
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);"""
    data_tuple = (discord_id, ticker, price, leverage, type, tp, sl, "0", "0")
    conn.execute(sqlite_insert_with_param, data_tuple)
    conn.commit()

def insert_limit_order(discord_id, ticker, leverage, type, tp, sl, entry):
    sqlite_insert_with_param = """INSERT OR REPLACE INTO 'LIMIT_ORDERS'
    ('DISCORD_ID', 'TICKET', 'LEVERAGE', 'TYPE', 'TP', 'SL', 'STATUS', 'ENTRY')
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);"""
    data_tuple = (discord_id, ticker, leverage, type, tp, sl, "0", entry)
    conn.execute(sqlite_insert_with_param, data_tuple)
    conn.commit()

def update_gain_and_tp(discord_id, gain, tp, status = "0"):
    conn.execute(f"UPDATE TRADES SET GAIN='{gain}', TP='{tp}', STATUS='{status}' WHERE DISCORD_ID='{str(discord_id)}'")
    conn.commit()

def get_all_open_orders():
    return conn.execute("SELECT * FROM TRADES WHERE STATUS = '0'")

