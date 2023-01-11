package mgologger

import (
	"bytes"
	"encoding/hex"
	"fmt"
	"log"
	"math/big"
	"strings"

	"github.com/ethereum/go-ethereum/common"
	"github.com/globalsign/mgo"
)

type MongoConfig struct {
	MongoURI       string
	DatabaseName   string
	CollectionName string
}

type Collection struct {
	Block         int
	Tx            string
	From          string
	To            string
	Value         string
	GasPrice      string
	GasUsed       string
	OpTrace       string
	FuncTrace     string
	EventTrace    string
	TransferTrace string
}

var (
	Logger     *mgo.Session
	Db         *mgo.Database
	collection string

	opTrace       *bytes.Buffer
	funcTrace     *bytes.Buffer
	eventTrace    *bytes.Buffer
	transferTrace *bytes.Buffer

	TraceIndex int
	CallStack  [1025]uint

	OpTraceFormat       = "pc, depth, opcode,gas, cost, output"
	FuncTraceFormat     = "index, calltype, depth, fromStr, toStr, valueStr, gas, inputStr, outputStr"
	EventTraceFormat    = "address,topics,data"
	TransferTraceFormat = "from, to, value, depth"
)

func InitLogger(cfg MongoConfig) {
	opTrace = bytes.NewBuffer(make([]byte, 8_000_00))
	funcTrace = bytes.NewBuffer(make([]byte, 2_000_000))
	eventTrace = bytes.NewBuffer(make([]byte, 500_000))
	transferTrace = bytes.NewBuffer(make([]byte, 500_000))

	for i := 0; i < 1024; i++ {
		CallStack[i] = 0
	}

	TraceIndex = 0

	session, err := mgo.DialWithTimeout(cfg.MongoURI, 0)
	if err != nil {
		log.Fatal(err)
	}

	Logger = session

	Db = session.DB(cfg.DatabaseName)
	collection = cfg.CollectionName
}

func InitTrace() {
	opTrace.Reset()
	funcTrace.Reset()
	eventTrace.Reset()
	transferTrace.Reset()

	for i := 0; i < 1024; i++ {
		CallStack[i] = 0
	}

	TraceIndex = 0
}

func AddOpLog(pc uint64, depth uint64, op string, gas uint64, gasCost uint64, ret []byte) {
	output := hex.EncodeToString(ret)
	opTrace.WriteString(fmt.Sprintf("%d,%d,%s,%d,%d,0x%s\n", pc, depth, op, gas, gasCost, output))
}

func AddFuncLog(index int, calltype string, depth int, from common.Address, to common.Address, value big.Int, gas uint64, input []byte, output []byte) {
	fromStr := from.String()
	toStr := to.String()
	valueStr := value.String()
	inputStr := hex.EncodeToString(input)
	outputStr := hex.EncodeToString(output)

	if depth == 0 {
		funcTrace.WriteString(fmt.Sprintf("%d,%s,%d,%s,%s,%s,%d,0x%s,0x%s,[],[]\n", index, calltype, depth, fromStr, toStr, valueStr, gas, inputStr, outputStr))
	} else {
		funcTrace.WriteString(fmt.Sprintf("%d,%s,%d,%s,%s,%s,%d,0x%s,0x%s,%+v\n", index, calltype, depth, fromStr, toStr, valueStr, gas, inputStr, outputStr, CallStack[1:depth+1]))
	}
}

func AddEventLog(addr common.Address, topics []common.Hash, data []byte) {
	eventTrace.WriteString(fmt.Sprintf("%s,%s,0x%s,%d\n", addr, topics, hex.EncodeToString(data), TraceIndex))
}

// Invoked on balance transfer from account A to account B
func AddTransferLog(from common.Address, to common.Address, value big.Int, depth int) {
	var output string

	if depth == 0 {
		output = fmt.Sprintf("%s,%s,%s,%d,%d,[]\n", from.String(), to.String(), value.String(), depth, TraceIndex)
	} else {
		output = fmt.Sprintf("%s,%s,%s,%d,%d,%+v\n", from.String(), to.String(), value.String(), depth, TraceIndex, CallStack[1:depth+1])
	}

	transferTrace.WriteString(output)
}

// we check if erc721 based on following inf
func WriteEntry(block big.Int, tx common.Hash, from string, to string, value big.Int, gasPrice big.Int, gasUsed uint64) {
	opTraceStr := strings.TrimSuffix(string(bytes.Trim(opTrace.Bytes(), "\x00")), "\n")
	funcTraceStr := strings.TrimSuffix(string(bytes.Trim(funcTrace.Bytes(), "\x00")), "\n")
	eventTraceStr := strings.TrimSuffix(string(bytes.Trim(eventTrace.Bytes(), "\x00")), "\n")
	transferTraceStr := strings.TrimSuffix(string(bytes.Trim(transferTrace.Bytes(), "\x00")), "\n")

	if opTraceStr == "" {
		return // early return if tx is eoa->eoa
	}

	trace := Collection{
		Block:         int(block.Uint64()),
		Tx:            tx.String(),
		From:          from,
		To:            to,
		Value:         value.String(),
		GasPrice:      gasPrice.String(),
		GasUsed:       fmt.Sprintf("%d", gasUsed),
		OpTrace:       opTraceStr,
		FuncTrace:     funcTraceStr,
		EventTrace:    eventTraceStr,
		TransferTrace: transferTraceStr,
	}

	err := Db.C(collection).Insert(trace)

	if err != nil {
		log.Println(err, ". Unable to log transaction tx: ", tx)
	}
}

func CloseMongo() {
	defer Logger.Close()
}
