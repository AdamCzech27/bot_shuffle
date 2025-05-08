import requests
import time
import random
import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class ShuffleBot:
    def __init__(self):
        self.url = "https://fifa-api.tesseractparadox.com/odin/predictions"
        self.driver = webdriver.Firefox()
        self.match_name = None
        self.prediction_line = None
        self.prediction_odds = None
        self.what = None
        self.results = {}

    def load_api_data(self):
        while True:
            try:
                response = requests.get(self.url)
                matches = response.json()
                if matches:
                    parsed_matches = []
                    for match in matches:
                        parsed_matches.append({
                            "name": match['name'],
                            "line": match['prediction']['line'],
                            "odd" : match['prediction']['odd'],
                            "what": match['prediction']['what']
                        })
                    return parsed_matches
            except Exception as e:
                print(f"Chyba při načítání API: {e}")
            time.sleep(10)

    def login_and_wait(self):
        self.driver.get("https://shuffle.com/sports/efootball/efootball-international")
        time.sleep(random.randint(3, 14))
        try:
            WebDriverWait(self.driver, 300).until(
                EC.presence_of_element_located((By.XPATH, "//span[text()='Wallet']"))
            )
            print("Přihlášení rozpoznáno. Pokračuji...")
        except Exception as e:
            print("Nepodařilo se přihlásit:", e)
            self.close()
            raise SystemExit

    def collect_valhalla_matches(self):
        self.driver.get("https://shuffle.com/sports/efootball/efootball-international")
        WebDriverWait(self.driver, 100).until(
            EC.presence_of_element_located((By.XPATH, '//a[contains(., "Valhalla")]'))
        )
        time.sleep(random.randint(3, 14))

        elements = self.driver.find_elements(By.XPATH, '//a[contains(., "Valhalla") or contains(., "Valkyrie")]')
        valhalla_links = [(el.text, el.get_attribute('href')) for el in elements]

        for text, href in valhalla_links:
            self.driver.get(href)
            time.sleep(random.randint(3, 14))
            try:
                WebDriverWait(self.driver, 100).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "MatchEventInfoSection_competitorName__M_3IT"))
                )
                spans = self.driver.find_elements(By.CLASS_NAME, "MatchEventInfoSection_competitorName__M_3IT")
                for span in spans:
                    try:
                        parent = span.find_element(By.XPATH, './ancestor::a')
                        match_href = parent.get_attribute('href')
                        team_text = span.text.strip()

                        if match_href in self.results:
                            self.results[match_href] += " vs " + team_text
                        else:
                            self.results[match_href] = team_text
                    except Exception as e:
                        print(f"Chyba při zpracování span: {e}")
            except Exception as e:
                print(f"Chyba při načítání zápasu: {e}")

    def find_and_bet(self, bet_money):
        for href, text in self.results.items():
            team_1, team_2 = text.split(' vs ')
            swapped_string = f"{team_2} vs {team_1}"
            if (text == self.match_name) or (swapped_string == self.match_name):
                self.driver.get(href)
                time.sleep(random.randint(3, 14))

                # počkáme, než zmizí případný overlay (mobilní menu nebo překryv)
                try:
                    WebDriverWait(self.driver, 5).until(
                        EC.invisibility_of_element_located(
                            (By.CLASS_NAME, "MobileNavItemContent_mobileNavItemWrapper__4i55y")
                        )
                    )
                except:
                    pass  # když overlay není přítomen, ignoruj chybu

                # výběr správné třídy dle predikce (over/under)
                over_under_class_name = "LadderMarketLayout_teamA__qsCMN" if self.what == 'over' else "LadderMarketLayout_teamB__dH6dD"

                try:
                    container = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, over_under_class_name))
                    )

                    elements = container.find_elements(By.CLASS_NAME, "SportsBetSelectionButton_eventText__FJ6GL")
                    for element in elements:
                        if element.text == str(self.prediction_line):
                            try:
                                xpath = (
                                    f"//div[contains(@class, '{over_under_class_name}')"
                                    f" and .//p[text()='{self.prediction_line}']"
                                    f" and .//p[contains(@class, 'oddsAndStatus')]//span/span[text()='{self.prediction_odds}']]"
                                )
                                button = WebDriverWait(self.driver, 10).until(
                                    EC.element_to_be_clickable(
                                        (By.XPATH, f"//div[contains(@class, '{over_under_class_name}')]//p[text()='{self.prediction_line}']")
                                    )
                                )

                                # scrollni na tlačítko, aby nebylo mimo viewport nebo zakryté
                                self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                                time.sleep(0.5)  # krátká pauza po scrollu

                                try:
                                    button.click()
                                except Exception:
                                    # fallback: klikni přes JS
                                    self.driver.execute_script("arguments[0].click();", button)

                                print(f"Clicked button for value: {self.prediction_line}")
                                break
                            except Exception as e:
                                print(f"Error while trying to click button: {e}")
                                continue
                except Exception as e:
                    print(f"Container nebo tlačítko nenalezeno: {e}")
                    continue

                time.sleep(random.randint(2, 5))

                # zadej částku do inputu
                try:
                    input_elem = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, '.CurrencyInput_currencyInput__YGw5R input'))
                    )
                    input_elem.clear()
                    try:
                        input_elem.send_keys(str(bet_money))
                    except Exception as e_inner:
                        print(f"[WARN] send_keys selhalo pro hodnotu {bet_money}, zkouším JS metodu... ({e_inner})")
                        self.driver.execute_script("arguments[0].value = arguments[1];", input_elem, str(bet_money))
                except (TimeoutException, NoSuchElementException) as e_outer:
                    print(f"[ERROR] Prvek pro zadání částky nebyl nalezen nebo není interaktivní: {e_outer}")
                    print("[DEBUG] Výstup HTML:")
                    print(self.driver.page_source[:2000])  # oříznuto pro přehlednost
                    continue

                time.sleep(random.randint(2, 5))

                # klikni na tlačítko "Bet"
                try:
                    bet_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') = 'place bets']")))
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", bet_button)
                    time.sleep(random.randint(2, 5))
                    bet_button.click()
                    print("Sázka úspěšně podána.")
                    
                    bet_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') = 'done']")))
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", bet_button)
                    time.sleep(random.randint(2, 5))
                    bet_button.click()
                    
                    
                except Exception as e:
                    print(f"Chyba při klikání na 'Bet': {e}")
                    continue
                    
                self.driver.get("https://shuffle.com/sports/efootball/efootball-international")

    def close(self):
        if self.driver:
            self.driver.quit()

    def run(self):
        try:
            self.login_and_wait()
            last_matches = set()

            while True:
                now = datetime.datetime.now().time()
                # Run only between 08:00 and 22:00
                if datetime.time(8, 0) <= now <= datetime.time(22, 0):
                    try:
                        matches = self.load_api_data()
                        new_matches = [m for m in matches if m["name"] not in last_matches]

                        if new_matches:
                            self.results = {}
                            self.collect_valhalla_matches()
                            for match in new_matches:
                                self.match_name = match["name"]
                                self.prediction_line = match["line"]
                                self.prediction_odds = match['odd']
                                self.what = match["what"]
                                # Adjust bet amount here
                                self.find_and_bet(bet_money=0.0001)
                                last_matches.add(self.match_name)
                    except Exception as e:
                        print(f"Nastala chyba během cyklu: {e}")
                    # Wait 10 seconds between checks
                    time.sleep(10)
                else:
                    # Outside allowed hours: sleep until next check (1 minute)
                    print("Mimo provozních hodin (08:00-22:00). Čekám...")
                    break
        finally:
            self.close()


# Spuštění
if __name__ == "__main__":
    bot = ShuffleBot()
    bot.run()
