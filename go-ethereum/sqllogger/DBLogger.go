package sqllogger

import (
	"encoding/json"
	"fmt"
	"io/ioutil"

	"github.com/holiman/uint256"
)

type sqllog struct {
	Block    string
	Tx       string
	From     string
	To       string
	Value    uint64
	GasLimit uint64
	Logs     []trace
}

type trace struct {
	Pc           uint64
	Depth        uint64
	Opcode       string
	GasUsed      uint64
	GasRemaining uint64
	Stack        []uint256.Int
	Memory       []byte
	Storage      string
	ReturnData   []byte
}

var (
	globLogger = &sqllog{}
)

func InitRecord(block string, tx string, from string, to string, value uint64, gl uint64) {
	globLogger.Block = block
	globLogger.Tx = tx
	globLogger.From = from
	globLogger.To = to
	globLogger.Value = value
	globLogger.GasLimit = gl
}

func AddEntry(pc uint64, depth uint64, op string, gU uint64, gR uint64, st []uint256.Int, mem []byte, stg string, retData []byte) {
	globLogger.Logs = append(globLogger.Logs, trace{Pc: pc, Depth: depth, Opcode: op, GasUsed: gU, GasRemaining: gR, Stack: st, Memory: mem, Storage: stg, ReturnData: retData})
}

func WriteEntry() {
	file, _ := json.MarshalIndent(globLogger, "", " ")
	path := fmt.Sprintf("../logs/output-%s.json", globLogger.Tx)
	_ = ioutil.WriteFile(path, file, 0644)
}
