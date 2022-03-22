TRANSFERSIG = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
APPROVESIG = "0x6e11fb1b7f119e3f2fa29896ef5fdf8b8a2d0d4df6fe90ba8668e7d8b2ffa25e"
APPROVEFORALLSIG = "0xaaf27816598688732a80b26fb3b6d0bc241c08f38a6d8ca2a0723f4835d593d6"

@staticmethod
def compare_logs(log1, log2):
    for i in range(min(len(log1), len(log2))):
        if 'calltype' in log1[i] and log1[i]['calltype'] == 'create':
            log1[i]['output'] = log2[i]['output']

        if log1[i] != log2[i]:
            print("Invalid match: \n", log1[i], log2[i])
            return 1
    return 0

@staticmethod
def isERC20(topics, data):
    if len(data) != 3:
        return False
    
    if topics[0] != TRANSFERSIG and topics[0] != APPROVESIG:
        return False
    
    return True

@staticmethod
def isERC721(topics, data):
    if len(data) != 4:
        return False
    
    if topics[0] != TRANSFERSIG and topics[0] != APPROVESIG and topics[0] != APPROVEFORALLSIG:
        return False
    
    return True