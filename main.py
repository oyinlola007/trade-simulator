import asyncio, discord, re

import yfinance as yf

import cogs.config as config
import cogs.db as db

db.initializeDB()

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author.id != config.BOT_ID:
        try:
            crypto_pattern = re.compile("^(long|short) [A-Z]+ @ (m|[0-9.]+)\n\d+x\nTP:[0-9.\s]+,[0-9.\s]+,[0-9.\s]+,[0-9.\s]+\nSL:[0-9.\s]+$")
            if crypto_pattern.match(message.content):
                splited = message.content.split()
                type_ = splited[0]
                ticker = splited[1]
                entry = splited[3]
                leverage = splited[4].replace("x", "")
                tp = ",".join([str(float(val.strip())) for val in message.content.split(":")[1].replace("SL", "").split(",")])
                sl = str(float(message.content.split(":")[2].strip()))

                price = yf.Ticker(f'{ticker}-USD').info['regularMarketPrice']

                if price == None:
                    await message.channel.send("Invalid ticker entered")
                    return

                tps = tp.slpit(",")

                if entry == "m":
                    if type_ == "short":
                        if float(sl) < price:
                            await message.channel.send(f"Stop loss must be greater than current price ({price})")
                            return

                        if not (tps[3] < tps[2] and tps[2] < tps[1] and tps[1] < tps[0] and tps[0] < price):
                            await message.channel.send(f"Invalid take profits entered")
                            return
                    else:
                        if float(sl) > price:
                            await message.channel.send(f"Stop loss must be lesser than current price ({price})")
                            return

                        if not (tps[3] > tps[2] and tps[2] > tps[1] and tps[1] > tps[0] and tps[0] > price):
                            await message.channel.send(f"Invalid take profits entered")
                            return

                    db.insert_trade(message.author.id, ticker, price, leverage, type_, tp, sl)


                """else:
                    #validate entry
                    price = float(entry)
                    if type_ == "short":
                        if float(sl) < price:
                            await message.channel.send(f"Stop loss must be greater than current price ({price})")
                            return

                        if not (tps[3] < tps[2] and tps[2] < tps[1] and tps[1] < tps[0] and tps[0] < price):
                            await message.channel.send(f"Invalid take profits entered")
                            return
                    else:
                        if float(sl) > price:
                            await message.channel.send(f"Stop loss must be lesser than current price ({price})")
                            return

                        if not (tps[3] > tps[2] and tps[2] > tps[1] and tps[1] > tps[0] and tps[0] > price):
                            await message.channel.send(f"Invalid take profits entered")
                            return

                    db.insert_limit_order(message.author.id, ticker, leverage, type, tp, sl, entry)"""

            stock_pattern = re.compile("^[A-Z]+ (call|put) @ (m|[0-9.]+)\nTP:[0-9.\s]+,[0-9.\s]+,[0-9.\s]+,[0-9.\s]+\nSL:[0-9.\s]+$")
            if stock_pattern.match(message.content):
                splited = message.split()
                type_ = splited[1]
                ticker = splited[0]
                entry = splited[3]
                tp = ",".join([str(float(val.strip())) for val in message.split(":")[1].replace("SL", "").split(",")])
                sl = str(float(message.split(":")[2].strip()))

                price = yf.Ticker(f'{ticker}').info['regularMarketPrice']
                leverage = 100

                if price == None:
                    await message.channel.send("Invalid ticker entered")
                    return

                tps = tp.slpit(",")

                if entry == "m":
                    if type_ == "put":
                        if float(sl) < price:
                            await message.channel.send(f"Stop loss must be greater than current price ({price})")
                            return

                        if not (tps[3] < tps[2] and tps[2] < tps[1] and tps[1] < tps[0] and tps[0] < price):
                            await message.channel.send(f"Invalid take profits entered")
                            return
                    else:
                        if float(sl) > price:
                            await message.channel.send(f"Stop loss must be lesser than current price ({price})")
                            return

                        if not (tps[3] > tps[2] and tps[2] > tps[1] and tps[1] > tps[0] and tps[0] > price):
                            await message.channel.send(f"Invalid take profits entered")
                            return

                    db.insert_trade(message.author.id, ticker, price, leverage, type_, tp, sl)


        except:
            pass



async def user_metrics_background_task():
    await client.wait_until_ready()
    while True:
        data = db.get_all_open_orders()

        for row in data:
            try:
                discord_id = row[0]
                ticker = row[1]
                price = row[2]
                type_ = row[4]
                leverage = row[3]
                tp = row[5]
                sl = row[6]
                gain = float(row[7])
                tps = tp.slpit(",")

                if type_ in ["long", "short"]:
                    current_price = yf.Ticker(f'{ticker}-USD').info['regularMarketPrice']
                    if type_ == "long":
                        for val in tps:
                            if float(val) >= current_price:
                                gain += 0.25 * leverage * abs(current_price - price)
                                tp.replace(f"{val},", "").replace(f"{val}", "")
                            else:
                                break

                        if gain != float(row[7]):
                            if tp == "":
                                db.update_gain_and_tp(discord_id, gain, tp, "1")
                            else:
                                db.update_gain_and_tp(discord_id, gain, tp)

                        if current_price < float(sl):
                            gain += -1 * (len(tps)/4) * leverage * abs(current_price - price)
                            db.update_gain_and_tp(discord_id, gain, tp, "1")
                    else:
                        for val in tps:
                            if float(val) <= current_price:
                                gain += 0.25 * leverage * abs(current_price - price)
                                tp.replace(f"{val},", "").replace(f"{val}", "")
                            else:
                                break

                        if gain != float(row[7]):
                            if tp == "":
                                db.update_gain_and_tp(discord_id, gain, tp, "1")
                            else:
                                db.update_gain_and_tp(discord_id, gain, tp)

                        if current_price > float(sl):
                            gain += -1 * (len(tps)/4) * leverage * abs(current_price - price)
                            db.update_gain_and_tp(discord_id, gain, tp, "1")

                else:
                    current_price = yf.Ticker(f'{ticker}').info['regularMarketPrice']
                    if type_ == "call":
                        for val in tps:
                            if float(val) >= current_price:
                                gain += 0.25 * leverage * abs(current_price - price)
                                tp.replace(f"{val},", "").replace(f"{val}", "")
                            else:
                                break

                        if gain != float(row[7]):
                            if tp == "":
                                db.update_gain_and_tp(discord_id, gain, tp, "1")
                            else:
                                db.update_gain_and_tp(discord_id, gain, tp)

                        if current_price < float(sl):
                            gain += -1 * (len(tps)/4) * leverage * abs(current_price - price)
                            db.update_gain_and_tp(discord_id, gain, tp, "1")
                    else:
                        for val in tps:
                            if float(val) <= current_price:
                                gain += 0.25 * leverage * abs(current_price - price)
                                tp.replace(f"{val},", "").replace(f"{val}", "")
                            else:
                                break

                        if gain != float(row[7]):
                            if tp == "":
                                db.update_gain_and_tp(discord_id, gain, tp, "1")
                            else:
                                db.update_gain_and_tp(discord_id, gain, tp)

                        if current_price > float(sl):
                            gain += -1 * (len(tps)/4) * leverage * abs(current_price - price)
                            db.update_gain_and_tp(discord_id, gain, tp, "1")

            except:
                pass

        await asyncio.sleep(1)


client.loop.create_task(user_metrics_background_task())
client.run(config.DISCORD_TOKEN)