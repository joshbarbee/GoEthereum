from mgofetch import MongoFetcher
from dasm import BlockParser, TxParser
from edges import build_blocks

fetcher = MongoFetcher()

res = fetcher.get_tx("0xc5b8151a3e5e8374f0c980764e0e3825cddf59492d6440ce3d6cf04061399464")

tx = TxParser()
tx.parse(res)
r = build_blocks(tx)

def dfs(node):
    if node == None:
        return
    
    print(node)

    if node.succ != None:
        dfs(node.succ)
        
if __name__ == "__main__":
    dfs(r)


