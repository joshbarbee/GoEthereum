APIURL = "https://api.etherscan.io/api?"

MONGOURI = "mongodb://127.0.0.1"

# etherscan base url for optraces
OPTRACEURL = "https://etherscan.io/vmtrace?txhash="
OPTRACEXPATH = "/html/body/div[1]/main/div[3]/form/div[3]/div[2]/div/div/div/table"

CALLTRACE = lambda x: "https://etherscan.io/vmtrace?type=parity&txhash=" + x + "#raw"
CALLTRACEXPATH = "/html/body/div[1]/main/div[2]/form/div[3]/div[2]"
