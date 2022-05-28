import datetime
import enum
import json
import logging
import os
import pickle
import random
import re
import shutil
import string
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from websocket import create_connection
import sys

logger = logging.getLogger(__name__)


class Interval(enum.Enum):
    in_1_minute = "1"
    in_3_minute = "3"
    in_5_minute = "5"
    in_15_minute = "15"
    in_30_minute = "30"
    in_45_minute = "45"
    in_1_hour = "1H"
    in_2_hour = "2H"
    in_3_hour = "3H"
    in_4_hour = "4H"
    in_daily = "1D"
    in_weekly = "1W"
    in_monthly = "1M"


class TvDatafeed:
    path = os.path.join(os.path.expanduser("~"), ".tv_datafeed/")
    headers = json.dumps({"Origin": "https://data.tradingview.com"})

    def __save_token(self, token):
        tokenfile = os.path.join(self.path, "token")
        contents = dict(
            token=token,
            date=self.token_date,
            chromedriver_path=self.chromedriver_path,
        )

        with open(tokenfile, "wb") as f:
            pickle.dump(contents, f)

        logger.debug("auth saved")

    def __load_token(self):
        tokenfile = os.path.join(self.path, "token")
        token = None
        if os.path.exists(tokenfile):
            with open(tokenfile, "rb") as f:
                contents = pickle.load(f)

            if contents["token"] not in [
                "unauthorized_user_token",
                None,
            ]:
                token = contents["token"]
                self.token_date = contents["date"]
                logger.debug("auth loaded")

            self.chromedriver_path = contents["chromedriver_path"]

        return token

    def __assert_dir(self):
        if not os.path.exists(self.path):
            os.mkdir(self.path)
            if self.chromedriver_path is None:
                if (
                    input(
                        "\n\ndo you want to install chromedriver automatically?? y/n\t"
                    ).lower()
                    == "y"
                ):
                    self.__install_chromedriver()

            else:
                self.__save_token(token=None)
                logger.info(
                    "will use specified chromedriver path, no to specify this path again"
                )

        if not os.path.exists(self.profile_dir):
            os.mkdir(self.profile_dir)
            logger.debug("created chrome user dir")

    def __install_chromedriver(self):

        os.system("pip install chromedriver-autoinstaller")

        import chromedriver_autoinstaller

        path = chromedriver_autoinstaller.install(cwd=True)

        if path is not None:
            self.chromedriver_path = os.path.join(
                self.path, "chromedriver" + (".exe" if ".exe" in path else "")
            )
            shutil.copy(path, self.chromedriver_path)
            self.__save_token(token=None)

            try:
                time.sleep(1)
                os.remove(path)
            except:
                logger.info(
                    f"unable to remove file '{path}', you may want to remove it manually"
                )

        else:
            logger.error(" unable to download chromedriver automatically.")

    def clear_cache(self):

        import shutil

        shutil.rmtree(self.path)
        logger.info("cache cleared")

    def __init__(
        self,
        username=None,
        password=None,
        chromedriver_path=None,
        auto_login=True,
    ) -> None:

        self.ws_debug = False
        self.__automatic_login = auto_login
        self.chromedriver_path = chromedriver_path
        self.profile_dir = os.path.join(self.path, "chrome")
        self.token_date = datetime.date.today() - datetime.timedelta(days=1)
        self.__assert_dir()

        token = None
        token = self.auth(username, password)

        if token is None:
            token = "unauthorized_user_token"
            logger.warning(
                "you are using nologin method, data you access may be limited"
            )

        self.token = token
        self.ws = None
        self.session = self.__generate_session()
        self.chart_session = self.__generate_chart_session()

    def __login(self, username, password):

        driver = self.__webdriver_init()

        if not self.__automatic_login:
            input()

        else:
            try:
                logger.debug("click sign in")
                driver.find_element_by_class_name("tv-header__user-menu-button").click()
                driver.find_element_by_xpath(
                    '//*[@id="overlap-manager-root"]/div/span/div[1]/div/div/div[1]/div[2]/div'
                ).click()

                time.sleep(5)
                logger.debug("click email")
                embutton = driver.find_element_by_class_name(
                    "tv-signin-dialog__toggle-email"
                )
                embutton.click()
                time.sleep(5)

                logger.debug("entering credentials")
                username_input = driver.find_element_by_name("username")
                username_input.send_keys(username)
                password_input = driver.find_element_by_name("password")
                password_input.send_keys(password)

                logger.debug("click login")
                submit_button = driver.find_element_by_class_name("tv-button__loader")
                submit_button.click()
                time.sleep(5)
            except Exception as e:
                logger.error(f"{e}, {e.args}")
                logger.error(
                    "automatic login failed\n Reinitialize tvdatafeed with auto_login=False "
                )

        return driver

    def auth(self, username, password):
        token = self.__load_token()

        if (
            token is None
            and (username is None or password is None)
            and self.__automatic_login
        ):
            pass

        elif self.token_date == datetime.date.today():
            pass

        elif token is not None and (username is None or password is None):
            driver = self.__webdriver_init()
            if driver is not None:
                token = self.__get_token(driver)
                self.token_date = datetime.date.today()
                self.__save_token(token)

        else:
            driver = self.__login(username, password)
            if driver is not None:
                token = self.__get_token(driver)
                self.token_date = datetime.date.today()
                self.__save_token(token)

        return token

    def __webdriver_init(self):
        caps = DesiredCapabilities.CHROME

        caps["goog:loggingPrefs"] = {"performance": "ALL"}

        logger.info("refreshing tradingview token using selenium")
        logger.debug("launching chrome")
        options = Options()

        if self.__automatic_login:
            options.add_argument("--headless")
            logger.debug("chromedriver in headless mode")

        # options.add_argument("--start-maximized")
        options.add_argument("--disable-gpu")

        # special workaround for linux
        if sys.platform == "linux":
            options.add_argument(
                f'--user-data-dir={os.path.expanduser("~")}/snap/chromium/common/chromium/Default'
            )
        # special workaround for macos. Credits "Ambooj"
        elif sys.platform == "darwin":
            options.add_argument(
                f'--user-data-dir={os.path.expanduser("~")}/Library/Application Support/Google/Chrome'
            )
        else:
            options.add_argument(f"user-data-dir={self.profile_dir}")
        driver = None
        try:
            if not self.__automatic_login:
                print(
                    "\n\n\nYou need to login manually\n\n Press 'enter' to open the browser "
                )
                input()
                print(
                    "opening browser. Press enter once lgged in return back and press 'enter'. \n\nDO NOT CLOSE THE BROWSER"
                )
                time.sleep(5)

            driver = webdriver.Chrome(
                self.chromedriver_path, desired_capabilities=caps, options=options
            )

            logger.debug("opening https://in.tradingview.com ")
            driver.set_window_size(1920, 1080)
            driver.get("https://in.tradingview.com")
            time.sleep(5)

            return driver

        except Exception as e:
            if driver is not None:
                driver.quit()
            logger.error(e)

    @staticmethod
    def __get_token(driver: webdriver.Chrome):
        driver.get("https://www.tradingview.com/chart/")

        def process_browser_logs_for_network_events(logs):
            for entry in logs:
                log = json.loads(entry["message"])["message"]

                if "Network.webSocketFrameSent" in log["method"]:
                    if (
                        "set_auth_token" in log["params"]["response"]["payloadData"]
                        and "unauthorized_user_token"
                        not in log["params"]["response"]["payloadData"]
                    ):
                        yield log

        logs = driver.get_log("performance")
        events = process_browser_logs_for_network_events(logs)
        token = None
        for event in events:
            x = event
            token = json.loads(x["params"]["response"]["payloadData"].split("~")[-1])[
                "p"
            ][0]

        driver.quit()

        return token

    def __create_connection(self):
        logging.debug("creating websocket connection")
        self.ws = create_connection(
            "wss://data.tradingview.com/socket.io/websocket", headers=self.headers
        )

    @staticmethod
    def __filter_raw_message(text):
        try:
            found = re.search('"m":"(.+?)",', text).group(1)
            found2 = re.search('"p":(.+?"}"])}', text).group(1)

            return found, found2
        except AttributeError:
            logger.error("error in filter_raw_message")

    @staticmethod
    def __generate_session():
        stringLength = 12
        letters = string.ascii_lowercase
        random_string = "".join(random.choice(letters) for i in range(stringLength))
        return "qs_" + random_string

    @staticmethod
    def __generate_chart_session():
        stringLength = 12
        letters = string.ascii_lowercase
        random_string = "".join(random.choice(letters) for i in range(stringLength))
        return "cs_" + random_string

    @staticmethod
    def __prepend_header(st):
        return "~m~" + str(len(st)) + "~m~" + st

    @staticmethod
    def __construct_message(func, param_list):
        return json.dumps({"m": func, "p": param_list}, separators=(",", ":"))

    def __create_message(self, func, paramList):
        return self.__prepend_header(self.__construct_message(func, paramList))

    def __send_message(self, func, args):
        m = self.__create_message(func, args)
        if self.ws_debug:
            print(m)
        self.ws.send(m)

    @staticmethod
    def __create_df(raw_data, symbol):
        try:
            out = re.search('"s":\[(.+?)\}\]', raw_data).group(1)
            x = out.split(',{"')
            data = list()

            for xi in x:
                xi = re.split("\[|:|,|\]", xi)
                ts = datetime.datetime.fromtimestamp(float(xi[4]))
                data.append(
                    [
                        ts,
                        float(xi[5]),
                        float(xi[6]),
                        float(xi[7]),
                        float(xi[8]),
                        float(xi[9]),
                    ]
                )

            data = pd.DataFrame(
                data, columns=["datetime", "open", "high", "low", "close", "volume"]
            ).set_index("datetime")
            data.insert(0, "symbol", value=symbol)
            return data
        except AttributeError:
            logger.error("no data, please check the exchange and symbol")

    @staticmethod
    def __format_symbol(symbol, exchange, contract: int = None):

        if ":" in symbol:
            pass
        elif contract is None:
            symbol = f"{exchange}:{symbol}"

        elif isinstance(contract, int):
            symbol = f"{exchange}:{symbol}{contract}!"

        else:
            raise ValueError("not a valid contract")

        return symbol

    def get_hist(
        self,
        symbol: str,
        exchange: str = "NSE",
        interval: Interval = Interval.in_daily,
        n_bars: int = 10,
        fut_contract: int = None,
        extended_session: bool = False,
    ) -> pd.DataFrame:
        """get historical data

        Args:
            symbol (str): symbol name
            exchange (str, optional): exchange, not required if symbol is in format EXCHANGE:SYMBOL. Defaults to None.
            interval (str, optional): chart interval. Defaults to 'D'.
            n_bars (int, optional): no of bars to download, max 5000. Defaults to 10.
            fut_contract (int, optional): None for cash, 1 for continuous current contract in front, 2 for continuous next contract in front . Defaults to None.
            extended_session (bool, optional): regular session if False, extended session if True, Defaults to False.

        Returns:
            pd.Dataframe: dataframe with sohlcv as columns
        """
        symbol = self.__format_symbol(
            symbol=symbol, exchange=exchange, contract=fut_contract
        )

        interval = interval.value

        self.__create_connection()

        self.__send_message("set_auth_token", [self.token])
        self.__send_message("chart_create_session", [self.chart_session, ""])
        self.__send_message("quote_create_session", [self.session])
        self.__send_message(
            "quote_set_fields",
            [
                self.session,
                "ch",
                "chp",
                "current_session",
                "description",
                "local_description",
                "language",
                "exchange",
                "fractional",
                "is_tradable",
                "lp",
                "lp_time",
                "minmov",
                "minmove2",
                "original_name",
                "pricescale",
                "pro_name",
                "short_name",
                "type",
                "update_mode",
                "volume",
                "currency_code",
                "rchp",
                "rtc",
            ],
        )

        self.__send_message(
            "quote_add_symbols", [self.session, symbol, {"flags": ["force_permission"]}]
        )
        self.__send_message("quote_fast_symbols", [self.session, symbol])

        self.__send_message(
            "resolve_symbol",
            [
                self.chart_session,
                "symbol_1",
                '={"symbol":"'
                + symbol
                + '","adjustment":"splits","session":'
                + ('"regular"' if not extended_session else '"extended"')
                + "}",
            ],
        )
        self.__send_message(
            "create_series",
            [self.chart_session, "s1", "s1", "symbol_1", interval, n_bars],
        )
        self.__send_message("switch_timezone", [self.chart_session, "exchange"])

        raw_data = ""

        logger.debug(f"getting data for {symbol}...")
        while True:
            try:
                result = self.ws.recv()
                raw_data = raw_data + result + "\n"
            except Exception as e:
                logger.error(e)
                break

            if "series_completed" in result:
                break

        return self.__create_df(raw_data, symbol)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    tv = TvDatafeed(
        # auto_login=False,
    )
    print(tv.get_hist("CRUDEOIL", "MCX", fut_contract=1))
    print(tv.get_hist("NIFTY", "NSE", fut_contract=1))
    print(
        tv.get_hist(
            "EICHERMOT",
            "NSE",
            interval=Interval.in_1_hour,
            n_bars=500,
            extended_session=False,
        )
    )
