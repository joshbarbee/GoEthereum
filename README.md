# Modified Go-Ethereum Docs + Specifications

*Go-Ethereum requires us to run a beacon node via a consensur client alongside the Go-Ethereum node, as a result of the hardfork. We use prysm for our consensus client (with no modifications).

Statistics:
Average RAM when running Geth + Consensus + MongoDB (on same computer): 10.2 gb average
Average document size (we only collect non-EOA-EOA transfers): 54 kb

## INSTALLATION & RUNNING:
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

## Modifications to Go-Ethereum:
A note: Each time we directly interact with the mgologger package outside of initializing the connection/trace or closing the connection, we must make sure we are not prefetching the transaction. This is done via checking the boolean evm.Prefetch.
- In core:
  - blockchain.go:
    - We initialize the mongoDB logger in NewBlockchain, on line 254
    - When the blockchain is stopped, we close the connection, in Stop()on line 940
  - evm.go:
    - In the Transfer function, we make a check for a prefetch transaction. If not prefetch, then log the transaction.
    - The Transfer function has additional parameters prefetch and evm.depth.
  - state_processor.go:
    - In applyTransaction:
      - We initialize the mongoDB trace for the specific transaction on line 100, after the EVM is reset
      - We then write the info of the now-executed transaction to the mongoDB database via mgologger.WriteEntry on line 146
  - state_prefetcher.go:
    - In the Prefetch function, we modify the cfg parameter to set the value of Prefetch to be true. This is the only time we explicity set the value of Prefetch. This cfg is then forwarded to the EVM.
  - In vm:
    - instructions.go
      - The return type of each opcode is modified to include an extra argument ([]byte, error) -> ([]byte, []byte,error)
      - For each return statement, we either modify the newly-added second parameter to either nil or a certain value contained within that opcode
      - The opcodes for which we return a certain value are the set of all opcodes that we run analysis on. See the analyzer docs for more details
      - the makeLog function will interact with the mgologger to write event logs. We make a check to evm.Prefetch to determine whether we are running the transaction as a real transaction, not a prefetched one.
      - These changes will also require making changes to the executionFunc parameters. See jump_table.go
    - interpreter.go:
      - The Config type has an additional field, Prefetch, a boolean.
    - evm.go:
      - The NewEVM function sets the struct field Prefetch to the value of config.Prefetch, passed in via the vmConfig.
      - Call / CallCode / DelegateCall / StaticCall / Create
        - Each of these functions have additional logic for logging function traces. 
        - We make a copy of the value and gas before the call is ran
        - Immediately before the call, we interact with the TraceIndex and CallStack of the logger. We increment the TraceIndex and update the CallStack based on the previous value of the TraceIndex.
        - After the call completes, we log the information of the call via mgologger.AddFuncLog.
        - These steps are done in every of the above functions. Some values may not need to be copied if it does not exist (see value for DelegateCall)
    - jump_table.go:
      - The executionFunc type is modified to now return the parameters ([]byte, []byte, error).
    - eips.go:
      - for each of the new opcodes defined in eips.go (all functions that implement executionFunc), redefine the return type of the function.

## LOGGER DATA TYPES:
The logger defines two distinct datatypes in mgologger/DBLogger.go. 
1. The MongoConfig struct consists of information used to generate the MongoDB connection, taking in the URI, database name, and collection name.
2. The Collection struct consists of an individual document in the MongoDB database. This includes any pertinent information about the transaction, such as the from, to, and value, and also the opcode logs, function logs, event logs, and transfer logs.
3. The logger also defines some static variables.
   - opTrace is the trace of the opcodes through transaction execution
   - funcTrace is the trace of the functions through a single transaction
   - eventTrace logs event emission throughout a transaction
   - transferTrace logs native transfers through a transaction

## LOGGER FUNCTIONS:
The logger must first be initialized before it is used, via invoking ```mgologger.InitLogger(cfg MongoConfig)```. This is currently done in ```core/blockchain.go:254```. 
- We first allocate space for the bytes buffer that we are writing the opcode data to. The opcode trace has 8mb allocated for it, the function trace has 2mb allocated, and the event trace and transfer trace has 500kb allocated. These values should be evaluated for future optimization.
- We also set all of our values (CallStack and TraceIndex) we use to track the depth of a transactions' execution to 0.
- Then, we initialize the mongoDB session, using the information stored in the cfg parameter.

