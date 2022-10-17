Modified Go-Ethereum Docs + Specifications

*Go-Ethereum requires us to run a beacon node via a consensur client alongside the Go-Ethereum node, as a result of the hardfork. We use prysm for our consensus client (with no modifications).

INSTALLATION & RUNNING:
PREREQ: Make sure MongoDB is installed on the system. If not, install here: https://www.mongodb.com/docs/manual/installation/
1. Clone the repo from https://github.com/joshbarbee/GoEthereum.git
2. Navigate to the ‘go-ethereum folder’: ```cd go-ethereum```
3. Build go-ethereum on your own machine: ```make geth```
4. Navigate to the ‘’consensus folder’
5. Install and run Prysm
   ```./prysm.sh beacon-chain -execution-endpoint /research/analysis/go-ethereum/data/geth.ipc --checkpoint-sync-url=https://beaconstate.ethstaker.cc```
   - The -execution-endpoint parameter specifies the location of the IPC server we are using to communicate between Geth and Prysm
   - The --checkpoint-sync-url is used to utilize a known 3rd party synced beacon node to speed up beacon syncing.
6. Run go-ethereum via the following command:
   ```sudo ./build/bin/geth --syncmode full --cache 2048 --datadir ./data --mongo.collection ethereum --mongo.database ethlogger --mongo.uri mongo://127.0.0.1:27017```
   - We use syncmode full, since we need to execute the opcodes of each transaction (but do not need to permanently store them via archive)
   - -cache can be whatever, but default is 4096mb
   - --datadir specifies the directory to write chaindata to. This needs to be constant whenever we run this node, otherwise we will start syncing from 0th block
   - mongo.uri specifies the URI of the MongoDB instance that we want to write logged data to
   - mongo.database is the specific database in MongoDB that we want to save data to
   - mongo.collection is the specific collection in MongoDB that we log data to
7. The beacon node and Geth should now be running. Once Geth begins full-syncing, check the results of the collected data in MongoDB. 
