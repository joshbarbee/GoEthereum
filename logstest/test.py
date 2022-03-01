from cmath import log
from random import randint
from trace import Trace
from flask import request
from pymongo import MongoClient
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
from parsers import parse_etherscan_optrace, parse_geth_optrace

# mongodb uri
MONGOURI = "mongodb://127.0.0.1"

# etherscan base url for optraces
OPTRACEURL = "https://etherscan.io/vmtrace?txhash="

# etherscan api url
APIURL = "https://api.etherscan.io/api"

# etherscan api key
APIKEY = ""

# the xpath to the talbe on etherscan
XPATH = "/html/body/div[1]/main/div[3]/form/div[3]/div[2]/div/div/div/table"

client = MongoClient(MONGOURI)
db = client.ethereum

def test_optraces(n_tests):
    driver = webdriver.Firefox()
    driver.maximize_window()

    # get n random documents
    res = db.traces.aggregate([{"$sample": {"size": n_tests}}])

    for trace in res:
        driver.get(OPTRACEURL + trace['tx'])
        
        try:
            elem = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, XPATH)))

            ops_geth = parse_geth_optrace(trace['optrace'])
            ops_etherscan = parse_etherscan_optrace(elem[0].text)
            
            if compare_logs(ops_geth, ops_etherscan):
                print("Error with transaction: ", trace['tx'])
            
        except Exception as e:
            print("Failed to load transaction ", trace['tx'], e)

def compare_logs(log1, log2):
    log2idx = 0
    for i in range(min(len(log1), len(log2))):
        if log1[i] != log2[log2idx]:
            log2idx += 1
            if log1[i] != log2[log2idx]:
                print("Invalid match: ", log1[i], log2[i])
                return 1
        log2idx += 1
    
    print("No errors found in log")
    return 0

def test_txinblock(n_tests, begin, end):
    for i in range(n_tests):
        # pick randint in block range
        blocknumber = randint(begin, end)

        # get all tx in a block
        traces = db.traces.find({"block": blocknumber})
        print(blocknumber)
        
        for trace in traces:
            print(trace)
            url = APIURL + "?module=proxy&action=eth_getCode&tag=latest&apikey=" + APIKEY + "&address=" + trace['to']

            res = request.get(url)

            print(res.text)

if __name__ == "__main__":
    test_optraces(20)