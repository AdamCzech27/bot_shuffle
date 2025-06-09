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
        logger.info(f"Otevírám stránku pro přihlášení: {self.url_web}")
        self.driver.get(self.url_web)

        delay = random.randint(3, 14)
        logger.debug(f"Čekám náhodně {delay} sekund před ověřením přihlášení...")
        time.sleep(delay)

        try:
            WebDriverWait(self.driver, 300).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "span#headerDepositButtonValue.btnDeposit__text.truncate")
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
                time.sleep(5)  # počkej před dalším pokusem

    def collect_matches(self):
        logger.debug("Čekám na načtení týmů a zápasů...")

        try:
            urls = [
                'https://yonibet.eu/ca/sport?bt-path=%2Fesoccer%2Fefootball%2Fa--valhalla-cup-2x4-min-2543590749606391853',
                'https://yonibet.eu/ca/sport?bt-path=%2Fesoccer%2Fefootball%2Fa--valkyrie-cup-2x4-min-2543607148261290024',
                'https://yonibet.eu/ca/sport?bt-path=%2Fesoccer%2Fefootball%2Fa--valhalla-cup-3-2x4-min-2543608703408549900',
            ]

            for url in urls:
                try:
                    logger.info(f"Načítám stránku: {url}")
                    self.driver.get(url)
                    time.sleep(3)

                    js_extract_matches = r"""
                        let shadowHost = document.querySelector('#bt-inner-page');
                        if (!shadowHost) return null;
                        let shadowRoot = shadowHost.shadowRoot;
                        if (!shadowRoot) return null;

                        let links = shadowRoot.querySelectorAll("a[data-editor-id='eventCardContent']");
                        let result = {};

                        links.forEach(link => {
                            let text = link.textContent.trim();
                            text = text.replace(/\s+/g, ' ');
                            let match = text.match(/([A-Za-z\s]+?\([A-Za-z]+\))\s*([A-Za-z\s]+?\([A-Za-z]+\))/);
                            if (match && match.length === 3) {
                                let team1 = match[1].trim();
                                let team2 = match[2].trim();
                                let key = `${team1} vs ${team2}`;
                                result[key] = link.href;
                            }
                        });
                        return result;
                    """

                    matches_dict = self.driver.execute_script(js_extract_matches)
                    if matches_dict:
                        self.results.update(matches_dict)
                        logger.info(f"Načteno {len(matches_dict)} zápasů.")
                    else:
                        logger.warning("Žádné zápasy nebyly nalezeny.")
                except Exception as e:
                    logger.error(f"Chyba při zpracování URL {url}: {str(e)}")

        except Exception as main_e:
            logger.critical(f"Fatální chyba: {str(main_e)}")
        print(self.results)

    def count_bet_value(self, additional_bankroll, number_of_units, max_stake):
        wait = WebDriverWait(self.driver, 10)
        balance_element = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "span#headerDepositButtonValue.btnDeposit__text.truncate")
        ))

        balance_str = balance_element.text.strip()
        balance_clean = balance_str.replace('€', '').replace(',', '.').strip()

        try:
            balance = float(balance_clean)
        except ValueError as ve:
            logger.error(f"Chybný formát zůstatku: {balance_clean}", exc_info=True)
            balance = 0.0

        bet_value = round(((balance + additional_bankroll) / number_of_units) * 2) / 2
        return min(bet_value, max_stake)

    def go_to_match_bet(self):
        normalize = lambda s: re.sub(r'\s+', ' ', s.strip())
        logger.info(f"Hledám zápas: {self.match_name}")
        match_name = normalize(self.match_name)

        for href, text in self.results.items():
            text = normalize(text)
            parts = text.split(' vs ', 1)
            print([text,match_name,swapped_string])
            if len(parts) != 2:
                logger.error(f"Neplatný formát zápasu: {text}")
                continue

            team_1, team_2 = parts
            swapped_string = f"{team_2} vs {team_1}"
            
            if text == match_name or swapped_string == match_name:
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

        logger.warning(f"Zápas {self.match_name} nebyl nalezen v seznamu výsledků.")

    
    def find_a_bet(self):
        try:
            logger.info(f"Hledám container pro sázku typu '{self.what}'...")
            time.sleep(15)

            js_click_over = f"""
            let shadowHost = document.querySelector('#bt-inner-page');
            if (!shadowHost) return 'No shadowHost';

            let shadowRoot = shadowHost.shadowRoot;
            if (!shadowRoot) return 'No shadowRoot';

            let markets = shadowRoot.querySelectorAll('[data-editor-id="tableMarketWrapper"]');
            let logs = [];

            for (let market of markets) {{
                let outcomes = market.querySelectorAll('[data-editor-id="tableOutcomePlate"]');
                for (let outcome of outcomes) {{
                    let nameEl = outcome.querySelector('[data-editor-id="tableOutcomePlateName"]');

                    if (nameEl) {{
                        let nameText = nameEl.textContent.trim().toLowerCase();
                        logs.push('Nalezen: ' + nameText);

                        if (nameText.includes('{self.what.lower()} {self.prediction_line}')) {{
                            outcome.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            outcome.click();
                            return '✅ Kliknuto na: ' + nameText;
                        }}
                    }}
                }}
            }}
            return '❌ Nenalezen žádný výběr {self.what} {self.prediction_line}.\\n' + logs.join(' | ');
            """

            result = self.driver.execute_script(js_click_over)
            logger.info(f"Výsledek kliknutí: {result}")

        except Exception as e:
            logger.error("Nepodarilo se kliknout na sazku", exc_info=True)

        time.sleep(random.randint(2, 5))

    
    def place_bet(self, bet_value):
        try:
            js_set_stake_and_place_bet = f"""
            let shadowHost = document.querySelector('#bt-inner-page');
            if (!shadowHost) return 'No shadowHost';

            let shadowRoot = shadowHost.shadowRoot;
            if (!shadowRoot) return 'No shadowRoot';

            // Najdeme input pro sázku
            let stakeInput = shadowRoot.querySelector('label[data-editor-id="betslipStakeInput"] input');
            if (!stakeInput) return '❌ Nenalezen input pro sázku';

            // Nastavíme hodnotu sázky (např. 10)
            stakeInput.value = {str(bet_value)};

            // Vyvoláme událost input, aby to stránka zaregistrovala
            stakeInput.dispatchEvent(new Event('input', { bubbles: true }));

            // Najdeme tlačítko Place Bet a klikneme na něj
            let placeBetBtn = shadowRoot.querySelector('[data-editor-id="betslipPlaceBetButton"]');
            if (!placeBetBtn) return '❌ Nenalezeno tlačítko Place Bet';

            placeBetBtn.click();
            return '✅ Sázka nastavena na 10 a kliknuto na Place Bet';
            """

            self.driver.execute_script(js_set_stake_and_place_bet)
            
        except (TimeoutException, NoSuchElementException) as e_outer:
            logger.error(f"Prvek pro zadání částky nebyl nalezen nebo není interaktivní: {e_outer}", exc_info=True)
            logger.debug("Výstup HTML (zkrácen):\n" + self.driver.page_source[:2000])
            return  # místo continue

        time.sleep(random.randint(2, 5))
     

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
