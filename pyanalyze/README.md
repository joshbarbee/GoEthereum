This is the pure-Python implementation of the work accomplished in TxSpector. Rather than using Datalog, we represent the relationship between opcodes as a custom Python class, `OpView`, which contains a collection of opcodes based on user-provided parameters, as well as functions to further filter the opcodes based on discrete values, as well as relations to other `OpViews`.

Currently, transaction data is collected via a modified full Go-Ethereum node, which exports the data to MongoDB. See documentation in the `/GoEthereum` folder for more info. The Python wrapper for this MongoDB instance can be found in the `analyzer/mgofetcher.py` file.

This implementation relies on the work done by Vandal to parse the transaction into a representation that allows us to conduct analysis. The Vandal program has been modified to support transactions (originally it was made for contracts) and a helper function, `tac_cfg.TacGraph.from_trace`, which is able to directly parse the MongoDB logs.

# Installation
`pip install -r requirements.txt`

# Running
*See examples/example_\* for examples of existing heuristics* 

*Assuming we are using data hosted on our MongoDB instance*

## Example
```
mkdir examples/output
python examples/example_reentrancy.py *tx_hash*
```

This will create a CSV file in the folder `examples/output` with the results of the reentrancy heuristic on the transaction, allowing further analysis to be conducted on the particular calls, SLOADs, and JUMPI instructions that may be evidence of reentrancy.

Ensure that the transaction is present in the MongoDB database before searching if possible. Otherwise, the program may spend a decent amount of time stuck attempting to search a (rather large) MongoDB collection for a non-existent transaction.

## Custom Script

This is not a guide that is able to be copy-pasted and used instantly. Rather, it shows the different steps that are taken to write a heuristic and serves as a guide to basic API calls. Steps 1-3 should always be executed in order. After an `OpView` is first queried from the `OpAnalyzer`, subsequent linking and filtering can be done at any time, not necessarily in the numerical order below. Step 6 can only be executed AFTER a linkage has been first made.

1. Import `mgofetcher` to be able to read data from MongoDB, `api` to import the common API `OpAnalyzer` used to first query `OpView` objects. Also, import the `operator` class (explained later)
```
import decompiler.mgofetcher as mgofetcher
import decompiler.analyzer.api as api
import decompiler.tac_cfg as tac_cfg
import operator
```

2. Set up the parameters for MongoDB and create an instance of the `MongoFetcher` class
```
URI = "mongodb://127.0.0.1"
COLLECTION = "ethereum"
DATABASE = "ethlogger"
TX_HASH = "0x37085f336b5d3e588e37674544678f8cb0fc092a6de5d83bd647e20e5232897b"

fetcher = mgofetcher.MongoFetcher(URI, DATABASE, COLLECTION)
```

3. Get the transaction query data from MongoDB. Then, we can initialize the common API in one of two ways:
```
tx = fetcher.get_tx(TX_HASH)
cfg = tac_cfg.TACGraph.from_trace(tx)
api = api.OpAnalyzer(cfg)
```
Or
```
tx = fetcher.get_tx(TX_HASH)
api = api.OpAnalyzer.load_from_mongo(tx)
```

4. Query an initial set of opcodes based on initial conditions, giving us an `OpView`. By passing in the optional kwarg `depth=(operator.gt,2)`, we ensure that all `SLOAD` ops in our `SLOAD OpView` have a depth that is greater than 2.
```
SLOAD = api.get_ops("SLOAD", depth=(operator.gt, 2))
JUMPI = api.get_ops("JUMPI")
```
*See API query documentation below for more info on filters*

5. Link one OpView to another OpView to allow us to link together separate OpViews, allowing us to link only on certain properties.
```
SLOAD.link_ops(jumpi, call_index=operator.eq, depth=operator.eq)
SLOAD.link_ops(sstore, depth=lambda x, y: x - 2 > y, op_index=operator.lt, save_links=True)
```

In the first example, we will iterate through all SLOAD ops in the SLOAD `OpView`. Then, for any JUMPI in the JUMPI `OpView`, if the call index is equal (did the opcodes happen during the same call) and the depth is equal, we will create a link from that JUMPI op to that SLOAD op. If no linkage exists, then we will remove the SLOAD frop the SLOAD `OpView`. This allows us to perform further analysis on SLOAD where SLOAD must satisfy dependencies relative to other variables. 

For instance, if there is a SLOAD op with a call index of 3 and depth of 2, but there is no JUMPI with a call index of 3 and depth of 2, that particular SLOAD op will be removed.

*The save_links option is required if an OpView is linked more than once, and you want to maintain linkages to the original OpView, as well as the new OpView*

