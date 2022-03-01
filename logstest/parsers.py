
def parse_geth_optrace(logs):
    res = []

    for i in logs.split("\n")[2:]:
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