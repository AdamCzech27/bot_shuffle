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
        self.url_web = "https://shuffle.com/sports/efootball/efootball-international"
        self.driver = webdriver.Firefox()
        self.match_name = None
        self.prediction_line = None
        self.prediction_odds = None
        self.roi = None
        self.what = None
        self.match_id = None
        self.results = {}

            
    def login_and_wait(self):
        login_url = self.url_web
        logger.info(f"Otevírám stránku pro přihlášení: {login_url}")
        self.driver.get(login_url)

        delay = random.randint(3, 14)
        logger.debug(f"Čekám náhodně {delay} sekund před ověřením přihlášení...")
        time.sleep(delay)

        try:
            WebDriverWait(self.driver, 300).until(
                EC.presence_of_element_located((By.XPATH, "//span[text()='Wallet']"))
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
                            "what": match['prediction']['what'],
                            "tour": match['prediction']['tournament']
                        }
                        logger.debug(f"Zpracován zápas: {parsed}")
                        parsed_matches.append(parsed)
                        
                    time.sleep(5)
                    return parsed_matches

            except requests.RequestException as e:
                logger.error(f"Chyba při načítání dat z API: {e}")

            # Počkej před dalším pokusem
            time.sleep(10)

    
    
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
                    logging.info(f"Načítám stránku: {url}")
                    driver.get(url)
                    time.sleep(15)

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

                    matches_dict = driver.execute_script(js_extract_matches)
                    if matches_dict:
                        self.results.update(matches_dict)
                        logging.info(f"Načteno {len(matches_dict)} zápasů.")
                    else:
                        logging.warning("Žádné zápasy nebyly nalezeny.")
                except Exception as e:
                    logging.error(f"Chyba při zpracování URL {url}: {str(e)}")

        except Exception as main_e:
            logging.critical(f"Fatální chyba: {str(main_e)}")

                
    def count_bet_value(self, additional_bankroll, number_of_units, max_stake):
        
        wait = WebDriverWait(self.driver, 10)
        balance_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "span[data-testid='balance']")))
        balance_str = balance_element.text.strip()
        balance = float(balance_str.replace('$', '').replace(',', ''))
        bet_value = round(((balance + additional_bankroll) / number_of_units) * 2) / 2

        return min(bet_value, max_stake)
        
    def go_to_match_bet(self):
        
        normalize = lambda s: re.sub(r'\s+', ' ', s.strip())

        logger.info(f"Hledání zápasu: {self.match_name}")
        match_name = normalize(self.match_name)

        for href, text in self.results.items():
            text = normalize(text)
            parts = text.split(' vs ', 1)

            if len(parts) != 2:
                logger.error(f"Neplatný formát zápasu: {text}")
                continue

            team_1, team_2 = parts
            swapped_string = f"{team_2} vs {team_1}"

            if text == match_name or swapped_string == match_name:
                logger.info(f"Zápas nalezen: {text}. Pokouším se načíst stránku: {href}")
                try:
                    self.driver.get(href)
                    delay = random.randint(3, 14)
                    logger.debug(f"Náhodné zpoždění {delay} sekund před pokračováním...")
                    time.sleep(delay)
                    logger.info("Úspěšně přejito na stránku zápasu.")
                    return
                except Exception as e:
                    logger.error(f"Nepodařilo se přejít na stránku zápasu: {e}", exc_info=True)
                    return

        logger.warning(f"Zápas {self.match_name} nebyl nalezen mezi výsledky.")

    
    def find_a_bet(self):

        over_under_class_name = (
            "LadderMarketLayout_teamA__qsCMN" if self.what == 'over' else "LadderMarketLayout_teamB__dH6dD"
        )

        try:
            logger.info(f"Hledám container pro sázku typu '{self.what}'...")
            container = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, over_under_class_name))
            )

            elements = container.find_elements(By.CLASS_NAME, "SportsBetSelectionButton_eventText__FJ6GL")
            logger.debug(f"Nalezeno {len(elements)} možností sázek")

            for element in elements:
                if element.text == str(self.prediction_line):
                    try:
                        logger.info(f"Hledám tlačítko pro hodnotu: {self.prediction_line}, kurz: {self.prediction_odds}")

                        xpath = (
                            f"//div[contains(@class, '{over_under_class_name}')]"
                            f"//button[p[1][text()='{self.prediction_line}'] and p[2]//span[text()='{self.prediction_odds}']]"
                        )

                        button = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, xpath))
                        )

                        self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                        time.sleep(0.5)

                        try:
                            button.click()
                            logger.info(f"Tlačítko kliknuto pro hodnotu: {self.prediction_line} @ {self.prediction_odds}")
                        except Exception:
                            self.driver.execute_script("arguments[0].click();", button)
                            logger.warning("Fallback: kliknutí provedeno přes JavaScript.")

                        break

                    except Exception as e:
                        logger.error(f"Chyba při pokusu o kliknutí na tlačítko: {e}", exc_info=True)

        except Exception as e:
            logger.error("Container nebo tlačítko nenalezeno.", exc_info=True)

        time.sleep(random.randint(2, 5))

    
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
            return  # místo continue

        time.sleep(random.randint(2, 5))

        # klikni na tlačítko "Bet"
        try:
            bet_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') = 'place bets']"))
            )
            self.driver.execute_script("arguments[0].scrollIntoView(true);", bet_button)
            time.sleep(random.randint(2, 5))
            bet_button.click()
            logger.info("Sázka úspěšně podána.")

            # potvrzení kliknutí na "Done"
            done_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') = 'done']"))
            )
            self.driver.execute_script("arguments[0].scrollIntoView(true);", done_button)
            time.sleep(random.randint(2, 5))
            done_button.click()
            logger.info("Potvrzení sázky úspěšně dokončeno.")
        except Exception as e:
            logger.error(f"Chyba při klikání na 'Bet' nebo 'Done': {e}", exc_info=True)
            return  # místo continue

        # návrat na homepage nebo jinou rozumnou akci
        self.driver.get(self.url_web)
        print("Cekam na dalsi sazku...")       

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
                if datetime.time(7, 0) <= now <= datetime.time(23, 0):
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
#####



