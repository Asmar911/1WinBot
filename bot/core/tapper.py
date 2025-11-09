import asyncio
from collections import OrderedDict
from time import time
from datetime import timedelta
from random import randint
from urllib.parse import unquote

import aiohttp
from aiohttp_proxy import ProxyConnector
from better_proxy import Proxy
from pyrogram import Client
from pyrogram.errors import FloodWait, Unauthorized, UserDeactivated, AuthKeyUnregistered
from pyrogram.raw.functions.messages.request_web_view import RequestWebView

from bot.config import settings
from bot.utils import logger
from bot.exceptions import InvalidSession
from .headers import headers


IGNORED_LEVEL_FIELDS = {"name", "description", "gradientsType"}


class Tapper:
    def __init__(self, tg_client: Client):
        self.session_name = f"{tg_client.name:<10}"
        self.tg_client = tg_client
        self.coin_balance = 0
        self.energyLimit = 0
        self.energyRegen = 0
        self.business_Config: list[dict] = []
        self.business_Info: list[dict] = []
        self.business_upgradable_cards: list[dict] = []
        self.blacklist_cards: set[str] = {"$cryptocliker_influencer"}


    async def get_tg_web_data(self, proxy: str | None) -> str:
        if proxy:
            proxy: Proxy = Proxy.from_str(proxy)
            proxy_dict = dict(
                scheme=proxy.protocol,
                hostname=proxy.host,
                port=proxy.port,
                username=proxy.login,
                password=proxy.password
            )
        else:
            proxy_dict = None

        self.tg_client.proxy = proxy_dict

        try:
            with_tg = True

            if not self.tg_client.is_connected:
                with_tg = False
                try:
                    await self.tg_client.connect()
                except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
                    raise InvalidSession(self.session_name)

            while True:
                try:
                    # peer = await self.tg_client.resolve_peer('token1win_bot')
                    peer = await self.tg_client.resolve_peer('OneWinTokenBot')
                    break
                except FloodWait as fl:
                    fls = fl.value

                    logger.warning(f"{self.session_name} | FloodWait {fl}")
                    logger.info(f"{self.session_name} | Sleep {fls}s")

                    await asyncio.sleep(fls + 3)

            web_view = await self.tg_client.invoke(RequestWebView(
                peer=peer,
                bot=peer,
                platform='android',
                from_bot_menu=False,
                url='https://clicker-frontend.tma.top/'
            ))

            auth_url = web_view.url
            tg_web_data = unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0])

            if with_tg is False:
                await self.tg_client.disconnect()

            query_id = tg_web_data.split('query_id=')[1].split('&user=')[0]
            user = unquote(tg_web_data.split('&user=')[1].split('&auth_date=')[0])
            auth_date = int(tg_web_data.split('&auth_date=')[1].split('&signature=')[0])
            signature = tg_web_data.split('&signature=')[1].split('&hash=')[0]
            hash_ = tg_web_data.split('&hash=')[1]
            payload = {'query_id': query_id, 'user': user,
                       'auth_date': auth_date, 'signature': signature, 'hash': hash_}

            return payload

        except InvalidSession as error:
            raise error

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error during Authorization: {error}")
            await asyncio.sleep(delay=3)

    async def login(self, http_client: aiohttp.ClientSession, tg_web_data: dict[str, str | int]) -> dict:
        try:
            response = await http_client.post(
                url=f"https://clicker-backend.tma.top/v3/game/start?query_id={tg_web_data['query_id']}&user={tg_web_data['user']}"
                f"&auth_date={tg_web_data['auth_date']}&signature={tg_web_data['signature']}&hash={tg_web_data['hash']}",
            )
            response.raise_for_status()

            return await response.json()
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while Login: {error}")
            await asyncio.sleep(delay=3)

    async def complete_onboarding(self, http_client: aiohttp.ClientSession) -> dict | None:
        try:
            response = await http_client.post(url="https://clicker-backend.tma.top/game/completed-onboarding",
                                              json={"is_completed_navigation_onboarding": True})
            response.raise_for_status()

            return await response.json()
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while complete onboarding: {error}")
            await asyncio.sleep(delay=3)

    async def balance(self, http_client: aiohttp.ClientSession) -> dict | None:
        try:
            response = await http_client.get(url="https://clicker-backend.tma.top/user/balance")
            response.raise_for_status()

            return await response.json()
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when get balance: {error}")
            await asyncio.sleep(delay=3)

    async def daily_reword(self, http_client: aiohttp.ClientSession) -> dict | None:
        try:
            response = await http_client.get(url="https://clicker-backend.tma.top/v2/tasks/everydayreward")
            response.raise_for_status()
            

            return await response.json()
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when getting daily reward: {error}")
            await asyncio.sleep(delay=3)

    async def Claim_daily_reword(self, http_client: aiohttp.ClientSession) -> dict | None:
        try:
            logger.info(f"{self.session_name} | Sleep 5s before claim Daily reword")
            await asyncio.sleep(delay=5)

            days = await self.daily_reword(http_client=http_client)
            for day in days:
                if day['isCurrent'] and day['status'] == "new":

                    response = await http_client.post(url="https://clicker-backend.tma.top/v2/tasks/everydayreward")
                    response.raise_for_status()
                    logger.success(f"{self.session_name} | Successfully Claimed Daily Reword {day['day']} {day['money']:,}")
                else:
                    logger.info(f"{self.session_name} | Daily Reword already claimed | Next in: {str(timedelta(seconds=day['secondLeft']))}")
                    break
            

            # return await response.json()
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when getting daily reward: {error}")
            await asyncio.sleep(delay=3)



    # async def Game_Config(self, http_client: aiohttp.ClientSession):
    #     try:
    #         response = await http_client.get(url='https://clicker-backend.tma.top/game/config?lang=en')
    #         response.raise_for_status()

    #         return await response.json()
    #     except Exception as error:
    #         logger.error(f"{self.session_name} | Unknown error while getting Game Config: {error}")
    #         await asyncio.sleep(delay=3)


    def update_business_upgradable_cards(self) -> None:
        """Build in-memory lists for business levels and upgrade targets."""
        if not self.business_Config or not self.business_Info:
            self.business_upgradable_cards = []
            return

        grouped_levels: "OrderedDict[str, dict]" = OrderedDict()
        for entry in self.business_Config:
            name = entry.get("name")
            if not name:
                continue

            bucket = grouped_levels.setdefault(
                name,
                {
                    "description": entry.get("description", ""),
                    "gradientsType": entry.get("gradientsType", ""),
                    "Levels": [],
                },
            )

            if not bucket.get("description") and entry.get("description"):
                bucket["description"] = entry["description"]
            if not bucket.get("gradientsType") and entry.get("gradientsType"):
                bucket["gradientsType"] = entry["gradientsType"]

            bucket["Levels"].append(
                {key: value for key, value in entry.items() if key not in IGNORED_LEVEL_FIELDS}
            )

        aggregated_by_name: dict[str, dict] = {}
        for name, payload in grouped_levels.items():
            payload["Levels"].sort(key=lambda lvl: lvl.get("level", 0))
            aggregated_by_name[name] = {
                "Levels": payload["Levels"],
                "Total Levels": len(payload["Levels"]),
            }

        upgradable: list[dict] = []
        for info in self.business_Info:
            name = info.get("name")
            current_level = info.get("level")
            if not name or current_level is None or name in self.blacklist_cards:
                continue

            aggregated = aggregated_by_name.get(name)
            if not aggregated:
                continue

            total_levels = aggregated["Total Levels"]
            if current_level >= total_levels:
                continue

            next_level = next(
                (lvl for lvl in aggregated["Levels"] if lvl.get("level", 0) > current_level),
                None,
            )
            if not next_level:
                continue

            cost = next_level.get("cost")
            profit = next_level.get("profit")
            if isinstance(cost, (int, float)) and cost:
                roi = (profit * 100 / cost) if isinstance(profit, (int, float)) else None
            else:
                roi = None

            upgradable.append(
                {
                    "name": name,
                    "id": next_level.get("id"),
                    "level": next_level.get("level"),
                    "cost": cost,
                    "profit": profit,
                    "roi": roi,
                }
            )

        upgradable.sort(key=lambda card: (card["roi"] is None, -(card["roi"] or 0)))
        self.business_upgradable_cards = [
            card for card in upgradable if card["name"] not in self.blacklist_cards
        ]



    # async def city_Config(self, http_client: aiohttp.ClientSession):
    #     try:
    #         response = await http_client.get(url='https://clicker-backend.tma.top/city/config')
    #         response.raise_for_status()

    #         return await response.json()
    #     except Exception as error:
    #         logger.error(f"{self.session_name} | Unknown error while getting City Config: {error}")
    #         await asyncio.sleep(delay=3)

    # async def City_Info(self, http_client: aiohttp.ClientSession):
    #     try:
    #         response = await http_client.get(url='https://clicker-backend.tma.top/v2/city/launch')
    #         response.raise_for_status()

    #         return await response.json()
    #     except Exception as error:
    #         logger.error(f"{self.session_name} | Unknown error while getting City Info: {error}")
    #         await asyncio.sleep(delay=3)

    async def Game_Config(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.get(url='https://clicker-backend.tma.top/game/config?lang=en')
            response.raise_for_status()
            if response:
                data = await response.json()
                self.business_Config = data['PassiveProfit']
                logger.success(f"{self.session_name} | Successfully Fetched PassiveProfit Info")
            else:
                logger.error(f"{self.session_name} | Unknown error while getting PassiveProfit")

            # return await response.json()
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting City Config: {error}")
            await asyncio.sleep(delay=3)

    async def Business_Info(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.get(url='https://clicker-backend.tma.top/business')
            response.raise_for_status()
            if response: 
                body = await response.json()
                self.business_Info = body["result"]["body"]
                logger.success(f"{self.session_name} | Successfully Fetched Business Info")
            else:
                logger.error(f"{self.session_name} | Unknown error while getting Business Body Info")

            # return await response.json()
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Business Info: {error}")
            await asyncio.sleep(delay=3)

    async def Business_Upgrade(self,Card_Id, Card_level, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.post(url='https://clicker-backend.tma.top/business', json={"id":Card_Id,"level":Card_level})
            response.raise_for_status()
            logger.success(f"{self.session_name} | Successfully Upgraded Card {Card_Id} to lvl {Card_level}")
            # return await response.json() ## response {"totalProfit": 36284550,"NextLevel": {"name": "$cryptocliker_oil_factory","icon": "Oil Factory-2","id": "oil_factory25","profit": 6500,"cost": 42500000,"level": 25}}

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Energy Boost Info: {error}")
            await asyncio.sleep(delay=3)

    async def UPGRADE(self, http_client: aiohttp.ClientSession):
        try:
            logger.info(f"{self.session_name} | Business upgrade phase started")

            while True:
                await asyncio.sleep(delay=3)
                await self.Game_Config(http_client=http_client)
                await asyncio.sleep(delay=3)
                await self.Business_Info(http_client=http_client)
                await asyncio.sleep(delay=3)

                self.update_business_upgradable_cards()
                if not self.business_upgradable_cards:
                    logger.info(f"{self.session_name} | No cards available for upgrade")
                    break

                balance_data = await self.balance(http_client=http_client)
                if not balance_data:
                    logger.warning(f"{self.session_name} | Unable to fetch balance before upgrading")
                    break

                self.coin_balance = balance_data.get("coinsBalance", self.coin_balance)

                card = self.business_upgradable_cards[0]
                card_id = card.get("id") or card.get("name")
                if not card_id:
                    logger.warning(f"{self.session_name} | Missing card id for {card.get('name')}, skipping")
                    self.blacklist_cards.add(card.get("name", ""))
                    continue

                cost = card.get("cost")
                if cost is None:
                    logger.warning(f"{self.session_name} | Missing cost info for {card['name']}, skipping")
                    self.blacklist_cards.add(card["name"])
                    continue

                if cost > self.coin_balance:
                    logger.warning(f"{self.session_name} | Need more {(cost - self.coin_balance):,} before upgrading {card['name']} card")
                    break

                remaining_balance = self.coin_balance - cost
                if remaining_balance < settings.MIN_Balance:
                    logger.warning(f"{self.session_name} | Stopped upgrading | Minimum balance ({settings.MIN_Balance:,}) would be breached")
                    break

                logger.info(f"{self.session_name} | Upgrading {card['name']} to level {card['level']} (cost: {cost:,})")
                await self.Business_Upgrade(Card_Id=card_id, Card_level=card['level'], http_client=http_client)
                await asyncio.sleep(delay=3)
                # Loop will refetch data before attempting the next upgrade

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while upgrading businesses: {error}")
            await asyncio.sleep(delay=3)

    # async def Upgrade_Mining(self, buildingId, buildingtype, http_client: aiohttp.ClientSession):
    #     try:
    #         response = await http_client.post(url='https://clicker-backend.tma.top/city/building', json={"buildingId":buildingId, "type":buildingtype})
    #         response.raise_for_status()

    #         return await response.json() ## respose {"population":3706486,"incomePerHour":37096868}
    #     except Exception as error:
    #         logger.error(f"{self.session_name} | Unknown error while getting Energy Boost Info: {error}")
    #         await asyncio.sleep(delay=3)

    async def get_energy_boost_info(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.get(url='https://clicker-backend.tma.top/v2/energy/bonus')
            response.raise_for_status()

            return await response.json()
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Energy Boost Info: {error}")
            await asyncio.sleep(delay=3)

    async def improvements_info(self, http_client: aiohttp.ClientSession) -> list[dict]:
        try:
            response = await http_client.get(url='https://clicker-backend.tma.top/energy/improvements')
            response.raise_for_status()

            return await response.json()
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting improvements: {error}")
            await asyncio.sleep(delay=3)

    async def level_up(self, http_client: aiohttp.ClientSession, boost_id: int) -> bool:
        try:
            response = await http_client.post(url='https://api-backend.yescoin.fun/build/levelUp', json=boost_id)
            response.raise_for_status()

            response_json = await response.json()

            return response_json['data']
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when Apply {boost_id} Boost: {error}")
            await asyncio.sleep(delay=3)

            return False

    async def apply_energy_boost(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.post(url='https://clicker-backend.tma.top/v2/energy/bonus')
            response.raise_for_status()

            return await response.json()
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when Apply Energy Boost: {error}")
            await asyncio.sleep(delay=3)

            return False

    async def send_taps(self, http_client: aiohttp.ClientSession, taps: int) -> None:
        try:
            response = await http_client.post(url='https://clicker-backend.tma.top/tap', json={"tapsCount": taps})
            response.raise_for_status()

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when Tapping: {error}")
            await asyncio.sleep(delay=3)

    async def Improve_Tap(self,old, http_client: aiohttp.ClientSession) -> None:
        try:
            response = await http_client.post(url='https://clicker-backend.tma.top/v3/energy/tap/improve')
            response.raise_for_status()
            data= await response.json()
            taps= data['result']['nextImprovement']['currentLevel']
            logger.success(f"{self.session_name} | Successfully Improved taps to {taps:,}(+{old:,}) Business Info")

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when Improve Tapping: {error}")
            await asyncio.sleep(delay=3)

    async def improvement_info(self, http_client: aiohttp.ClientSession) -> None:
        try:
            response = await http_client.get(url='https://clicker-backend.tma.top/v3/energy/tap/improvement')
            response.raise_for_status()
            data= await response.json()
            oldLvl= data['result']['currentLevel']
            logger.info(f"{self.session_name} | Sleep For 5s before Upgrade taps")
            await asyncio.sleep(delay=5)
            await self.Improve_Tap(old=oldLvl, http_client=http_client)

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when Improve Tapping: {error}")
            await asyncio.sleep(delay=3)

    async def check_proxy(self, http_client: aiohttp.ClientSession, proxy: Proxy) -> None:
        try:
            response = await http_client.get(url='https://httpbin.org/ip', timeout=aiohttp.ClientTimeout(5))
            ip = (await response.json()).get('origin')
            logger.info(f"{self.session_name} | Proxy IP: {ip}")
        except Exception as error:
            logger.error(f"{self.session_name} | Proxy: {proxy} | Error: {error}")

    async def run(self, proxy: str | None) -> None:
        access_token_created_time = 0

        proxy_conn = ProxyConnector().from_url(proxy) if proxy else None

        async with aiohttp.ClientSession(headers=headers, connector=proxy_conn) as http_client:
            if proxy:
                await self.check_proxy(http_client=http_client, proxy=proxy)

            while True:
                try:
                    if time() - access_token_created_time >= 3600:
                        tg_web_data = await self.get_tg_web_data(proxy=proxy)
                        login_data = await self.login(http_client=http_client, tg_web_data=tg_web_data)
                        access_token = login_data.get('result', {}).get('token')
                        # print (access_token)

                        http_client.headers["Authorization"] = f"Bearer {access_token}"
                        headers["Authorization"] = f"Bearer {access_token}"

                        access_token_created_time = time()

                        balance_data = await self.balance(http_client=http_client)

                        balance = balance_data['coinsBalance']
                        curr_energy = login_data['result']['currentEnergy']
                        limit_energy = login_data['result']['energyLimit']

                        logger.success(
                            f"{self.session_name} | Login! | Balance: {balance:,} | Passive Earn: {login_data['result']['totalPassiveProfit']:,}  | Energy: {curr_energy:,}/{limit_energy:,}")

                        if login_data['result']['isCompletedNavigationOnboarding'] is False:
                            await self.complete_onboarding(http_client=http_client)

                        await self.Claim_daily_reword(http_client=http_client)
                    

                    taps = randint(a=settings.RANDOM_TAPS_COUNT[0], b=settings.RANDOM_TAPS_COUNT[1])

                    game_data = await self.balance(http_client=http_client)

                    available_energy = game_data['currentEnergy']
                    coins_by_tap = game_data['coinsPerClick']

                    if taps * coins_by_tap >= available_energy:
                        taps = abs(available_energy // 10 - 1)

                    status = await self.send_taps(http_client=http_client, taps=taps)

                    profile_data = await self.balance(http_client=http_client)

                    if not profile_data:
                        continue

                    self.energyLimit = profile_data['energyLimit']
                    self.energyRegen = profile_data['energyRegen']
                    new_balance = profile_data['coinsBalance']
                    self.coin_balance = new_balance
                    available_energy = profile_data['currentEnergy']
                    calc_taps = new_balance - balance

                    logger.success(f"{self.session_name} | Successful tapped! {taps:,} taps | "
                                   f"Balance: <c>{self.coin_balance:,}</c> (<g>+{calc_taps:,}</g>) | remaining taps: {available_energy:,}")

                    boosts_info = await self.get_energy_boost_info(http_client=http_client)

                    energy_boost_count = boosts_info['result']['remaining']
                    second_to_next_use_energy = boosts_info['result']['seconds_to_next_use']

                    if (energy_boost_count > 0 and second_to_next_use_energy == 0
                            and available_energy < settings.MIN_AVAILABLE_ENERGY
                            and settings.APPLY_DAILY_ENERGY is True):
                        logger.info(f"{self.session_name} | Sleep 5s before activating the daily energy boost")
                        await asyncio.sleep(delay=5)

                        status = await self.apply_energy_boost(http_client=http_client)
                        if status is True:
                            logger.success(f"{self.session_name} | Energy boost applied")

                            await asyncio.sleep(delay=1)

                        continue

                    if available_energy < settings.MIN_AVAILABLE_ENERGY:
                        logger.info(f"{self.session_name} | Minimum energy reached: {available_energy}")

                        await self.UPGRADE(http_client=http_client)
                        await asyncio.sleep(delay=3)
                        await self.improvement_info(http_client=http_client)
                        
                        # sleep_max = randint(a=settings.SLEEP_BY_MIN_ENERGY[0], b=settings.SLEEP_BY_MIN_ENERGY[1])
                        sleep_limit = self.energyLimit / self.energyRegen
                        sleep_max = randint(a=sleep_limit+60,b=sleep_limit+240)
                        logger.info(f"{self.session_name} | Sleep Limit: {sleep_limit} | Sleep {sleep_max}s")

                        await asyncio.sleep(delay=sleep_max)

                        continue

                except InvalidSession as error:
                    raise error

                except Exception as error:
                    logger.error(f"{self.session_name} | Unknown error: {error}")
                    await asyncio.sleep(delay=3)

                else:
                    sleep_between_clicks = randint(a=settings.SLEEP_BETWEEN_TAP[0], b=settings.SLEEP_BETWEEN_TAP[1])

                    logger.info(f"{self.session_name} | Sleep {sleep_between_clicks}s")
                    await asyncio.sleep(delay=sleep_between_clicks)


async def run_tapper(tg_client: Client, proxy: str | None):
    try:
        await Tapper(tg_client=tg_client).run(proxy=proxy)
    except InvalidSession:
        logger.error(f"{tg_client.name} | Invalid Session")
