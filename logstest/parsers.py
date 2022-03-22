from funcs import isERC20, isERC721
import json


def parse_geth_optrace(logs):
    res = []

    for i in logs.split("\n")[1:]:
        log = i.split(",")
        
        if len(log) > 1:
            if log[2] == "KECCAK256":
                log[2] = "SHA3"

            log_dict = {
                "pc": log[0],
                "depth": log[1],
                "opcode": log[2], 
                "gas": log[3],
                "cost": log[4]
            }

            res.append(log_dict)
    
    return res

def parse_etherscan_optrace(logs):
    res = []

    for i in logs.split("\n")[1:]:
        log = i.split(" ")[1:]

        if len(log) > 1:
            log_dict = {
                "pc": log[0],
                "depth": log[4],
                "opcode": log[1], 
                "gas": log[2],
                "cost": log[3],
            }

            res.append(log_dict)
    
    return res

def parse_geth_functrace(logs):
    res = []

    for i in logs.split("\n")[1:]:
        log = i.split(",")
        
        if len(log) > 1:
            log_dict = {
                "calltype": log[0].lower(),
                "depth": log[1],
                "from": log[2].lower(), 
                "to": log[3].lower(),
                "value": log[4],
                "gas": hex(int(log[5])),
                "input": "0x0000000000000000000000000000000000000000000000000000000000000000" if log[6] == "0x0000000000000000000000000000000000000000000000000000000000000000" else log[6].lower(),
                "output": log[7].lower()
            }

            res.append(log_dict)
    
    return res

def parse_etherscan_functrace(logs):
    res = []

    logs = json.loads(logs)

    for log in logs:
        if log['type'] == 'create':
            op = log['result']['address']

        elif 'result' not in log or 'output' not in log['result']:
            op = "0x"
        else:
            op = log['result']['output']

        # we distinguish between create2 and create in our logs. Etherscan does not
        ct = log['action']['callType'] if log['type'] != 'create' else log['type']

        # etherscan has no representation for null addr
        to = log['action']['to'] if 'to' in log['action'] else "0x0"

        # the input key is replaced with init on contract creation
        ip = log['action']['input'] if 'input' in log['action'] else log['action']['init']
       
        log_dict = {
            "calltype": ct,
            "depth": str(len(log['traceAddress'])),
            "from": log['action']['from'].lower(),
            'to': to.lower(),
            'value': log['action']['value'].lower(),
            'gas': log['action']['gas'],
            "input": ip.lower(),
            "output": op.lower()
        }

        res.append(log_dict)

    return res

def parse_geth_eventtrace(logs):
    res = []

    for i in logs.split("\n")[1:]:
        entries = i.split(",")
        
        # topics are space deliminated
        topics = (entries[1].replace("[", "").replace("]","")).split(" ")

        log_dict = {
            "address": entries[0].lower(),
            "topics": topics,
            "data": entries[2],
        }

        res.append(log_dict)
    
    return res

def parse_etherscan_eventtrace(logs):
    res = []

    for i in logs:
        log_dict = {
            "address": i["address"].lower(),
            "topics": i["topics"],
            "data": i["data"] if i["data"] != "" else "0x",
        }

        res.append(log_dict)
    
    return res