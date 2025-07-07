import os
import re
import csv
import time
import random
import datetime
import logging
import requests

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Nastavení loggeru
logging.basicConfig(
    level=logging.INFO,  # změň na DEBUG pro detailnější logování
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class BetsIo:
    def __init__(self):
        self.url = "https://fifa-api.tesseractparadox.com/odin/predictions"
        self.url_web = "https://www.bets.io/en"
        self.driver = webdriver.Firefox()
        self.match_name = None
        self.prediction_line = None
        self.prediction_odds = None
        self.roi = None
        self.what = None
        self.match_id = None
        self.results = {}
        self.urls = [
            'https://www.bets.io/en/sports/cybersport',
            'https://www.bets.io/en/sports/cs2'
        ]

    def login_and_wait(self):
        logger.info(f"Otevírám stránku pro přihlášení: {self.url_web}")
        self.driver.get(self.url_web)

        delay = random.randint(3, 14)
        logger.debug(f"Čekám náhodně {delay} sekund před ověřením přihlášení...")
        time.sleep(delay)

        try:
            WebDriverWait(self.driver, 300).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//span[contains(text(), 'Deposit') and contains(@class, 'sm:flex')]")
                )
            )
            logger.info("Přihlášení bylo úspěšně rozpoznáno.")
        except Exception as e:
            logger.error(f"Nepodařilo se přihlásit: {e}", exc_info=True)
            self.close()
            raise
            
    def load_api_data(self):
        logger.info("Čekám na data z API...")
        while True:
            try:
                logger.debug("Načítám data z API...")
                response = requests.get(self.url, timeout=5)
                response.raise_for_status()
                matches = response.json()

                if matches:
                    logger.info(f"Nalezeno {len(matches)} zápasů v API.")
                    parsed_matches = []
                    for match in matches:
                        parsed = {
                            "id": match['id'],
                            "name": match['name'],
                            "line": match['prediction']['line'],
                            "odd": match['prediction']['odd'],
                            "roi": match['prediction']['roi'] * 100,
                            "what": match['prediction']['what'],
                        }
                        logger.debug(f"Zpracován zápas: {parsed}")
                        parsed_matches.append(parsed)

                    time.sleep(5)
                    return parsed_matches

                else:
                    x = random.randint(1, 200)
                    if x > 185:
                        select_num = random.randint(0, len(self.urls) - 1)
                        if self.driver.current_url != self.urls[select_num]:
                            logger.info(f"Přecházím na náhodnou URL: {self.urls[select_num]}")
                            self.driver.get(self.urls[select_num])
                    else:
                        logger.debug("API nevrátilo zápasy, čekám 5 sekund...")
                        time.sleep(5)

            except requests.RequestException as e:
                logger.error(f"Chyba při načítání dat z API: {e}")
            time.sleep(10)  # počkej před dalším pokusem

    def collect_matches(self):
        logger.debug("Čekám na načtení týmů a zápasů...")

        try:
            urls = [
                'https://www.bets.io/en/sports/rsoccer/valhalla-cup-2025-week-28-l-109972190',
                'https://www.bets.io/en/sports/rsoccer/valhalla-cup-3-2025-week-28-l-109972250',
                'https://www.bets.io/en/sports/rsoccer/valkyrie-cup-2025-week-28-l-109972238',
            ]

            for url in urls:
                try:
                    logger.info(f"Načítám stránku: {url}")
                    self.driver.get(url)
                    time.sleep(10) 

                    iframe = WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located((By.TAG_NAME, "iframe"))
                    )
                    self.driver.switch_to.frame(iframe)

                    WebDriverWait(self.driver, 20).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.sb-BettingTable-link[data-test-id='game-link']"))
                    )

                    game_links = self.driver.find_elements(By.CSS_SELECTOR, "a.sb-BettingTable-link[data-test-id='game-link']")

                    for game in game_links:
                        teams = game.find_elements(By.CSS_SELECTOR, "span.sb-TeamColumn-name")
                        if len(teams) >= 2:
                            team1 = teams[0].get_attribute("title")
                            team2 = teams[1].get_attribute("title")
                            matchup = f"{team1} vs {team2}"

                            href = game.get_attribute("href")
                            self.results.update({matchup: href})

                    logger.info(f"Načteno {len(self.results)} zápasů.")


                except Exception as e:
                    logger.error(f"Chyba při zpracování URL {url}: {str(e)}")


        except Exception as main_e:
            logger.critical(f"Fatální chyba: {str(main_e)}")

    def count_bet_value(self, additional_bankroll, number_of_units, max_stake):
        balance = 0.0
        try:
            self.driver.switch_to.default_content()
            wait = WebDriverWait(self.driver, 10)

            btc_icon = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "img[alt='BTC icon']"))
            )
            parent = btc_icon.find_element(By.XPATH, "..")
            container = parent.find_element(By.XPATH, "ancestor::div[contains(@class, 'flex')]")
            value_div = container.find_element(By.XPATH, ".//div[contains(@class, 'text-right')]")

            balance_str = value_div.text.strip().replace(',', '.')
            balance = float(balance_str)

            logger.info(f"Aktuální stav BTC: {balance}")
        except Exception as e:
            logger.error(f"Nepodařilo se najít BTC zůstatek: {e}")
            # Pokud chceš vracet None při chybě, odkomentuj následující řádek
            # return None

        bet_value = (balance + additional_bankroll) / number_of_units
        
        formatted_bet_value = f"{bet_value:.6f}"
        logger.info(f"Hodnota sázky: {formatted_bet_value}")

        return formatted_bet_value



    def go_to_match_bet(self):

        logger.info(f"Hledám zápas: {self.match_name}")

        for text,href in self.results.items():
            parts = text.split(' vs ')
            swapped_string = f"{parts[1]} vs {parts[0]}"

            if text == self.match_name or swapped_string == self.match_name:
                logger.info(f"Zápas nalezen: {text}. Přecházím na stránku: {href}")
                try:
                    self.driver.get(href)
                    delay = random.randint(3, 14)
                    logger.debug(f"Čekám {delay} sekund před pokračováním...")
                    time.sleep(delay)
                    logger.info("Úspěšně načtena stránka zápasu.")
                    return
                except Exception as e:
                    logger.error(f"Chyba při přechodu na stránku zápasu: {e}", exc_info=True)
                    return



    def find_a_bet(self):
        
        logger.info(f"Hledám container pro sázku typu '{self.what}'...")

        try:
            time.sleep(5)
            wait = WebDriverWait(self.driver, 20)

            # Přepnutí zpět na hlavní stránku - pro jistotu
            self.driver.switch_to.default_content()

            # Čekání na tlačítko 'All' a kliknutí
            button_all = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-test-id='all']")))
            button_all.click()
            logger.info("Kliknuto na záložku 'All'.")

            # Čekání na načtení tabulky sázek
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.sb-MarketTable")))

            # Vyhledání všech sázek podle názvu marketu
            markets = self.driver.find_elements(By.XPATH, "//span[contains(text(), 'Match Total Goals')]")
            found = False

            for market_name in markets:
                container = market_name.find_element(By.XPATH, "./ancestor::div[contains(@class,'sb-MarketTable')]")
                buttons = container.find_elements(By.CSS_SELECTOR, "button.sb-Outcome")

                for btn in buttons:
                    label = btn.find_element(By.CSS_SELECTOR, "span.sb-Outcome-label").get_attribute("title")
                    odd = btn.find_element(By.CSS_SELECTOR, "div.sb-Outcome-odds").text

                    if label == self.what and str(self.prediction_line) in market_name.text and odd == str(self.prediction_odds):
                        logger.info(f"Nalezena správná sázka '{label}' s kurzem {odd}.")

                        # Počkej na zmizení toastu
                        toast_hidden = False
                        try:
                            WebDriverWait(self.driver, 10).until_not(
                                EC.presence_of_element_located((By.CSS_SELECTOR, ".Toastify__toast-container"))
                            )
                            toast_hidden = True
                        except TimeoutException:
                            logger.warning("Toast nezmizel, pokusím se o kliknutí skrze JavaScript.")

                        # Pokud toast zmizel, klasické kliknutí
                        if toast_hidden:
                            try:
                                btn.click()
                                logger.info("Kliknutí na sázku proběhlo klasicky.")
                            except ElementClickInterceptedException:
                                logger.warning("Tlačítko překryto, používám JavaScriptové kliknutí.")
                                self.driver.execute_script("arguments[0].click();", btn)
                        else:
                            # Toast nezmizel - rovnou JavaScriptové kliknutí
                            try:
                                self.driver.execute_script("arguments[0].click();", btn)
                                logger.info("Kliknutí skrze JavaScript proběhlo.")
                            except Exception:
                                logger.error("Nepodařilo se kliknout na sázku ani přes JavaScript.", exc_info=True)
                                return

                        found = True
                        break

                if found:
                    break

            if not found:
                logger.warning("Požadovaná sázka nenalezena.")

        except Exception:
            logger.error("Nepodařilo se dokončit vyhledání a kliknutí na sázku.", exc_info=True)



    def place_bet(self, bet_value):
        self.driver.switch_to.default_content()
        wait = WebDriverWait(self.driver, 30)

        try:
            stake_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[data-test-id='bet-stake-input']")))

            current_value = stake_input.get_attribute('value')
            for _ in current_value:
                stake_input.send_keys(Keys.BACKSPACE)
                time.sleep(0.3)

            time.sleep(0.3)

            for c in str(bet_value):
                stake_input.send_keys(c)
                time.sleep(0.1)

            self.driver.execute_script("""
                let el = arguments[0];
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
                el.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true }));
                el.blur();
            """, stake_input)

            time.sleep(0.5)

            place_bet_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-test-id='place-bet-button']")))
            wait.until(lambda d: place_bet_button.get_attribute("disabled") is None)

            self.driver.execute_script("arguments[0].click();", place_bet_button)
            logger.info("Tlačítko Place Bet bylo stisknuto (JS klik).")

            # Počkej na zmizení potvrzovacího toastu, pokud tam je
            try:
                WebDriverWait(self.driver, 10).until_not(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".Toastify__toast-container"))
                )
                logger.info("Potvrzovací toast zmizel.")
            except TimeoutException:
                logger.warning("Toast nezmizel, pokračuji dál.")

            time.sleep(0.5)

            # Vyhledání tlačítka Clear
            clear_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[title="Clear"]')))
            self.driver.execute_script("arguments[0].click();", clear_button)
            logger.info("Tlačítko Clear bylo stisknuto (JS klik).")

            logger.info("Sázka úspěšně zadána a potvrzena.")

        except TimeoutException:
            logger.error("Nepodařilo se dokončit sázku - input nebo tlačítko nenalezeno.")
        except Exception as e:
            logger.error("Neočekávaná chyba při zadávání sázky.", exc_info=True)


    def log_bet_to_csv(self, bet_value):
        filename = "shuffle_bets.csv"
        file_exists = os.path.isfile(filename)

        with open(filename, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if not file_exists:
                # Zapiš hlavičku, pokud soubor neexistuje
                writer.writerow(["Timestamp", "id", "Match", "What", "Line", "Odds", "ROI", "Bet Value"])

            writer.writerow([
                datetime.datetime.now().isoformat(),
                self.match_id,
                self.match_name,
                self.what,
                self.prediction_line,
                self.prediction_odds,
                round(self.roi, 2),
                bet_value
            ])
    
    def close(self):
        if self.driver:
            self.driver.quit()
    
    def run(self):
        try:
            self.login_and_wait()
            last_matches = set()

            while True:
                #<= datetime.time(24, 0)
                now = datetime.datetime.now().time()
                if datetime.time(7, 0) <= now:
                    try:
                        matches = self.load_api_data()
                        new_matches = [m for m in matches if m["id"] not in last_matches]

                        if not new_matches:
                            time.sleep(25)

                        if new_matches:
                            logger.info("Zjištěny nové zápasy, načítám data...")
                            self.results = {}
                            self.collect_matches()
                            
                            
                            bet_value = self.count_bet_value(additional_bankroll= 0.0001, number_of_units = 20, max_stake = 80)
                            logger.info(f"Hodnota sazky {bet_value}")
                            for match in matches:
                                try:
                                    self.match_name = match["name"]
                                    self.prediction_line = match["line"]
                                    self.roi = match["roi"]
                                    self.prediction_odds = "{:.2f}".format(float(match["odd"]))
                                    self.match_id = match["id"]
                                    self.what = match["what"]
                                    
                                    if self.match_id not in last_matches: 
                                        logger.info(f"Nový zápas: {self.match_name}, predikce: {self.what} {self.prediction_line} @ {self.prediction_odds}")

                                        self.go_to_match_bet()
                                        self.find_a_bet()

                                        self.place_bet(bet_value=bet_value)
                                        self.log_bet_to_csv(bet_value=bet_value)

                                        last_matches.add(self.match_id)  
                                        time.sleep(random.randint(2, 5))

                                except Exception as match_error:
                                    logger.error(f"Chyba při zpracování zápasu '{match['name']}': {match_error}", exc_info=True)       
                        else:
                            logger.debug("Žádné nové zápasy.")

                    except Exception as loop_error:
                        logger.error(f"Chyba během načítání nebo zpracování zápasů: {loop_error}", exc_info=True)

                else:
                    logger.info("Mimo provozních hodin (08:00–23:00). Ukončuji běh.")
                    break
        finally:
            self.close()


# Spuštění
if __name__ == "__main__":
    bot = BetsIo()
    bot.run()        