from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import json
import time

options = webdriver.FirefoxOptions()
driver = webdriver.Firefox(options=options)

driver.get("https://yonibet.eu/ca/sport?bt-path=%2Fesoccer%2Fefootball%2Fa--valhalla-cup-2x4-min%2Fogc-nice-junior-paris-saint-germain-bony-2543858739027513344")

# počkej na načtení (lepší je explicitní wait, ale tady pro příklad sleep)
time.sleep(15)  # Počkej na načtení stránky a dynamického obsahu


js_click_over = """
let shadowHost = document.querySelector('#bt-inner-page');
if (!shadowHost) return 'No shadowHost';

let shadowRoot = shadowHost.shadowRoot;
if (!shadowRoot) return 'No shadowRoot';

let markets = shadowRoot.querySelectorAll('[data-editor-id="tableMarketWrapper"]');

for (let market of markets) {
    let outcomes = market.querySelectorAll('[data-editor-id="tableOutcomePlate"]');
    for (let outcome of outcomes) {
        let nameEl = outcome.querySelector('[data-editor-id="tableOutcomePlateName"] span');
        if (nameEl && nameEl.textContent.trim().toLowerCase().includes('over')) {
            outcome.click();
            return 'Clicked on: ' + nameEl.textContent.trim();
        }
    }
}
return 'No element with "over" found';
"""

result = driver.execute_script(js_click_over)
print(result)




######


from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import json
import time

options = webdriver.FirefoxOptions()
driver = webdriver.Firefox(options=options)

driver.get("https://yonibet.eu/ca/sport?bt-path=%2Fesoccer%2Fefootball%2Fa--valhalla-cup-2x4-min%2Fogc-nice-junior-paris-saint-germain-bony-2543858739027513344")

# počkej na načtení (lepší je explicitní wait, ale tady pro příklad sleep)
time.sleep(15)  # Počkej na načtení stránky a dynamického obsahu


js_code = """
let shadowHost = document.querySelector('#bt-inner-page');
if (!shadowHost) return null;

let shadowRoot = shadowHost.shadowRoot;
if (!shadowRoot) return null;

let markets = shadowRoot.querySelectorAll('[data-editor-id="tableMarketWrapper"]');
let result = [];

markets.forEach(market => {
    let outcomes = market.querySelectorAll('[data-editor-id="tableOutcomePlate"]');
    let match = [];

    outcomes.forEach(outcome => {
        let nameEl = outcome.querySelector('[data-editor-id="tableOutcomePlateName"] span');
        let oddEl = outcome.querySelector('span.bt469');
        if (nameEl && oddEl) {
            match.push({
                'team': nameEl.textContent.trim(),
                'odd': oddEl.textContent.trim()
            });
        }
    });

    if (match.length >= 2) {
        result.push(match);
    }
});

return JSON.stringify(result);
"""

data_json = driver.execute_script(js_code)
data = json.loads(data_json) if data_json else []

print(data)

driver.quit()
