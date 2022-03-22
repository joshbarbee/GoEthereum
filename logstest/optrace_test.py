from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from pymongo import MongoClient
from parsers import parse_geth_optrace, parse_etherscan_optrace
from consts import OPTRACEURL, OPTRACEXPATH, APIURL
import requests
import os
from funcs import compare_logs

APIKEY = os.getenv("APIKEY", "No .env with api key found")

def test_optraces(db, n_tests):
    driver = webdriver.Firefox(service_log_path=os.devnull)
    driver.minimize_window()

    print("Testing optraces")

    # get n random documents
    res = db.traces_test.aggregate([{"$sample": {"size": n_tests}}])

    for trace in res:
        test_ops(driver, trace)

def test_ops(driver, trace):
    driver.get(OPTRACEURL + trace['tx'])
            
    try:
        elem = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, OPTRACEXPATH)))

        ops_geth = parse_geth_optrace(trace['optrace'])
        ops_etherscan = parse_etherscan_optrace(elem[0].text)
        
        if compare_logs(ops_geth, ops_etherscan):
            print("Error with transaction: ", trace['tx'])
        else:
            print("No errors found in log", trace['tx'])
        
    except Exception as e:
        print("Failed to load transaction ", trace['tx'], e)
        return -1
    
    return 0

def test_txinblock(db, n_tests):
    driver = webdriver.Firefox(service_log_path=os.devnull)
    driver.minimize_window()

    res = db.traces_test.aggregate([{"$sample": {"size": n_tests}}])

    for trace in res:    
        res = requests.get(APIURL + APIKEY + "&module=proxy&action=eth_getBlockByNumber&boolean=true&tag=" + hex(int(trace['block'])))
        txs = res.json()['result']['transactions']

        if len(txs) == 0:
            continue

        db_traces = db.traces_test.find({"block":trace['block']})
        
        for tx in db_traces:
            if tx in txs:
                test_ops(db, driver, tx)

                