6. Reduce links made between OpViews based on variables the ops use or define. If you have some knowledge about the particular opcodes to be analyzed, then the lower-level APIs of `reduce_descendant, reduce_ancestor, reduce_value` can be used. These functions support querying directly on opcode arguments, the values of these arguments, and defined variables by that particular opcode. 

However, there are also easier-to-use APIs that do not require a semantic knowledge about the relevancy of particular variables to particular opcodes.
```
sload.reduce_descendant(self_def_var=True, link_def_var=False, link_use_vi=1)
sload.reduce_value(operator.ne, self_def_var=False, self_use_vi = 0, link_def_var=False, link_use_vi=0)
```
In the first, we analyze the dependencies between variables that our SLOAD defines (denoted by `self_def_var=True`) and variables that ops linked to the SLOAD use (`link_def_var=False`). Because we have some semantic knowledge about the particular opcode argument we want to analyze for the linked ops, when we are searching through the graph of variable dependencies, we will only look at the 2nd argument passed to the linked op when that linked op was invoked.

In the second, we reduce our `SLOAD OpView` based on the variables that the SLOAD opview uses, as well as the variables that linked ops to the `SLOAD OpView` use. Our first argument is `operator.ne`, indicating we want to remove any SLOAD where the value of the linked op's first argument is not equal to the value of the SLOAD op's first argument.

7. Exporting to a CSV. To export, make sure that the folder where the files should be written to exists. Then, we can export via 
```
sload.export("./examples/output/reentrancy.csv", cached_links=True)
```
*cached_links=True is used because for reentrancy, we are interested in both the existing links for the sload, as well as previous links we made*

# Profiling 
To run the profiler, run: 
```
python profiling/profiler.py N
```
which runs the sample heuristic (reentrancy) over N random transactions. Reentrancy is our most demanding heuristic typically, so it makes sense to test it specifically. Results of previous profiling runs can be seen in `profiling.out`

Last run:
```
Reentrancy Average (100): Memory: 77.81516808509826 MB Time: 3.582s
```

# API Documentation
Below is short documentation for each of the existing API functions. An explanation of intended usage is included. Longer documentation can be found in the source code. Since the Vandal functionality is largely unchanged, we are only documenting functions found in `decompiler/analyzer`, as well as the file `decompiler/mgofetcher`. Additionally, we only document functions that could realistically be called by a user. For documentation of methods not present below (like `decompiler.variable.Variable.get_ancestors`), see the source code.

`mgofetcher.MongoFetcher(mongoURI, db, collection)`
-
- `get_block(block : int)`: Returns a list containing the transaction dump of each transaction in the particular block that we collected output for
- `get_tx(tx : str)`: Returns a singular tx dump from MongoDB.

`analyzer.api.OpAnalyzer(source : TACGraph)`
-
- The OpAnalyzer is the entry point for interactions with the data generated by Vandal. To create an OpView (allowing further discrete analysis), an OpAnalyzer must first be generated
- `__load__`: Internal function used to intialize the OpViews. OpViews are stored in the OpAnalyzer as a dictionary, with the keys being the opcode name and value being the base OpView of that particular opcode (OpView consisting of all ops of that opcode)
- `load_from_mongo(cls, tx)`: Class method that handles consturction of TAC CFG as well as initialization of OpAnalyzer from results of TACCFG. Use in case you have no need to directly access the CFG, passing directly in the MongoDB query result for a particular transaction.
- `get_ops(opcode, **kwargs)`: Creates a new OpView of the passed opcode, where each op in the OpView matches bounds set in kwargs. Example kwargs inputs should be a 2-tuple, where the first is a binary function that outputs a boolean, and the second is a discrete value to bound check a property with. Each key in the kwargs should be a discrete property of the `Op` class (op_index, call_index, pc, depth). For example: `call_index=(operator.gt, 2)` or `op_index=(operator.lt, 1000)`
- `link_ops, filter, reduce_links, filter_value, reduce_value, reduce_descendant, reduce_ancestor, filter_address, reduce_address`: See below documentation for `OpView` API.

`analyzer.api.Op()`
-
- This is the object that is used to represent each op in an OpView. Typically, it should never be accessed directly.
- op_index: The index of the specific op in all of the ops executed by the transaction.
- call_index: The index of the specific call in all of the calls executed by the transaction.
- pc: The program counter of the op when executing in the transaction.
- depth: The call depth of the program at the time the op was executed.
- use_vars: A list of metavariables used by the op. The number of elements in the list is defined by the specific opcode being executed. A list of the arguments of each possible opcode is defined within `opcodes.md`.
- def_var: If the op defines a variable, maintains a reference to that metavariable. See `opcodes.md` for explanation of each OpCode

*Metavariables are used to represent variables defined and used by the program during run time. Since we are unable to determine the actual name of the variable, we use an intermediate symbol to represent such. The symbol used for these metavariables is VX, where X is an integer such as V1234*

