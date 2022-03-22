# make geth
(cd ./go-ethereum && make)

# start rpc server with config
./go-ethereum/build/bin/geth --syncmode="full" --datadir="../../data" --maxpeers=500, --http