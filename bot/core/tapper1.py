import asyncio
from time import time
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


class Tapper:
    def __init__(self, tg_client: Client):
        self.session_name = f"{tg_client.name:<10}"
        self.tg_client = tg_client

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
                url=f"https://clicker-backend.tma.top/game/start?query_id={tg_web_data['query_id']}&user={tg_web_data['user']}"
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

    async def claim_daily_reward(self, http_client: aiohttp.ClientSession) -> None:
        """Claim daily reward if it has not been collected yet."""
        try:
            response = await http_client.get(
                url="https://clicker-backend.tma.top/v2/tasks/everydayreward"
            )
            response.raise_for_status()
            data = await response.json()

            today = data.get("days", [{}])[0]
            if today.get("isCollected") is False:
                post_response = await http_client.post(
                    url="https://clicker-backend.tma.top/v2/tasks/everydayreward",
                    json={"id": today.get("id")},
                )
                post_response.raise_for_status()
                logger.success(
                    f"{self.session_name} | Claimed daily reward: {today.get('money')}"
                )
        except Exception as error:
            logger.error(
                f"{self.session_name} | Unknown error when getting daily reward: {error}"
            )
            await asyncio.sleep(delay=3)


    async def Game_Config(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.get(url='https://clicker-backend.tma.top/game/config?lang=en')
            response.raise_for_status()

            return await response.json()
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Game Config: {error}")
            await asyncio.sleep(delay=3)

    async def city_Config(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.get(url='https://clicker-backend.tma.top/city/config')
            response.raise_for_status()

            return await response.json()
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting City Config: {error}")
            await asyncio.sleep(delay=3)

    async def City_Info(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.get(url='https://clicker-backend.tma.top/v2/city/launch')
            response.raise_for_status()

            return await response.json()
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting City Info: {error}")
            await asyncio.sleep(delay=3)

    async def Mining_Info(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.get(url='https://clicker-backend.tma.top/minings')
            response.raise_for_status()

            return await response.json()
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Mining Info: {error}")
            await asyncio.sleep(delay=3)

    async def upgrade_mining(self, card_id: str, http_client: aiohttp.ClientSession):
        """Upgrade mining card by id."""
        try:
            response = await http_client.post(
                url="https://clicker-backend.tma.top/minings", json={"id": card_id}
            )
            response.raise_for_status()
            return await response.json()
        except Exception as error:
            logger.error(
                f"{self.session_name} | Unknown error while upgrading mining {card_id}: {error}"
            )
            await asyncio.sleep(delay=3)

    async def upgrade_building(
        self, building_id: int, building_type: str, http_client: aiohttp.ClientSession
    ):
        """Upgrade a city building."""
        try:
            response = await http_client.post(
                url="https://clicker-backend.tma.top/city/building",
                json={"buildingId": building_id, "type": building_type},
            )
            response.raise_for_status()
            return await response.json()
        except Exception as error:
            logger.error(
                f"{self.session_name} | Unknown error while upgrading building {building_id}: {error}"
            )
            await asyncio.sleep(delay=3)

    async def upgrade_game_objects( self, http_client: aiohttp.ClientSession, balance: int) -> int:
        """Upgrade minings and city buildings if enough balance."""
        try:
            minings = await self.Mining_Info(http_client=http_client) or []
            for mining in minings:
                cost = mining.get("cost") or 0
                mining_id = mining.get("id")
                if mining_id and cost <= balance:
                    if await self.upgrade_mining(mining_id, http_client):
                        balance -= cost
                        logger.success(
                            f"{self.session_name} | Upgraded mining {mining_id}"
                        )

            city = await self.City_Info(http_client=http_client) or {}
            for building in city.get("buildings", []):
                upgrade_cost = building.get("upgradeCost") or 0
                building_id = building.get("id")
                building_type = building.get("type")
                if building_id and building_type and upgrade_cost <= balance:
                    if await self.upgrade_building(
                        building_id, building_type, http_client
                    ):
                        balance -= upgrade_cost
                        logger.success(
                            f"{self.session_name} | Upgraded building {building_id}"
                        )

            return balance
        except Exception as error:
            logger.error(
                f"{self.session_name} | Unknown error while upgrading objects: {error}"
            )
            await asyncio.sleep(delay=3)
            return balance

    async def auto_upgrade(self, http_client: aiohttp.ClientSession, balance: int) -> int:
        """Perform all available upgrades using current balance."""
        balance = await self.upgrade_improvements(http_client, balance)
        balance = await self.upgrade_game_objects(http_client, balance)
        return balance

    async def get_energy_boost_info(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.get(url='https://clicker-backend.tma.top/energy/bonus')
            response.raise_for_status()

            return await response.json()
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Energy Boost Info: {error}")
            await asyncio.sleep(delay=3)

    async def get_turbo_boost_info(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.get(url='https://clicker-backend.tma.top/turbo/bonus')
            response.raise_for_status()

            return await response.json()
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Turbo Boost Info: {error}")
            await asyncio.sleep(delay=3)

    async def improvements_info(self, http_client: aiohttp.ClientSession) -> list[dict]:
        try:
            response = await http_client.get(url='https://clicker-backend.tma.top/energy/improvements')
            response.raise_for_status()

            return await response.json()
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting improvements: {error}")
            await asyncio.sleep(delay=3)

    async def buy_improvement(self, http_client: aiohttp.ClientSession, item_id: str) -> bool:
        """Purchase improvement by id."""
        try:
            response = await http_client.post(
                url="https://clicker-backend.tma.top/energy/improvements",
                json={"id": item_id},
            )
            response.raise_for_status()
            await response.json()
            return True
        except Exception as error:
            logger.error(
                f"{self.session_name} | Unknown error when upgrading {item_id}: {error}"
            )
            await asyncio.sleep(delay=3)
            return False

    async def upgrade_improvements(self, http_client: aiohttp.ClientSession, balance: int) -> int:
        """Automatically upgrade tap income, energy and charge improvements."""
        try:
            improvements = await self.improvements_info(http_client=http_client)
            if not improvements:
                return balance

            for item in improvements:
                item_id = item.get("id", "")
                price = item.get("price") or item.get("cost") or 0
                level = item.get("level", 0)

                if item_id.startswith("tapincome") and settings.AUTO_UPGRADE_TAP:
                    if level < settings.MAX_TAP_LEVEL and price <= balance:
                        if await self.buy_improvement(http_client, item_id):
                            balance -= price
                            logger.success(
                                f"{self.session_name} | Tap income upgraded to level {level + 1}"
                            )
                elif item_id.startswith("energylimit") and settings.AUTO_UPGRADE_ENERGY:
                    if level < settings.MAX_ENERGY_LEVEL and price <= balance:
                        if await self.buy_improvement(http_client, item_id):
                            balance -= price
                            logger.success(
                                f"{self.session_name} | Energy limit upgraded to level {level + 1}"
                            )
                elif item_id.startswith("energyregen") and settings.AUTO_UPGRADE_CHARGE:
                    if level < settings.MAX_CHARGE_LEVEL and price <= balance:
                        if await self.buy_improvement(http_client, item_id):
                            balance -= price
                            logger.success(
                                f"{self.session_name} | Charge speed upgraded to level {level + 1}"
                            )

            return balance
        except Exception as error:
            logger.error(
                f"{self.session_name} | Unknown error while upgrading improvements: {error}"
            )
            await asyncio.sleep(delay=3)
            return balance

    async def apply_energy_boost(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.post(url='https://clicker-backend.tma.top/energy/bonus')
            response.raise_for_status()

            return await response.json()
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when Apply Energy Boost: {error}")
            await asyncio.sleep(delay=3)

            return False

    async def apply_turbo_boost(self, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.post(url='https://clicker-backend.tma.top/turbo/bonus')
            response.raise_for_status()

            return await response.json()
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when Apply Turbo Boost: {error}")
            await asyncio.sleep(delay=3)

            return False

    async def send_taps(self, http_client: aiohttp.ClientSession, taps: int) -> None:
        try:
            response = await http_client.post(url='https://clicker-backend.tma.top/tap', json={"tapsCount": taps})
            response.raise_for_status()

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when Tapping: {error}")
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
                        access_token = login_data.get('token')

                        http_client.headers["Authorization"] = f"Bearer {access_token}"
                        headers["Authorization"] = f"Bearer {access_token}"

                        access_token_created_time = time()

                        balance_data = await self.balance(http_client=http_client)

                        balance = balance_data['coinsBalance']
                        curr_energy = login_data['currentEnergy']
                        limit_energy = login_data['energyLimit']

                        logger.success(
                            f"{self.session_name} | Login! | Balance: {balance:,} | Passive Earn: {login_data['totalPassiveProfit']:,}  | Energy: {curr_energy:,}/{limit_energy:,}")

                        if login_data.get('isCompletedNavigationOnboarding') is False:
                            await self.complete_onboarding(http_client=http_client)

                        await self.claim_daily_reward(http_client=http_client)
                        balance = await self.auto_upgrade(http_client, balance)
                    

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

                    new_balance = profile_data['coinsBalance']
                    available_energy = profile_data['currentEnergy']
                    calc_taps = new_balance - balance
                    balance = new_balance

                    logger.success(f"{self.session_name} | Successful tapped! {taps:,} taps | "
                                   f"Balance: <c>{balance:,}</c> (<g>+{calc_taps:,}</g>) | remaining taps: {available_energy:,}")

                    balance = await self.auto_upgrade(http_client, balance)

                    boosts_info = await self.get_energy_boost_info(http_client=http_client)

                    energy_boost_count = boosts_info['remaining']
                    second_to_next_use_energy = boosts_info['seconds_to_next_use']

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

                    turbo_info = await self.get_turbo_boost_info(http_client=http_client)
                    turbo_boost_count = turbo_info['remaining']
                    second_to_next_use_turbo = turbo_info['seconds_to_next_use']

                    if (
                        turbo_boost_count > 0
                        and second_to_next_use_turbo == 0
                        and settings.APPLY_DAILY_TURBO is True
                    ):
                        logger.info(
                            f"{self.session_name} | Sleep 5s before activating the daily turbo boost"
                        )
                        await asyncio.sleep(delay=5)

                        status = await self.apply_turbo_boost(http_client=http_client)
                        if status is True:
                            logger.success(f"{self.session_name} | Turbo boost applied")

                            await asyncio.sleep(delay=1)

                        continue

                    if available_energy < settings.MIN_AVAILABLE_ENERGY:
                        logger.info(f"{self.session_name} | Minimum energy reached: {available_energy}")
                        sleep_max = randint(a=settings.SLEEP_BY_MIN_ENERGY[0], b=settings.SLEEP_BY_MIN_ENERGY[1])
                        logger.info(f"{self.session_name} | Sleep {sleep_max}s")

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