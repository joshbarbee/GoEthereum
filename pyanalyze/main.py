from mgofetch import MongoFetcher
from dasm import BlockParser, TxParser
from edges import build_edges

fetcher = MongoFetcher()

res = fetcher.get_tx("0xc1022a196228afccbe33c0b5895c819140e5701bd694877c3144c0ec592013c2")

tx = TxParser()
tx.parse(res)
r = build_edges(tx)

while (r != None):
    print(r)
    r = r.succ