For each transaction, we must reinitialize some global values, such as the optrace. This is done by ```mgologger.InitTrace()``` in ```core/state_processor.go:100```
- We reset the optrace, funcTrace, eventTrace, and tranferTrace buffers, setting our write location back to 0, and reinitializing all values of the buffer to 0.
- We reset the CallStack and TraceIndex

We add an opcode log for each opcode. This is done via ```mgologger.AddOpLog(pc uint64, depth uint64, op string, gas uint64, gasCost uint64, ret []byte)```, invoked in ```core/vm/interpreter.go:239```. We invoke this after a single opcode execution, for each opcode. 

Function logs (call/callcode/delegatecall/staticcall/create) are logged in ```mgologger.AddFuncLog(index int, calltype string, depth int, from common.Address, to common.Address, value big.Int, gas uint64, input []byte, output []byte)```. The input parameters are converted into a string and then written to the buffer. 
- Function logs are interacted with in ```core/vm/evm.go```. Each of the Go functons that define an EVM call have logger interactions. 
- We make copies of any mutable values that we want to log before the context of the call is executed. These values are currently the gasLeft of the transaction before the call, and the value param associated with the internal transfer.
- In the case of non-precompiled contracts, we log the results of the function execution. First, we manipulate the call index and call stack from mgologger before calling the .Run() function. This is used to trace the execution order of the calls.
- We then log the return data after .Run() concludes, if the transaction is not a prefetch tx. Due to how we log the calls, the calls are written in the order that they finish evaluating, rather than they start evaluating. See example below for more info

```mgoLogger.AddEventLog(addr common.Address, topics []common.Hash, data []byte)``` writes any emitted event by a transaction to the logged data. 
- This is invoked in ```core/vm/instructions.go```, within the ```makeLog``` function. 
- The address that emitted the event, the topics of the event, and data of the event are logged, as well as an index to track what specific call emitted the event.

```mgoLogger.WriteEntry(block big.Int, tx common.Hash, from string, to string, value big.Int, gasPrice big.Int, gasUsed uint64)``` writes the result of a single transaction to the mongoDB instance.
- This is invoked in ```core/state_process.go``` in the ```applyTransaction``` function. 
- If there is an error in logging the data (such as the mongoDB server refuses the connection), the program will log the error, but not panic.

## Example transaction & output
The format of the optrace output is: the following: pc, depth, opcode,gas, cost, output
The format of the function traces is: index, calltype, depth, fromStr, toStr, valueStr, gas, inputStr, outputStr
The format of the event trace is: address, topics, data
The format of the transfer trace is: from, to, value, depth

