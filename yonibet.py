import requests
import time
import random
import datetime
import logging
import csv
import os
from dotenv import load_dotenv

load_dotenv()

SHUFFLE_ADDITIONAL_BANKROLL = float(os.getenv('SHUFFLE_ADDITIONAL_BANKROLL'))
SHUFFLE_NUMBER_OF_UNITS = float(os.getenv('SHUFFLE_NUMBER_OF_UNITS'))
SHUFFLE_MAX_STAKE = float(os.getenv('SHUFFLE_MAX_STAKE'))
SHUFFLE_BET_FROM = int(os.getenv('SHUFFLE_BET_FROM'))
SHUFFLE_BET_TO = int(os.getenv('SHUFFLE_BET_TO'))



import requests
import time
import random
import datetime
import logging
import csv
import os


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Nastavení loggeru na začátku souboru
logging.basicConfig(
    level=logging.INFO,  # nebo DEBUG pro více detailů
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class ShuffleBot:
    def __init__(self):
        self.url = "https://fifa-api.tesseractparadox.com/odin/predictions"
        self.url_web = "https://yonibet.eu/ca/sport?bt-path=%2Fesoccer-137"
        self.driver = webdriver.Firefox()
        self.match_name = None
        self.prediction_line = None
        self.prediction_odds = None
        self.roi = None
        self.what = None
        self.match_id = None
        self.results = {}
        self.urls = [
                'https://yonibet.eu/ca/sport',
                'https://yonibet.eu/ca/games/category/popular',
                'https://yonibet.eu/ca/play/125837-aviatrix',
                'https://yonibet.eu/ca/play/130602-jackass-gold-hold-amp-win-buy-bonus',
                'https://yonibet.eu/ca/sport?bt-path=%2Fcounter-strike-109',
                'https://yonibet.eu/ca/sport?bt-path=%2Fesoccer%2Fefootball%2Fa--valhalla-cup-2x4-min-2538512713961840683',
                'https://yonibet.eu/ca/sport?bt-path=%2Frugby-league-59',
                'https://yonibet.eu/ca/sport?bt-path=%2Fbasketball%2Fusa%2Fnba-1669819088278523904'
            ]

            
    def login_and_wait(self):
        login_url = self.url_web
        logger.info(f"Otevírám stránku pro přihlášení: {login_url}")
        self.driver.get(login_url)

        delay = random.randint(3, 14)
        logger.debug(f"Čekám náhodně {delay} sekund před ověřením přihlášení...")
        time.sleep(delay)

        try:
            WebDriverWait(self.driver, 300).until(
                EC.presence_of_element_located((By.ID, "headerAccountButton"))
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
                logger.debug("Načítání dat z API...")
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
                            "what": match['prediction']['what']
                        }
                        logger.debug(f"Zpracován zápas: {parsed}")
                        parsed_matches.append(parsed)
                        
                    time.sleep(5)
                    return parsed_matches

            except requests.RequestException as e:
                logger.error(f"Chyba při načítání dat z API: {e}")
            
            if not matches:
                x = random.randint(1, 200)
                i = 1
                if x > 185:
                    while i > 0:
                        select_num = random.randint(0, len(self.urls)-1)
                        
                        if self.driver.current_url != self.urls[select_num]:
                            self.driver.get(self.urls[select_num])
                            i = 0
                else:
                    time.sleep(5)

    
    
    def collect_matches(self):
        self.driver.get(self.url_web)

        xpath = '//div[contains(@class, "bt279") and (contains(text(), "Valhalla") or contains(text(), "Valkyrie"))]'
        logger.debug("Čekám na načtení odkazů na zápasy...")
        WebDriverWait(self.driver, 200).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )

        delay = random.randint(3, 14)
        time.sleep(delay)

        elements = self.driver.find_elements(By.XPATH, xpath)
        valhalla_links = [(el.text, el.get_attribute('href')) for el in elements]
        logger.info(f"Nalezeno {len(valhalla_links)} odkazů na zápasy.")

        for text, href in valhalla_links:
            logger.info(f"Otevírám zápas: {text} ({href})")
            self.driver.get(href)
            time.sleep(random.randint(3, 14))

            try:
                class_name = 'div.bt2068[data-editor-id="eventCardStatusLabel"]'
                logger.debug("Čekám na načtení týmů v zápase...")
                WebDriverWait(self.driver, 100).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, class_name))
                )

                spans = self.driver.find_elements(By.CSS_SELECTOR, class_name)
                for span in spans:
                    try:
                        # Předpokládám, že chceme najít odkaz (<a>), ne <div>, protože href je u <a>
                        parent = span.find_element(By.XPATH, './ancestor::a[1]')
                        match_href = parent.get_attribute('href')
                        team_text = span.text.strip()

                        if match_href in self.results:
                            self.results[match_href] += " vs " + team_text
                            logger.debug(f"Zápas aktualizován: {self.results[match_href]}")
                        else:
                            self.results[match_href] = team_text
                            logger.debug(f"Zápas nalezen: {match_href} -> {team_text}")
                    except Exception as e:
                        logger.warning(f"Chyba při zpracování týmu: {e}", exc_info=True)

            except Exception as e:
                logger.error(f"Chyba při načítání detailu zápasu ({href}): {e}", exc_info=True)


    def count_bet_value(self, additional_bankroll, number_of_units, max_stake):
        wait = WebDriverWait(self.driver, 10)

        # Čekáme na načtení balance z elementu podle ID
        balance_element = wait.until(
            EC.presence_of_element_located((By.ID, "headerDepositButtonValue"))
        )

        balance_str = balance_element.text.strip()
        balance = float(balance_str.replace('€', '').replace(',', '').strip())

        bet_value = round(((balance + SHUFFLE_ADDITIONAL_BANKROLL) / SHUFFLE_NUMBER_OF_UNITS) / 5) * 5

        return min(bet_value, SHUFFLE_MAX_STAKE)
        
    def go_to_match_bet(self):
        
        logger.info(f"Hledání zápasu: {self.match_name}")
        for href, text in self.results.items():
            
            parts = text.split(' vs ', 1) 
            
            if len(parts) != 2:
                logger.error(f"Neplatný formát zápasu: {text}")
                return
            
            team_1, team_2 = parts
            swapped_string = f"{team_2} vs {team_1}"

            if (text == self.match_name) or (swapped_string == self.match_name):
                logger.info(f"Zápas nalezen: {text}. Pokouším se načíst stránku: {href}")
                try:
                    self.driver.get(href)
                    delay = random.randint(3, 14)
                    logger.debug(f"Náhodné zpoždění {delay} sekund před pokračováním...")
                    time.sleep(delay)

                    # Úspěšný přechod (případně můžeš přidat i kontrolu nějakého prvku na stránce)
                    logger.info("Úspěšně přejito na stránku zápasu.")
                    return  # nebo break, pokud chceš pokračovat dál v cyklu

                except Exception as e:
                    logger.error(f"Nepodařilo se přejít na stránku zápasu: {e}", exc_info=True)
                    return  # nebo continue, podle toho, jaký má být další krok

        logger.warning(f"Zápas {self.match_name} nebyl nalezen mezi výsledky.")

    
    def find_a_bet(self):
        try:
            expected_text = f"{self.what.lower()} {self.prediction_line}".strip()
            logger.info(f"Hledám sázku: '{expected_text}' s kurzem {self.prediction_odds}...")

            container = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-editor-id='tableMarketWrapper']"))
            )

            options = container.find_elements(By.CSS_SELECTOR, "div[data-editor-id='tableOutcomePlate']")
            logger.debug(f"Nalezeno {len(options)} možností sázek")

            for option in options:
                try:
                    bet_text_element = option.find_element(By.CSS_SELECTOR, "div[data-editor-id='tableOutcomePlateName'] span")
                    bet_text = bet_text_element.text.strip().lower()

                    odds_element = option.find_element(By.CSS_SELECTOR, "div span")
                    odds_text = odds_element.text.strip()

                    logger.debug(f"Možnost: '{bet_text}' @ {odds_text}")

                    if bet_text == expected_text and odds_text == str(self.prediction_odds):
                        try:
                            button = option.find_element(By.TAG_NAME, "button")
                        except Exception:
                            button = option

                        self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                        time.sleep(0.5)

                        try:
                            button.click()
                            logger.info(f"Kliknuto na sázku: {bet_text} @ {odds_text}")
                        except Exception:
                            self.driver.execute_script("arguments[0].click();", button)
                            logger.warning("Fallback: kliknutí přes JavaScript.")
                        break

                except Exception as e:
                    logger.warning(f"Chyba při zpracování možnosti sázky: {e}")

        except Exception as e:
            logger.error(f"Nepodařilo se najít nebo zpracovat sázku: {e}")



    
    def place_bet(self, bet_value):
        try:
            input_elem = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.CurrencyInput_currencyInput__YGw5R input'))
            )
            input_elem.clear()
            try:
                input_elem.send_keys(str(bet_value))
                logger.info(f"Zadána částka: {bet_value}")
            except Exception as e_inner:
                logger.warning(f"send_keys selhalo pro hodnotu {bet_value}, zkouším JS metodu... ({e_inner})")
                self.driver.execute_script("arguments[0].value = arguments[1];", input_elem, str(bet_value))
        except (TimeoutException, NoSuchElementException) as e_outer:
            logger.error(f"Prvek pro zadání částky nebyl nalezen nebo není interaktivní: {e_outer}", exc_info=True)
            logger.debug("Výstup HTML (zkrácen):\n" + self.driver.page_source[:2000])
            return

        time.sleep(random.randint(2, 5))

        # klikni na tlačítko "Place Bets"
        try:
            bet_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//button[contains(translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'place bets')]"
                ))
            )
            logger.info("Tlačítko 'Place Bets' nalezeno.")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", bet_button)
            time.sleep(random.randint(2, 5))
            bet_button.click()
            logger.info("Sázka úspěšně podána.")

            # potvrzení kliknutí na "Done"
            done_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//button[contains(translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'done')]"
                ))
            )
            logger.info("Tlačítko 'Done' nalezeno.")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", done_button)
            time.sleep(random.randint(2, 5))
            done_button.click()
            logger.info("Potvrzení sázky úspěšně dokončeno.")
        except Exception as e:
            logger.error(f"Chyba při klikání na 'Place Bets' nebo 'Done': {e}", exc_info=True)
            return

        # návrat na homepage nebo jinou rozumnou akci
        self.driver.get(self.url_web)
        print("Čekám na další sázku...")    

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
                now = datetime.datetime.now().time()
                if datetime.time(SHUFFLE_BET_FROM, 0) <= now <= datetime.time(SHUFFLE_BET_TO, 0):
                    try:
                        matches = self.load_api_data()
                        new_matches = [m for m in matches if m["id"] not in last_matches]

                        if not new_matches:
                            time.sleep(30)

                        if new_matches:
                            logger.info("Zjištěny nové zápasy, načítám data...")
                            self.results = {}
                            self.collect_matches()
                            
                            bet_value = self.count_bet_value(additional_bankroll = 200 , number_of_units = 20, max_stake = 80)
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
    bot = ShuffleBot()
    bot.run()        
