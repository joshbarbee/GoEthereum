package mgologger

import (
	"bytes"
	"encoding/hex"
	"fmt"
	"log"
	"math/big"
	"os"

	"github.com/ethereum/go-ethereum/common"
	"github.com/ethereum/go-ethereum/crypto"
	"github.com/globalsign/mgo"
	"github.com/holiman/uint256"
	"github.com/joho/godotenv"
)

type Collection struct {
	Block      string
	Tx         string
	From       string
	To         string
	Value      string
	GasPrice   string
	GasUsed    string
	Optrace    string
	Functrace  string
	Eventtrace string
}

var (
	logger            *mgo.Session
	Db                *mgo.Database
	BaseOptracestr    string
	BaseFunctracestr  string
	BaseEventtracestr string
	BaseERC721str     string
	BaseERC20str      string
	Functrace         *bytes.Buffer
	Optrace           *bytes.Buffer
	Eventtrace        *bytes.Buffer
	firstOpWrite      bool
	depthBuffer       [1025]*bytes.Buffer
	currentDepth      int
	TransferSig       common.Hash
	ApprovalSig       common.Hash
	ApprovalForAllSig common.Hash
)

func InitLogger() {
	err := godotenv.Load("../.env")
	if err != nil {
		log.Fatal("Failed to log godotenv")
	}

	_ = os.Getenv("DBPASS")

	url := "mongodb://127.0.0.1:27017"

	// initialize log for current tx
	BaseOptracestr = "pc,depth,opcode,gas,output\n"
	BaseFunctracestr = "calltype,depth,from,to,val,gas,input,output\n"
	BaseEventtracestr = "address,topics,data,type,function\n"

	Optrace = bytes.NewBuffer(make([]byte, 16000000))
	Functrace = bytes.NewBuffer(make([]byte, 8000000))
	Eventtrace = bytes.NewBuffer(make([]byte, 8000000))

	for i := 0; i < 1025; i++ {
		depthBuffer[i] = bytes.NewBuffer(make([]byte, 10000))
	}

	currentDepth = 0

	// initialize event function signatures for token tracing
	TransferSig = crypto.Keccak256Hash([]byte("Transfer(address,address,uint256)"))
	ApprovalSig = crypto.Keccak256Hash([]byte("Approval(address,address,uint256)"))
	ApprovalForAllSig = crypto.Keccak256Hash([]byte("Approval(address,address,bool)"))

	session, err := mgo.Dial(url)

	if err != nil {
		log.Fatal(err)
	}

	logger = session

	Db = session.DB("ethereum")
}

func InitTrace() {
	Optrace.Reset()
	Functrace.Reset()
	Eventtrace.Reset()

	Optrace.WriteString(BaseOptracestr)
	Functrace.WriteString(BaseFunctracestr)
	Eventtrace.WriteString(BaseEventtracestr)

	for i := 0; i < 1025; i++ {
		depthBuffer[i].Reset()
	}

	currentDepth = 0

	firstOpWrite = true
}

func AddOpLog(pc uint64, depth uint64, op string, gas uint64, gasCost uint64, extra string, isCall bool) {
	if firstOpWrite {
		Optrace.WriteString(fmt.Sprintf("%d,%d,%s,%d,%d,", pc, depth, op, gas, gasCost))
	} else {
		Optrace.WriteString(fmt.Sprintf("%s\n%d,%d,%s,%d,%d,", extra, pc, depth, op, gas, gasCost))
	}

	firstOpWrite = false
}

func EndOpLog(ret string, tx common.Hash) {
	txCopy := tx.String()

	if txCopy != "0x0000000000000000000000000000000000000000000000000000000000000000" {
		Optrace.WriteString(ret)
		Optrace.WriteString(txCopy)
	}
}

func AddFuncLog(ct string, d int, from string, to string, value uint256.Int, g uint64, input string, output string) {
	val := value.String()

	depthBuffer[d].WriteString(fmt.Sprintf("%s,%d,%s,%s,%s,%d,0x%s,0x%s\n", ct, d, from, to, val, g, input, output))

	for d < currentDepth {
		depthBuffer[currentDepth-1].WriteString(depthBuffer[currentDepth].String())
		depthBuffer[currentDepth].Reset()

		currentDepth--
	}

	if d == 0 {
		for currentDepth > d {
			depthBuffer[currentDepth-1].WriteString(depthBuffer[currentDepth].String())
			depthBuffer[currentDepth].Reset()

			currentDepth--
		}

		Functrace.WriteString(depthBuffer[0].String())
		depthBuffer[0].Reset()
	}

	currentDepth = d
}

func AddEventLog(addr common.Address, topics []common.Hash, data []byte) {
	res, function := isERC20(topics, data)

	if res {
		Eventtrace.WriteString(fmt.Sprintf("%s,%s,0x%s,ERC20,%s\n", addr, topics, hex.EncodeToString(data), function))
		return
	}

	res, function = isERC721(topics, data)
	if res {
		Eventtrace.WriteString(fmt.Sprintf("%s,%s,0x%s,ERC721,%s\n", addr, topics, hex.EncodeToString(data), function))
		return
	}

	Eventtrace.WriteString(fmt.Sprintf("%s,%s,0x%s,,\n", addr, topics, hex.EncodeToString(data)))
}

// we check if erc20 based on following info:
// 1. if event signature is Transfer(from,to,value) or Approval(owner,spender,value)
// 2. length of topics is 3
func isERC20(topics []common.Hash, data []byte) (ret bool, function string) {
	if len(topics) != 3 {
		return false, ""
	}

	switch topics[0] {
	case TransferSig:
		return true, "Transfer"
	case ApprovalSig:
		return true, "Approval"
	default:
		return false, ""
	}
}

// we check if erc721 based on following info
// 1. if event sig is Transfer(from,to,value) or Approval(owner,spender,value) or ApporvalForAll(address,address,bool)
// 2. length of topics is 4
func isERC721(topics []common.Hash, data []byte) (ret bool, function string) {
	if len(topics) != 4 {
		return false, ""
	}

	switch topics[0] {
	case TransferSig:
		return true, "Transfer"
	case ApprovalSig:
		return true, "Approval"
	case ApprovalForAllSig:
		return true, "ApprovalForAll"
	default:
		return false, ""
	}
}

func WriteEntry(block big.Int, tx common.Hash, from string, to string, value big.Int, gasPrice big.Int, gasUsed uint64, extra string) {
	if Optrace.String() != fmt.Sprint(BaseOptracestr+tx.String()) {
		trace := Collection{
			Block:      block.String(),
			Tx:         tx.String(),
			From:       from,
			To:         to,
			Value:      value.String(),
			GasPrice:   gasPrice.String(),
			GasUsed:    fmt.Sprintf("%d", gasUsed),
			Functrace:  Functrace.String()[:len(Functrace.String())-1],
			Eventtrace: Eventtrace.String()[:len(Eventtrace.String())-1], // remove newline
			Optrace:    Optrace.String()[:len(Optrace.String())-len(tx.String())] + extra,
		}
		err := Db.C("traces_test").Insert(trace)

		trace = Collection{}

		if err != nil {
			log.Println(err, ". Unable to log transaction tx: ", tx)
			return
		}
	}

	InitTrace()
}

func CloseMongo() {
	defer logger.Close()
}
