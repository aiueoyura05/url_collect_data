import csv
import datetime
import sqlite3
import time
import fcntl
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

# Configuration
CSV_RESULT_PATH_TEMPLATE = "output_chrome_{timestamp}.csv"
USER_DATA_DIR = r'C:\Users\[ユーザ名]\AppData\Local\Google\Chrome\User Data'
DB_PATH = 'phishtank0727.db'
LOCK_FILE_PATH = 'C:\\temp\\selenium_test_with_db.lock'  # 適切なパスに変更してください
FETCH_INTERVAL = 3600  # 1 hour in seconds

# CSV column headers
FIELDNAMES = ["id", "url", "status", "chrome", "error", "redirections"]

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

def init_driver():
    options = Options()
    options.add_argument(f"user-data-dir={USER_DATA_DIR}")
    options.add_argument('--profile-directory=Default')
    options.add_argument('--disk-cache-size=0')
    # Uncomment the following line to enable headless mode
    # options.add_argument('--headless')
    return webdriver.Chrome(options=options)

def check_safe_search(driver, n=0, flag=False):
    try:
        details_button = driver.find_element(By.ID, "details-button")
        details_button.click()
        proceed_link = driver.find_element(By.ID, "proceed-link")
        proceed_link.click()
        flag = True
        if n > 50:
            return flag, n, True
        return check_safe_search(driver, n + 1, flag)
    except NoSuchElementException:
        return flag, n, False
    except Exception as e:
        logger.error(f"An error occurred while checking safe search: {e}")
        return flag, n, True

def write_to_csv(file_path, data):
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in data:
            try:
                writer.writerow(row)
            except Exception as e:
                logger.error(f"Error writing to CSV: {row} - {e}")
                error_row = {key: (row[key] if key in row else '') for key in FIELDNAMES}
                writer.writerow(error_row)

def get_urls_from_db(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT phish_id, url, verified, timestamp FROM phish_data ORDER BY timestamp')
    rows = c.fetchall()
    conn.close()
    return rows

def process_urls(driver, urls):
    results = []
    for row in urls:
        phish_id, url, status, timestamp = row
        error_flg = False
        safe_search = False
        redirections = 0

        logger.info(f"Processing {phish_id}, {url}, {datetime.datetime.now()}")
        try:
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[-1])
            driver.get(url)
            safe_search, redirections, error_flg = check_safe_search(driver)
        except Exception as e:
            logger.error(f"An error occurred while processing URL {url}: {e}")
            error_flg = True
        finally:
            try:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            except Exception as e:
                logger.error(f"Error closing tab for URL {url}: {e}")
                driver.quit()
                driver = init_driver()

            result = {"id": phish_id, "url": url, "status": status, "chrome": safe_search, "error": error_flg, "redirections": redirections}
            results.append(result)
            logger.info(result)

    return results

def acquire_lock(file_path):
    """Acquire file lock to prevent concurrent execution."""
    file = open(file_path, 'w')
    try:
        fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return file
    except IOError:
        return None

def main():
    lock_file = acquire_lock(LOCK_FILE_PATH)
    if lock_file is None:
        logger.warning("Another instance is running. Exiting.")
        exit(1)

    driver = init_driver()
    driver.set_page_load_timeout(5)
    driver.set_script_timeout(2)
    driver.implicitly_wait(5)

    try:
        while True:
            try:
                urls = get_urls_from_db(DB_PATH)
                if urls:
                    latest_timestamp = urls[-1][-1].replace(":", "").replace(" ", "_")
                    csv_result_path = CSV_RESULT_PATH_TEMPLATE.format(timestamp=latest_timestamp)
                    results = process_urls(driver, urls)
                    write_to_csv(csv_result_path, results)
            except Exception as e:
                logger.error(f"An error occurred during processing: {e}")

            time.sleep(FETCH_INTERVAL)
    finally:
        fcntl.flock(lock_file, fcntl.LOCK_UN)
        lock_file.close()
        driver.quit()
        logger.info("Resources have been released and script is exiting.")

if __name__ == '__main__':
    main()
