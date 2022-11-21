# make geth
(cd ./go-ethereum && make)

# ENSURE MONGODB IS RUNNING ON CLIENT - AND MONGODB OPTIONS SET CORRECTLY IN GETH
# (default settings are the same as the default mongodb settings)

# start consensus client 
sudo ./consensus/prysm.sh beacon-chain --execution-endpoint=/home/josh/GoEthereum/data/geth.ipc --accept-terms-of-use --checkpoint-sync-url https://beaconstate.info &

# start rpc server with config
sudo ./go-ethereum/build/bin/geth --syncmode full --datadir data --http --http.api eth,net,engine,admin 