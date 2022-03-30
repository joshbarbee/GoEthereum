from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from pymongo import MongoClient
from parsers import parse_geth_functrace, parse_etherscan_functrace
from consts import CALLTRACE, CALLTRACEXPATH
from funcs import compare_logs
import os

def test_functraces(db, n_traces):
    driver = webdriver.Firefox(service_log_path=os.devnull)
    driver.minimize_window()
    
    print("Testing Function traces")

    # get n random documents
    res = db.traces.aggregate([{"$sample": {"size": n_traces}}])
    res = db.traces.find({"tx":"0xc5b8151a3e5e8374f0c980764e0e3825cddf59492d6440ce3d6cf04061399464"})

    for trace in res:
        driver.get(CALLTRACE(trace['tx']))

        try:
            WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, CALLTRACEXPATH)))
            driver.execute_script("document.getElementById('editor').setAttribute('value', '['+(editor.getValue().trim())+']')")
            etherscan = driver.find_element(By.ID, "editor").get_attribute("value")

            func_geth = parse_geth_functrace(trace['functrace'])
  
            func_etherscan = parse_etherscan_functrace(etherscan)

            if compare_logs(func_geth, func_etherscan):
                print("Error with transaction: ", trace['tx'])
            else:
                print("No errors found in log", trace['tx'])
        except Exception as e:
            print("Failed to load transaction ", trace['tx'], e)
            return -1
                    # we have to do this due to selenium being bad with the console
        driver.close()
        driver = webdriver.Firefox()
        driver.minimize_window()
    driver.close()
    return 0