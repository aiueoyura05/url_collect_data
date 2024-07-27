import csv
import time
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.common.exceptions import NoSuchElementException

#skip rows
skip_n = 0

# Define CSV file path
csv_result_path = "output_edge0701.csv"

# Define CSV column headers
fieldnames = ["id", "url", "status", "edge", "error", "redirections"]

# CSVファイルのパス
csv_file_path = r''
user_data_dir = r'Edge\User Data\Default'

def init_driver():
    # Edgeのオプション設定
    options = Options()

    options.add_argument(f"user-data-dir={user_data_dir}")
    options.add_argument('--profile-directory=Default')

    # ヘッドレスモードを有効にする場合
    # options.add_argument('--headless')


    return webdriver.Edge(options=options)


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

        #limit the number of redirects to 100 or less.
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
                error_row = {"id": row["id"], "url": "error", "status": row["status"], "edge": row["edge"], "error": row["error"], "redirections": row["redirections"]}
                writer.writerow(error_row)

def main():
    global driver

    #Execution count
    exe_count = 0

    # Write header to CSV file
    with open(csv_result_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write header
        writer.writeheader()

    # CSVファイルを開く
    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)

        #skip the first n +1 rows.
        for _ in range(skip_n+1):
            next(reader)

        for row in reader:
            url = row[1]  # URLを読み込む
            exe_count += 1
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
                print(f"エラーが発生しました: {e.msg}")
                error_flg = True
                pass

            try:
                # タブを閉じて、最初のタブに戻る
                driver.close()  # 現在のタブを閉じる
                driver.switch_to.window(driver.window_handles[0])  # 最初のタブに戻る
            except Exception as e:
                print(f"URL: {url}, タブを閉じる際にエラーが発生しました: {e.msg}")
                #Reopen the driver in case of error occuring.
                driver.quit()
                driver = init_driver()
            finally:
                result = {"id": exe_count, "url": row[1], "status": row[2], "edge": safe_search,  "error": error_flg, "redirections": redirections}
                write_to_csv([result])
                print(result)

    # 全てのURLの処理が終わったら、ブラウザを閉じる
    driver.quit()


if __name__ == '__main__':
    # WebDriverの初期化
    driver = init_driver()
    #timeout setting
    driver.set_page_load_timeout(5)
    driver.set_script_timeout(2)
    driver.implicitly_wait(5)

    main()