`analyzer.api.OpView(Dict[Op, OpChain])`
- 
- The OpView is the datatype that is used for most relations and analysis. It is an extension of a dictionary, where the key is an `Op` object and the value is a list of `Op` objects that are linked to the particular key.
- In some functions, we pass the parameters `self_def_var: bool = True, self_use_vi: int = None, link_def_var: bool = True, link_use_vi: int = None)`, or some variant of such. `self_def_var` refers to the defined variable of an op in the OpView, `self_use_vi` represents the variable indice of a particular used variable in an op in the OpView. For any function definition `self_use_vi` or just `use_vi`, if `self_use_vi` and `self_def_var` are both false, then we default to checking the operator on all used variables. 
- When initializing, pass no arguments. The OpView should be built incrementally via `OpView.add_op` (see `decompiler/analyzer/api.py`).
- `add_op(op : Op)`: Adds a new op to the OpView. 
- `link_ops(other : OpView, save_links : bool = False, **kwargs)`: Link an `OpView` object to another `OpView` object. `**kwargs` key should be the name of a discrete property of Op, and the value should be an operator to act between self and other, For instance, `call_index=operator.gt` or `depth=operator.eq`. `link_ops` is the function with the room for the most optimzation. This is currently the most time-costly function. Read `caching` below to see current steps to improve performance.
- `filter(**kwargs)`: Filters an opview based on kwargs, with the key being a Op property and the value being a 2-tuple of a binary boolean function and a discrete value. For instance `op_index = (operator.lt, 100)` or `depth = (operator.gt, 3)`
- `reduce_links(**kwargs)`: Allows for post-initial linkage reduction of links between an OpView and linked ops. Supports same kwargs as `link_ops`.
- `filter_value(value : int, oper, def_var, use_vi)`: Filter an OpView to the set of ops that either have a defined variable or a used variable that, when first defined, had a value that satisfies the `oper` binary expression when compared to `value`. If `def_var` is True, then we will only look at the defined variable for each op in the OpView. If `use_vi` is set, then we will only consider ops that the `use_vi`-th used variable of that op satisifeis the binary `oper` expression.
- `reduce_value(oper: Callable, self_def_var: bool = True, self_use_vi: int = None, link_def_var: bool = True, link_use_vi: int = None,)`: Filter an OpView to the set of ops that either define or use a value that satisifies some binary expression with a defined or used variable from a linked op. 
- `reduce_descendant(self_def_var: bool = True, self_use_vi: int = None, link_def_var: bool = True, link_use_vi: int = None,)`: Reduce the ops in the OpView to only those who define / use a variable which is an ancestor of some linked op. That is, given an op defines a variable V13, and a linked op uses V13, there is an edge from the op to the linked op and we would keep op in the OpView.
- `reduce_ancestor(self_def_var: bool = True, self_use_vi: int = None, link_def_var: bool = True, link_use_vi: int = None,)`: Reduce the ops in the OpView to only those who define / use a variable which is an descendant of some linked op. That is, given an op defines a variable V13, and a linked op uses V13, there is an edge from the op to the linked op and we would keep op in the OpView.

*Note that the above two are complementary - that is - sload.reduce_descendant(jumpi) = jumpi.reduce_ancesotr(sload)*

- `filter_address(address : str)`: Reduce the ops in the OpView to only those which were executed by a particular address.
- `reduce_address()`: Reduces the ops in the OpView to only those executed in the same address as some currently linked op.
- `export(filepath : str = None, cached_links = False)`: Exports results to a CSV file. If there are cached results, they are appended to each row in the results. Results consist of each op's op index, call index, depth, and address for each op in the opView, for each linked op for that particular op.

# Caching
Previously, our program performance was terribly lacklusted. One particular stage of the reentrancy heuristic (the first linkage between SLOAD and JUMPI) could take up to 27 seconds. This was because we were not taking advantage of the fact that, if we know that, for some user-supplied `Op` properties (i.e depth == 2, call_index == 3,) a particular op in our `OpView` satisifies those constraints, then any other op also matching those properties will also satisfy those constraints.

Currently, there is some caching that occurs in `link_ops` to speed up linkage, but caching currently is only optimal if the comparision operator is equal or not equal. In cases such as operator.gt (a monotonic function), we know that if operator.gt is True for some particular property of an op1 in OpView, then any other op2 in the original OpView that has the same property with a value of less or equal to op1 will be able to cache op1's pre-computed linkages. 

However, this is not necessarily a trivial issue and likely requires some sort of implementation in Z3. The idea is to initially map all of the ops in the linkee OpView to a dictionary based on possible bounds computed by Z3, given the user parameters. Then, we can bound each op in the linker OpView and determine the pre-computed linkee ops that satisfy the bounds.

