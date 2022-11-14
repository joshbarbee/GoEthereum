# make geth
(cd ./go-ethereum && make)

# start consensus client 
sudo ./consensus/prysm.sh beacon-chain --execution-endpoint=~/research/GoEthereum/data/geth.ipc --accept-terms-of-use &

# start rpc server with config
sudo ./go-ethereum/build/bin/geth --syncmode full --datadir data --authrpc.addr localhost --authrpc.port 8551 --authrpc.vhosts localhost --authrpc.jwtsecret data/geth/jwtsecret 