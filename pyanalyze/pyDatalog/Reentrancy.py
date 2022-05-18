from memory import Memory
from pyDatalog import pyDatalog

def main(mem : Memory):
    print(mem.is_connected("V1339","V1342"))

    print(mem.find_instr("JUMPI"))