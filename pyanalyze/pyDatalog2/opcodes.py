from pyDatalog import pyDatalog
from typing import List
from pyDatalog import pyEngine
import logging

pyDatalog.create_terms("edge,defined,use,op,value,val,H,T,var,stmt,addr,_,"
                        "var1,caller,loc,cd,cn,i,op,arg_loc,dest,arg_addr,"
                        "arg_val,size,var2,left_var,right_var,res_var,"
                        "data_start,data_length,address,return_start,"
                        "return_length,success,cond,gas,target,res,offset,length")
pyDatalog.create_terms("op_SLOAD,op_JUMPI,op_SSTORE,op_LT,op_GT,_,X,"
                        "op_SLT,op_SGT,op_EQ,op_SUB,op_ADD,op_MUL,"
                        "op_EXP,op_CALLDATALOAD,op_EXTCODESIZE,"
                        "op_TIMESTAMP,op_NUMBER,op_COINBASE,op_DIFFICULTY,"
                        "op_GASLIMIT,op_ORIGIN,op_CALL,op_DELEGATECALL,"
                        "op_DELEGATE,op_STATICCALL,op_SELFDESTRUCT,op_CALLCODE,"
                        "op_REVERT,sc_addr,op_STOP,op_CALLER,op_RETURN")

pyEngine.logging = True
logging.basicConfig(level=logging.DEBUG)

'''
    Loads in every opcode. Creates a dependency between info in pyDatalog
'''
def define_ops():
    edge(H,T)
    defined(var,stmt,loc,cd,cn)
    use(var,stmt,i,loc,cd,cn)
    op(stmt,op,loc)
    value(var,val)

    op_SLOAD(stmt,arg_loc,val,loc,cd,cn)
    op_JUMPI(stmt,dest,cond,loc,cd,cn)
    op_SSTORE(stmt,arg_addr,arg_val,loc,cd,cn)

    # arithmetic ops
    op_LT(stmt,left_var,right_var,res_var,loc,cd,cn)
    op_GT(stmt,left_var,right_var,res_var,loc,cd,cn)
    op_SLT(stmt,left_var,right_var,res_var,loc,cd,cn)
    op_EQ(stmt,left_var,right_var,res_var,loc,cd,cn)
    op_SUB(stmt,left_var,right_var,res_var,loc,cd,cn)
    op_MUL(stmt,left_var,right_var,res_var,loc,cd,cn)
    op_EXP(stmt,left_var,right_var,res_var,loc,cd,cn)

    # call-related
    op_CALL(stmt,gas,target,value,data_start,data_length,return_start,return_length,success,loc,cd,cn)
    op_CALLCODE(stmt,gas,target,value,data_start,data_length,return_start,return_length,success,loc,cd,cn)
    op_DELEGATECALL(stmt,gas,target,value,data_start,data_length,return_start,return_length,success,loc,cd,cn)
    op_STATICCALL(stmt,gas,target,value,data_start,data_length,return_start,return_length,success,loc,cd,cn)
    
    # data related
    op_CALLDATALOAD(stmt,i,res,loc,cd,cn)
    op_EXTCODESIZE(stmt,addr,size,loc,cd,cn)
    op_TIMESTAMP(stmt,res_var,loc,cd,cn)
    op_NUMBER(stmt,res_var,loc,cd,cn)
    op_COINBASE(stmt,res_var,loc,cd,cn)
    op_DIFFICULTY(stmt,res_var,loc,cd,cn)
    op_GASLIMIT(stmt,res_var,loc,cd,cn)
    op_ORIGIN(stmt,res_var,loc,cd,cn)
    op_CALLER(stmt,caller,loc,cd,cn)
    
    # terminating opcodes

    op_SELFDESTRUCT(stmt,addr,loc,cd,cn)
    op_REVERT(stmt,var1,var2,loc,cd,cn)
    op_STOP(stmt,loc,cd,cn)
    op_RETURN(stmt,offset,length,loc,cd,cn)

    # other assorted dependency for smart contract addr
    sc_addr(address)

'''
    Loads in all defined opcodes and creates dependencies between op and datalog
'''
def load_ops(path : str):
    ops = __load_op(path, "SLOAD")
    __create_link(op_SLOAD, ops)
    +op_SLOAD(ops[0][0],ops[0][1],ops[0][2],ops[0][3],ops[0][4],ops[0][5])
    print(op_SLOAD(_,_,_,_,_,_))
'''
    Loads in an individual opcode from .fact file. 
    Returns all rows from the .facts file, which the 
    individual op dictates the behavior for in load_ops
'''
def __load_op(path : str, op : str) -> List[List[str]]:
    res = []
    with open(f"{path}/op_{op}.facts", "r") as f:
        for line in f.readlines():
            res.append(line.strip("\n").split("\t"))

    return res

def __create_link(var, ops): 
    for op in ops:
        +op_SLOAD(*op)