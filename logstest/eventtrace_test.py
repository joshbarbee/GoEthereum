import os
import requests 
from pymongo import MongoClient
from consts import APIURL
from parsers import parse_geth_eventtrace, parse_etherscan_eventtrace
from funcs import compare_logs

APIKEY = os.getenv("APIKEY", "No .env with api key found")

def test_eventtraces(db, n : int):
    print("Testing event traces")

    res = db.traces.aggregate([{"$sample": {"size": n}}])
    for trace in res:
        # get transaction tx logs from etherscan api
        eth_res = requests.get(APIURL + APIKEY + "&module=proxy&action=eth_getTransactionReceipt&txhash=" + trace['tx']).json()

        if ('logs' in eth_res['result']):
            eth = parse_etherscan_eventtrace(eth_res["result"]['logs'])
        else:
            eth = []

        geth = parse_geth_eventtrace(trace['eventtrace'])

        if (compare_logs(eth, geth)):
            print("Error with transaction: ", trace['tx'])
        else:
            print("No errors found in log", trace['tx'])