This is an example transaction output for 0x438d08548ecb2233443c2978b6a8099bde3763baceffcf2963fd80665d147c01 on Ethereum.
```{  
  "_id": {    
    "$oid": "634d91a97ea5d071460ce00e"  },  
    "block": 182278,  
    "tx": "0x438d08548ecb2233443c2978b6a8099bde3763baceffcf2963fd80665d147c01",  "from": "0x8266c4a0e9301661F19C936B7bd16c0dFA37C6e6",  
    "to": "0x84cB2FD6f7B123acC0762Ba4A8E1E3987cBa125D",  "value": "0",  "gasprice": "50000000000",  
    "gasused": "41845",  
    "optrace": "0,1,PUSH1,0,3,0x\n0,1,PUSH2,0,3,0x023f\n0,1,MSTORE8,0,57,0x\n0,1,PUSH29,0,3,0x0100000000000000000000000000000000000000000000000000000000\n0,1,PUSH1,0,3,0x\n0,1,CALLDATALOAD,0,3,0x48a6ea3b00000000000000000000000000000000000000000000000000000000\n0,1,DIV,0,5,0x\n0,1,PUSH4,0,3,0x48a6ea3b\n0,1,DUP2,0,3,0x\n0,1,EQ,0,3,0x\n0,1,ISZERO,0,3,0x\n0,1,PUSH2,0,3,0x0147\n0,1,JUMPI,0,10,0x\n0,1,PUSH1,0,3,0x04\n0,1,CALLDATALOAD,0,3,0x000000000000000000000000000000000000000000000000000000000002c804\n0,1,PUSH1,0,3,0x40\n0,1,MSTORE,0,3,0x\n0,1,PUSH1,0,3,0x40\n0,1,MLOAD,0,3,0x02c804\n0,1,NUMBER,0,2,0x02c806\n0,1,SUB,0,3,0x\n0,1,NUMBER,0,2,0x02c806\n0,1,SUB,0,3,0x\n0,1,BLOCKHASH,0,20,0xff80d9f7dd96851149231345d3fc578974d06d527a6a7dbf78e455ea43942080\n0,1,PUSH1,0,3,0x60\n0,1,MSTORE,0,3,0x\n0,1,PUSH1,0,3,0x\n0,1,PUSH1,0,3,0x60\n0,1,MLOAD,0,3,0xff80d9f7dd96851149231345d3fc578974d06d527a6a7dbf78e455ea43942080\n0,1,EQ,0,3,0x\n0,1,ISZERO,0,3,0x\n0,1,PUSH2,0,3,0x013e\n0,1,JUMPI,0,10,0x\n0,1,JUMPDEST,0,1,0x\n0,1,PUSH1,0,3,0x60\n0,1,MLOAD,0,3,0xff80d9f7dd96851149231345d3fc578974d06d527a6a7dbf78e455ea43942080\n0,1,PUSH1,0,3,0x40\n0,1,MLOAD,0,3,0x02c804\n0,1,SSTORE,0,20000,0x\n0,1,JUMPDEST,0,1,0x\n0,1,JUMPDEST,0,1,0x\n0,1,PUSH4,0,3,0x7a05a2c7\n0,1,DUP2,0,3,0x\n0,1,EQ,0,3,0x\n0,1,ISZERO,0,3,0x\n0,1,PUSH2,0,3,0x028f\n0,1,JUMPI,0,10,0x\n0,1,JUMPDEST,0,1,0x\n0,1,PUSH4,0,3,0x2fc39764\n0,1,DUP2,0,3,0x\n0,1,EQ,0,3,0x\n0,1,ISZERO,0,3,0x\n0,1,PUSH2,0,3,0x02c7\n0,1,JUMPI,0,10,0x\n0,1,JUMPDEST,0,1,0x\n0,1,POP,0,2,0x\n0,1,STOP,0,0,0x",  "functrace": "0,CALL,0,0x8266c4a0e9301661F19C936B7bd16c0dFA37C6e6,0x84cB2FD6f7B123acC0762Ba4A8E1E3987cBa125D,0,68408,0x48a6ea3b000000000000000000000000000000000000000000000000000000000002c804,0x,[],[]",  
    "eventtrace": "",  
    "transfertrace": "0x8266c4a0e9301661F19C936B7bd16c0dFA37C6e6 0x84cB2FD6f7B123acC0762Ba4A8E1E3987cBa125D,0,0,0,[]"
}```

