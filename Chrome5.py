import csv
import time
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager  # 自動でChromeDriverを管理

# Define file paths
csv_input_path = "input_urls.csv"
csv_result_path = "output_chrome0701.csv"
user_data_dir = r'Chrome\User Data\Default'
fieldnames = ["id", "url", "chrome", "error", "redirections"]

# Fetch interval in seconds
fetch_interval = 3600

def init_driver():
    # Chromeのオプション設定
    options = Options()
    options.add_argument(f"user-data-dir={user_data_dir}")
    options.add_argument('--profile-directory=Default')
    # ヘッドレスモードを有効にする場合
    # options.add_argument('--headless')
    # Serviceを使用してWebDriverを初期化
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def check_safe_search(n, flag):
    global driver
    try:
        error = False
        # Click the "details-button"
        more_info_button = driver.find_element(By.ID, "moreInformationDropdownLink")
        more_info_button.click()
        # Click the "proceed-link"
        proceed_link = driver.find_element(By.ID, "overrideLink")
        proceed_link.click()
        flag = True
        # Limit the number of redirects to 100 or less.
        if n > 100:
            error = True
            return flag, n, error
        return check_safe_search(n+1, flag)
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
        # Write data rows
        for row in data:
            try:
                writer.writerow(row)
            except:
                print(f"Error at writing csv: {row}")
                error_row = {"id": row["id"], "url": "error", "chrome": row["chrome"], "error": row["error"], "redirections": row["redirections"]}
                writer.writerow(error_row)

def fetch_urls_from_csv():
    urls = []
    with open(csv_input_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            urls.append((row['id'], row['url']))
    return urls

def main():
    global driver
    exe_count = 0
    with open(csv_result_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
    while True:
        urls = fetch_urls_from_csv()
        for row in urls:
            exe_count += 1
            url = row[1]
            error_flg = False
            safe_search = False
            redirections = 0
            print(f"{exe_count}, {url}, {datetime.datetime.now()}")
            try:
                # URLを新しいタブで開く
                driver.execute_script("window.open('');")  # 新しいタブを開く
                driver.switch_to.window(driver.window_handles[-1])  # 新しいタブに切り替え
                driver.get(url)  # URLを開く
                # URLを開いた後の処理（必要に応じて）
                safe_search, redirections, error_flg = check_safe_search(0, safe_search)
            except Exception as e:
                print(f"エラーが発生しました: {e}")
                error_flg = True
            try:
                # タブを閉じて、最初のタブに戻る
                driver.close()  # 現在のタブを閉じる
                driver.switch_to.window(driver.window_handles[0])  # 最初のタブに戻る
            except Exception as e:
                print(f"URL: {url}, タブを閉じる際にエラーが発生しました: {e}")
                # Reopen the driver in case of error occurring.
                driver.quit()
                driver = init_driver()
            finally:
                result = {"id": exe_count, "url": url, "chrome": safe_search, "error": error_flg, "redirections": redirections}
                write_to_csv([result])
                print(result)
        time.sleep(fetch_interval)
    # 全てのURLの処理が終わったら、ブラウザを閉じる
    driver.quit()

if __name__ == '__main__':
    # WebDriverの初期化
    driver = init_driver()
    # timeout setting
    driver.set_page_load_timeout(5)
    driver.set_script_timeout(2)
    driver.implicitly_wait(5)
    main()
