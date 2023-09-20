# Arithmetic Ops and STOP
- STOP = code: 0x00 uses: 0 defines: 0
- ADD = code: 0x01 uses: 2 defines: 1
- MUL = code: 0x02 uses: 2 defines: 1
- SUB = code: 0x03 uses: 2 defines: 1
- DIV = code: 0x04 uses: 2 defines: 1
- SDIV = code: 0x05 uses: 2 defines: 1
- MOD = code: 0x06 uses: 2 defines: 1
- SMOD = code: 0x07 uses: 2 defines: 1
- ADDMOD = code: 0x08 uses: 3 defines: 1
- MULMOD = code: 0x09 uses: 3 defines: 1
- EXP = code: 0x0A uses: 2 defines: 1
- SIGNEXTEND = code: 0x0B uses: 2 defines: 1

# Comparison and Bitwise Logic
- LT = code: 0x10 uses: 2 defines: 1
- GT = code: 0x11 uses: 2 defines: 1
- SLT = code: 0x12 uses: 2 defines: 1
- SGT = code: 0x13 uses: 2 defines: 1
- EQ = code: 0x14 uses: 2 defines: 1
- ISZERO = code: 0x15 uses: 1 defines: 1
- AND = code: 0x16 uses: 2 defines: 1
- OR = code: 0x17 uses: 2 defines: 1
- XOR = code: 0x18 uses: 2 defines: 1
- NOT = code: 0x19 uses: 1 defines: 1
- BYTE = code: 0x1A uses: 2 defines: 1
- SHA3 = code: 0x20 uses: 2 defines: 1

# Environmental Information
- ADDRESS = code: 0x30 uses: 0 defines: 1
- BALANCE = code: 0x31 uses: 1 defines: 1
- ORIGIN = code: 0x32 uses: 0 defines: 1
- CALLER = code: 0x33 uses: 0 defines: 1
- CALLVALUE = code: 0x34 uses: 0 defines: 1
- CALLDATALOAD = code: 0x35 uses: 1 defines: 1
- CALLDATASIZE = code: 0x36 uses: 0 defines: 1
- CALLDATACOPY = code: 0x37 uses: 3 defines: 0
- CODESIZE = code: 0x38 uses: 0 defines: 1
- CODECOPY = code: 0x39 uses: 3 defines: 0
- GASPRICE = code: 0x3A uses: 0 defines: 1
- EXTCODESIZE = code: 0x3B uses: 1 defines: 1
- EXTCODECOPY = code: 0x3C uses: 4 defines: 0

# Block Information
- BLOCKHASH = code: 0x40 uses: 1 defines: 1
- COINBASE = code: 0x41 uses: 0 defines: 1
- TIMESTAMP = code: 0x42 uses: 0 defines: 1
- NUMBER = code: 0x43 uses: 0 defines: 1
- DIFFICULTY = code: 0x44 uses: 0 defines: 1
- GASLIMIT = code: 0x45 uses: 0 defines: 1

# Stack, Memory, Storage, Flow
- POP = code: 0x50 uses: 1 defines: 0
- MLOAD = code: 0x51 uses: 1 defines: 1
- MSTORE = code: 0x52 uses: 2 defines: 0
- MSTORE8 = code: 0x53 uses: 2 defines: 0
- SLOAD = code: 0x54 uses: 1 defines: 1
- SSTORE = code: 0x55 uses: 2 defines: 0
- JUMP = code: 0x56 uses: 1 defines: 0
- JUMPI = code: 0x57 uses: 2 defines: 0
- PC = code: 0x58 uses: 0 defines: 1
- MSIZE = code: 0x59 uses: 0 defines: 1
- GAS = code: 0x5A uses: 0 defines: 1
- JUMPDEST = code: 0x5B uses: 0 defines: 0
- PUSH1 = code: 0x60 uses: 0 defines: 1
- PUSH32 = code: 0x7F uses: 0 defines: 1
- DUP1 = code: 0x80 uses: 1 defines: 2
- DUP16 = code: 0x8F uses: 16 defines: 17
- SWAP1 = code: 0x90 uses: 2 defines: 2
- SWAP16 = code: 0x9F uses: 17 defines: 17
# Logging
- LOG0 = code: 0xA0 uses: 2 defines: 0
- LOG1 = code: 0xA1 uses: 3 defines: 0
- LOG2 = code: 0xA2 uses: 4 defines: 0
- LOG3 = code: 0xA3 uses: 5 defines: 0
- LOG4 = code: 0xA4 uses: 6 defines: 0

# System Operations
- CREATE = code: 0xF0 uses: 3 defines: 1
- CREATE2 = code: 0xF5 uses: 4 defines: 1
- CALL = code: 0xF1 uses: 7 defines: 1
- CALLCODE = code: 0xF2 uses: 7 defines: 1
- RETURN = code: 0xF3 uses: 2 defines: 0
- DELEGATECALL = code: 0xF4 uses: 6 defines: 1
- INVALID = code: 0xFE uses: 0 defines: 0
- SELFDESTRUCT = code: 0xFF uses: 1 defines: 0

# New Byzantinium OpCodes for block.number >= BYZANTIUM_FORK_BLKNUM
- REVERT = code: 0xFD uses: 2 defines: 0
- RETURNDATASIZE = code: 0x3D uses: 0 defines: 1
- RETURNDATACOPY = code: 0x3E uses: 3 defines: 0
- STATICCALL = code: 0xFA uses: 6 defines: 1

# TAC Operations
# These are not EVM opcodes, but they are used by the three-address code
- NOP = code: -1 uses: 0 defines: 0
- CONST = code: -2 uses: 0 defines: 0
- LOG = code: -3 uses: 0 defines: 0
- THROW = code: -4 uses: 0 defines: 0
- THROWI = code: -5 uses: 0 defines: 0