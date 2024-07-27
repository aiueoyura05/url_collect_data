import csv
import datetime
import sqlite3
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

# Define file paths and database path
csv_result_path = "output_chrome0701.csv"
db_path = 'phishtank0727.db'
user_data_dir = r'C:\Users\[ユーザ名]\AppData\Local\Google\Chrome\User Data'
fieldnames = ["id", "url", "status", "chrome", "error", "redirections", "japanese"]

# Fetch interval for database in seconds
fetch_interval = 3600

def init_driver():
    options = Options()
    options.add_argument(f"user-data-dir={user_data_dir}")
    options.add_argument('--profile-directory=Default')
    options.add_argument('--disk-cache-size=0')
    # Uncomment the following line to enable headless mode
    # options.add_argument('--headless')
    return webdriver.Chrome(options=options)

def check_safe_search(n, flag):
    global driver
    try:
        error = False
        details_button = driver.find_element(By.ID, "details-button")
        details_button.click()
        proceed_link = driver.find_element(By.ID, "proceed-link")
        proceed_link.click()
        flag = True

        if n > 50:
            error = True
            return flag, n, error

        return check_safe_search(n + 1, flag)
    except NoSuchElementException:
        error = False
        return flag, n, error
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        error = True
        return flag, n, error

def write_to_csv(data):
    with open(csv_result_path, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        for row in data:
            try:
                writer.writerow(row)
            except:
                print(f"Error at writing csv: {row}")
                error_row = {"id": row["id"], "url": "error", "status": row["status"], "chrome": row["chrome"], "error": row["error"], "redirections": row["redirections"]}
                writer.writerow(error_row)

def fetch_urls_from_db():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT id, url, status FROM phish_data")
    rows = c.fetchall()
    conn.close()
    return rows

def main():
    global driver

    exe_count = 0
    with open(csv_result_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

    while True:
        urls = fetch_urls_from_db()
        for row in urls:
            exe_count += 1
            url = row[1]
            status = row[2]
            error_flg = False
            safe_search = False
            redirections = 0

            print(f"{exe_count}, {url}, {datetime.datetime.now()}")
            try:
                driver.execute_script("window.open('');")
                driver.switch_to.window(driver.window_handles[-1])
                driver.get(url)
                safe_search, redirections, error_flg = check_safe_search(0, safe_search)
            except Exception as e:
                print(f"エラーが発生しました: {e}")
                error_flg = True

            try:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            except Exception as e:
                print(f"URL: {url}, タブを閉じる際にエラーが発生しました: {e}")
                driver.quit()
                driver = init_driver()
            finally:
                result = {"id": exe_count, "url": url, "status": status, "chrome": safe_search, "error": error_flg, "redirections": redirections}
                write_to_csv([result])
                print(result)

        time.sleep(fetch_interval)

if __name__ == '__main__':
    driver = init_driver()
    driver.set_page_load_timeout(5)
    driver.set_script_timeout(2)
    driver.implicitly_wait(5)
    main()
