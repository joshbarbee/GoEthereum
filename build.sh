#!/bin/sh

# this will build the geth and consensus client, and then start syncing, logging collected data
# to mongodb

# make geth
(cd ./go-ethereum && make)

# ENSURE MONGODB IS RUNNING ON CLIENT - AND MONGODB OPTIONS SET CORRECTLY IN GETH
# default settings are the same as the default mongodb settings
# but can configure via mongo.url, mongo.collection, ... options on Geth

# start consensus client 
sudo ./consensus/prysm.sh beacon-chain --execution-endpoint=/home/josh/Research/GoEthereum/data/geth.ipc --accept-terms-of-use --checkpoint-sync-url https://beaconstate.info --datadir data &

# start rpc server with config
sudo ./go-ethereum/build/bin/geth --syncmode archive --datadir data --http --http.api eth,net,engine,admin --mongo.database ethlogger2
