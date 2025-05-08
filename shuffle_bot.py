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
            if not self.is_matching_match(text):
                continue

            self.driver.get(href)
            time.sleep(random.randint(3, 14))
            self.wait_for_overlay_to_disappear()

            try:
                if self.select_prediction_button():
                    self.enter_bet_amount(bet_money)
                    self.confirm_bet()
            except Exception as e:
                print(f"[ERROR] Chyba během procesu sázení: {e}")
                continue

            self.driver.get("https://shuffle.com/sports/efootball/efootball-international")


    def is_matching_match(self, match_text):
        team_1, team_2 = match_text.split(' vs ')
        swapped_string = f"{team_2} vs {team_1}"
        return match_text == self.match_name or swapped_string == self.match_name

    def wait_for_overlay_to_disappear(self):
        try:
            WebDriverWait(self.driver, 5).until(
                EC.invisibility_of_element_located(
                    (By.CLASS_NAME, "MobileNavItemContent_mobileNavItemWrapper__4i55y")
                )
            )
        except:
            pass

    def select_prediction_button(self):
        class_name = "LadderMarketLayout_teamA__qsCMN" if self.what == 'over' else "LadderMarketLayout_teamB__dH6dD"

        try:
            container = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, class_name))
            )
            elements = container.find_elements(By.CLASS_NAME, "SportsBetSelectionButton_eventText__FJ6GL")

            for element in elements:
                if element.text == str(self.prediction_line):
                    return self.click_prediction_button(class_name)
        except Exception as e:
            print(f"[ERROR] Není možné najít container nebo tlačítko: {e}")
        return False

    def click_prediction_button(self, class_name):
        try:
            button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, f"//div[contains(@class, '{class_name}')]//p[text()='{self.prediction_line}']")
                )
            )
            self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
            time.sleep(0.5)

            try:
                button.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", button)

            print(f"Clicked button for value: {self.prediction_line}")
            return True
        except Exception as e:
            print(f"[ERROR] Nepodařilo se kliknout na predikci: {e}")
            return False

    def enter_bet_amount(self, amount):
        try:
            # Pokusíme se najít input pro zadání částky
            input_elem = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.CurrencyInput_currencyInput__YGw5R input'))
            )
            input_elem.clear()

            try:
                input_elem.send_keys(str(amount))
            except Exception as e_inner:
                print(f"[WARN] send_keys selhalo, zkouším JS... ({e_inner})")
                self.driver.execute_script("arguments[0].value = arguments[1];", input_elem, str(amount))

        except (TimeoutException, NoSuchElementException) as e_outer:
            print(f"[ERROR] Nelze zadat částku: {e_outer}")
            print("[DEBUG] HTML výstup:")
            print(self.driver.page_source[:2000])

            # Přidání funkce pro kliknutí na clear bet a návrat na stránku
            self.clear_bet_and_return()  # Zavoláme funkci pro kliknutí na clear bet
            raise

    def clear_bet_and_return(self):
        try:
            # Klikni na tlačítko pro smazání sázky (clear bet)
            clear_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') = 'clear bet']"))
            )
            self.driver.execute_script("arguments[0].scrollIntoView(true);", clear_button)
            time.sleep(random.randint(2, 5))
            clear_button.click()

            print("Sázka byla vymazána (clear bet).")

            # Čekáme na potvrzení vymazání nebo na jakýkoliv jiný signál, že sázka byla odstraněna
            time.sleep(random.randint(3, 7))  # Počkej chvíli pro jistotu

            # Návrat na stránku "efootball-international"
            self.driver.get("https://shuffle.com/sports/efootball/efootball-international")
            print("Vrátili jsme se zpět na stránku efootball-international.")

        except Exception as e:
            print(f"[ERROR] Chyba při vymazávání sázky nebo návratu na stránku: {e}")

    def confirm_bet(self):
        try:
            bet_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') = 'place bets']")))
            self.driver.execute_script("arguments[0].scrollIntoView(true);", bet_button)
            time.sleep(random.randint(2, 5))
            bet_button.click()

            done_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') = 'done']")))
            self.driver.execute_script("arguments[0].scrollIntoView(true);", done_button)
            time.sleep(random.randint(2, 5))
            done_button.click()

            print("Sázka úspěšně podána.")
        except Exception as e:
            print(f"[ERROR] Chyba při potvrzení sázky: {e}")
            raise


    def close(self):
        if self.driver:
            self.driver.quit()

    def run(self):
        try:
            self.login_and_wait()
            last_matches = set()

            while True:
                now = datetime.datetime.now().time()
                # Provozní doba mezi 8:00 a 23:00
                if datetime.time(8, 0) <= now <= datetime.time(23, 0):
                    try:
                        matches = self.load_api_data()
                        new_matches = [m for m in matches if m["name"] not in last_matches]

                        if new_matches:
                            self.results = {}
                            self.collect_valhalla_matches()

                            for match in new_matches:
                                try:
                                    self.match_name = match["name"]
                                    self.prediction_line = match["line"]
                                    self.prediction_odds = match["odd"]
                                    self.what = match["what"]

                                    print(f"[INFO] Nový zápas: {self.match_name}, predikce: {self.what} {self.prediction_line} @ {self.prediction_odds}")
                                    self.find_and_bet(bet_money=0.0001)
                                    last_matches.add(self.match_name)

                                except Exception as match_error:
                                    print(f"[ERROR] Chyba při zpracování zápasu '{match['name']}': {match_error}")
                    except Exception as loop_error:
                        print(f"[ERROR] Chyba během načítání nebo zpracování zápasů: {loop_error}")

                    time.sleep(10)
                else:
                    print("Mimo provozních hodin (08:00–23:00). Čekám...")
                    break
        finally:
            self.close()


# Spuštění
if __name__ == "__main__":
    bot = ShuffleBot()
    bot.run()
