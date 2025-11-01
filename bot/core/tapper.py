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

    # async def daily_reword(self, http_client: aiohttp.ClientSession) -> dict | None:
    #     try:
    #         response = await http_client.get(url="https://clicker-backend.tma.top/v2/tasks/everydayreward")
    #         response.raise_for_status()
    #         is_collected = response.get('days')[0].get('isCollected')
    #         reward = response.get('days')[0].get('money')
    #         day = response.get('days')[0].get('id')
    #         if is_collected == False:
    #             post_response = await self.session.post('https://crypto-clicker-backend-go-prod.100hp.app/tasks/everydayreward',proxy = self.proxy)
                
    #             authorization = self.session.headers['authorization']
    #             del self.session.headers['authorization']
    #             self.session.headers['access-control-request-headers'] = 'authorization'
    #             self.session.headers['access-control-request-method'] = 'POST'
                
    #             await self.session.options('https://crypto-clicker-backend-go-prod.100hp.app/tasks/everydayreward',proxy = self.proxy)
                
    #             del self.session.headers['access-control-request-headers']
    #             del self.session.headers['access-control-request-method']
    #             self.session.headers['authorization'] = authorization
            
    #             logger.success(f"| Thread {self.thread} | {self.name} | claim {day} reward : {reward}")

    #         # return await response.json()
    #     except Exception as error:
    #         logger.error(f"{self.session_name} | Unknown error when getting daily reward: {error}")
    #         await asyncio.sleep(delay=3)
    #

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

    async def Upgrade_Mining(self,Card_Id, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.post(url='https://clicker-backend.tma.top/minings', json={"id":Card_Id})
            response.raise_for_status()

            return await response.json() ## response {"totalProfit": 36284550,"NextLevel": {"name": "$cryptocliker_oil_factory","icon": "Oil Factory-2","id": "oil_factory25","profit": 6500,"cost": 42500000,"level": 25}}
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Energy Boost Info: {error}")
            await asyncio.sleep(delay=3)

    async def Upgrade_Mining(self, buildingId, buildingtype, http_client: aiohttp.ClientSession):
        try:
            response = await http_client.post(url='https://clicker-backend.tma.top/city/building', json={"buildingId":buildingId, "type":buildingtype})
            response.raise_for_status()

            return await response.json() ## respose {"population":3706486,"incomePerHour":37096868}
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Energy Boost Info: {error}")
            await asyncio.sleep(delay=3)

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
