### This is the main pyDatalog-based Souffle variant python parser. 

The entrypoint for the program is at main.py. The program takes 
one mandatory argument. 
1. The path to the .facts folder containing the intermediate .facts
   representation. The argument should include the backslash at the
   end of the path

At this point, the memory for the .facts folder is loaded in at
memory.py. Memory.py loads in the opAll.facts folder, creating initial
dataframes consisting of all opcode info and all mapping relationships
between defined and used variables and operations. 

## Memory.py
`Memory.load(self)`
- No parameters
- Returns None
- Runs Memory.__load_facts(). Then processes each opcode and converts
  list of dataframe rows to dataframe

`Memory.__load_facts(self)`
- No parameters
- Returns None
- Loads in the opAll.facts file into a pandas dataframe. Then creates
  a mapping between each opcode and all rows matching that opcode, into
  the self.ops dict. 
  - Draws edges between a defined variable symbol and used variable symbol
    for later graph-relationship checking with the can_reach dependency
  - Stores value(var_symbol, value) relationships when a variable is defined
  - Creates a addr((call_number, depth), address) dependency when the address
  of execution is changed. This allows us to see the smart contract currently
  executing the ops.

`Memory._contains_instr(self)`
- var : str (Parent variable to begin search at)
- instr : str (Instruction op name to match with)
- call_num : int (Call number required to be same for matches)
- returns boolean on whether var is linked to instr via any children opcodes or
  def-use variables


After the memory is loaded, the vulnerability analysis begins. The 
different vulnerability heuristics are below:

## 1: Reentrancy
# 1st step:
In the first step, we first find all SLOAD instructions. We only wish
to find instructions where the depth is greater than 2. We use the 
Memory.find_instr_depth(instr: str, min_depth : int) function to find
all SLOAD at depth >= 3. We then reduce the set of SLOADS to the set of SLOAD
where a JUMPI instruction was found as an edge to the variable defined by SLOAD

# 2nd step:
In the second step, we find all SSTORE instructions such that the lowest depth
of the SSTORE instruction is one less than the lowest depth of all SLOAD
instructions. We then reduce the set of SSTORE instructions such that they 
must all occur after the earliest SLOAD instruction. We then reduce the set 
of SSTOREs to only SSTOREs that have a value corresponding to the same 
value of any of our current SLOAD instructions

# 3rd step:
In the third step, we reduce on the address of SSTORE and SLOAD arguments. We
go through the list of SSTORE arguments and remove ones that did not occur at the
same smart contract address as any SLOADs. 