Here is an example of a multi-call transaction, where the ordering of the transactions is done based on the time of execution completion, rather than execution initialization (from tx 0x779a37efdadd72b239fe245b538eb83fc98aea2bb7ffdce52d38a50af621977c).
```1,CALL,1,0x4e9Ad443432C3157634f7e30A98DFd524F092455,0x1d11e5eaE3112dbD44f99266872FF1D07C77DCe8,0,150047,0x38cc4831,0x0000000000000000000000002bcc5943c2264648824ee9a479c351c74273453d,[1]
2,CALL,1,0x4e9Ad443432C3157634f7e30A98DFd524F092455,0x2BCC5943c2264648824Ee9A479c351C74273453D,0,144513,0xc281d19e,0x00000000000000000000000026588a9301b0428d95e6fc3a5024fce8bec12d51,[2]
3,CALL,1,0x4e9Ad443432C3157634f7e30A98DFd524F092455,0x1d11e5eaE3112dbD44f99266872FF1D07C77DCe8,0,133119,0x38cc4831,0x0000000000000000000000002bcc5943c2264648824ee9a479c351c74273453d,[3]
4,CALL,1,0x4e9Ad443432C3157634f7e30A98DFd524F092455,0x2BCC5943c2264648824Ee9A479c351C74273453D,0,127247,0x60f6670100000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000006496f5444414f0000000000000000000000000000000000000000000000000000,0x,[4]
5,CALL,1,0x4e9Ad443432C3157634f7e30A98DFd524F092455,0x1d11e5eaE3112dbD44f99266872FF1D07C77DCe8,0,121274,0x38cc4831,0x0000000000000000000000002bcc5943c2264648824ee9a479c351c74273453d,[5]
6,CALL,1,0x4e9Ad443432C3157634f7e30A98DFd524F092455,0x2BCC5943c2264648824Ee9A479c351C74273453D,0,115063,0x524f38890000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000355524c0000000000000000000000000000000000000000000000000000000000,0x0000000000000000000000000000000000000000000000000000000000000000,[6]
8,CALL,2,0x2BCC5943c2264648824Ee9A479c351C74273453D,0xf65B3B60010d57d0bb8478aA6cEd15fE720621b4,0,0,0x,0x,[7 8]
7,CALL,1,0x4e9Ad443432C3157634f7e30A98DFd524F092455,0x2BCC5943c2264648824Ee9A479c351C74273453D,0,103761,0xadf59f99000000000000000000000000000000000000000000000000000000000000003c000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000000355524c0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000004c6a736f6e2868747470733a2f2f6170692e6b72616b656e2e636f6d2f302f7075626c69632f5469636b65723f706169723d455448584254292e726573756c742e58455448585842542e632e300000000000000000000000000000000000000000,0x867f35abdb6852da5db5d4575c2f37c9bd70ad95aa02ba3f9c9884bf905d3a4c,[7]
0,CALL,0,0x26588a9301b0428d95e6Fc3A5024fcE8BEc12D51,0x4e9Ad443432C3157634f7e30A98DFd524F092455,0,175528,0x27dc297e6cc3f4f81522e891bbee6e2a24143929338e482d4b136a899f3350bb5514bb4600000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000008302e303032343430000000000000000000000000000000000000000000000000,0x,[],[]``` 

Note how the call that initializes first (identified by the first value in each row), is actually the call that is logged last, since the first call does not complete until any child calls complete.
```

# Decompiler
The decompiler converts the MongoDB transaction logs into an intermediate representation that is then used by the heuristics analyzer. More information about the decompiler can be found in the file `pyanalze/README.md`. To decompile a single transaction into an intermediate representation, follow the following command (with the pyanalyze folder):

First, install dependencies. Dependencies are located within the `pyanalze/requirements.txt` file and can be installed via `python -m pip install -r requirements.txt`. Then, you can run the analyzer via invoking the following arguments: 

```
sh ./bin/decompile.sh tx_hash
```

Where the tx_hash is the transaction hash of the transaction to be analyzed. The decompiler supports other options and can be invoked directly via calling `python bin/decompile`. A list of them all are below
```
python ./bin/decompile infile *options
  *options:
  - t / tsv: where to output the tabs-seperated facts file to. In the example decompile.sh
    file, this is set to 'facts-tmp'. This folder is then read from in the analyzer.
  - o / opcodes: the set of opcodes to output .facts files for. We do analysis over the
    following opcodes currently:
    CREATE BALANCE CALLER CALLVALUE STOP RETURN REVERT ORIGIN CALLDATALOAD EQ TIMESTAMP
    NUMBER DIFFICULTY COINBASE BLOCKHASH GASLIMIT EXTCODESIZE SELFDESTRUCT JUMPI JUMP
    JUMPDEST SSTORE SLOAD CALL DELEGATE CALLCODE STATICCALL
  - c / config: overrides the default configuration via a configuration string
  - C / config_file: overrides the default configuration via a configuration file
  - v / vv / verbose / prolix: varying levels of verbosity for the decompiler output
  - V / version: output decompiler version
  - txhash : the transaction hash of the transction to analyze
  - u / uri : the uri of the mongoDB instance to connect to
  - d / db : the database to read from in MongoDB
  - col / collection : the collection to read from in mongoDB
```

This will then output the .facts file to the tsv folder path. 

For info on the analysis stage, see `pyanalyze/readme.md`