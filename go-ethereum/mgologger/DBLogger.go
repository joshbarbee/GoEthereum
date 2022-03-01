package mgologger

import (
	"bytes"
	"fmt"
	"log"
	"math/big"
	"os"

	"github.com/ethereum/go-ethereum/common"
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

type ERC721Token struct {
	Amount   uint256.Int
	Creator  common.Address
	OriginTx common.Hash
	Contract common.Hash
	Events   []string
}

type ERC20Token struct {
	Amount   uint256.Int
	Creator  common.Address
	OriginTx common.Hash
	Contract common.Hash
	Events   []string
}

var (
	logger            *mgo.Session
	Db                *mgo.Database
	BaseOptracestr    string
	BaseFunctracestr  string
	BaseEventtracestr string
	Functrace         *bytes.Buffer
	Optrace           *bytes.Buffer
	Eventtrace        *bytes.Buffer
)

func InitLogger() {
	err := godotenv.Load("../.env")
	if err != nil {
		log.Fatal("Failed to log godotenv")
	}

	_ = os.Getenv("DBPASS")

	url := "mongodb://127.0.0.1:27017"

	// initialize log for current tx
	BaseOptracestr = "pc,depth,opcode,gas,extra\n"
	BaseFunctracestr = "calltype,depth,from,to,val,gas,gasused,input,output\n"
	BaseEventtracestr = "address,topics,data\n"

	Optrace = bytes.NewBuffer(make([]byte, 16000000))
	Functrace = bytes.NewBuffer(make([]byte, 8000000))
	Eventtrace = bytes.NewBuffer(make([]byte, 8000000))

	session, err := mgo.Dial(url)

	if err != nil {
		log.Fatal(err)
	}

	logger = session

	Db = session.DB("ethereum")
}

func InitTrace(tx common.Hash) {
	Optrace.Reset()
	Functrace.Reset()
	Eventtrace.Reset()

	Optrace.WriteString(tx.String() + "\n" + BaseOptracestr)
	Functrace.WriteString(BaseFunctracestr)
	Eventtrace.WriteString(BaseEventtracestr)
}

func AddOpLog(pc uint64, depth uint64, op string, gas uint64, gasCost uint64, extra string) {
	// add opcode logs for current tx
	Optrace.WriteString(fmt.Sprintf("%d,%d,%s,%d,%d,%s\n", pc, depth, op, gas, gasCost, extra))
}

func EndOpLog(tx common.Hash) {
	txCopy := tx.String()

	if txCopy != "0x0000000000000000000000000000000000000000000000000000000000000000" {
		Optrace.WriteString(txCopy)
	}
}

func AddFuncLog(ct string, d int, from string, to string, value *big.Int, g uint64, gu uint64, input string, output string) {
	Functrace.WriteString(fmt.Sprintf("%s,%d,%s,%s,%d,%d,%d,%s,%s\n", ct, d, from, to, value, g, gu, input, output))
}

func AddEventTrace(addr string, topics string, data string) {
	Eventtrace.WriteString(fmt.Sprintf("%s, %s, %s\n", addr, topics, data))
}

func WriteEntry(block big.Int, tx common.Hash, from string, to string, value big.Int, gasPrice big.Int, gasUsed uint64, extra string) {
	trace := Collection{
		Block:      block.String(),
		Tx:         tx.String(),
		From:       from,
		To:         to,
		Value:      value.String(),
		GasPrice:   gasPrice.String(),
		GasUsed:    fmt.Sprintf("%d", gasUsed),
		Optrace:    Optrace.String(),
		Functrace:  Functrace.String(),
		Eventtrace: Eventtrace.String(),
	}

	if Optrace.String() != fmt.Sprint(tx.String()+"\n"+BaseOptracestr+tx.String()) {
		err := Db.C("traces").Insert(trace)

		if err != nil {
			log.Println(err, ". Unable to log transaction tx: ", tx)
			return
		}
	}
}

func CloseMongo() {
	defer logger.Close()
}

/* This is deprecated, works for SQL
func InitLogger() {
	err := godotenv.Load("../.env")
	if err != nil {
		log.Fatal("Failed to log godotenv")
	}

	pass := os.Getenv("DBPASS")
	conn_str := fmt.Sprintf("%s%s%s", "josh:", pass, "@tcp(127.0.0.1:3306)/blockchain")

	db, err := sql.Open("mysql", conn_str)

	if err != nil {
		log.Fatal(err)
	}

	logger = *db

	// initialize log for current tx
	trace = []Trace{}

}

func AddEntryLogs(txhash common.Hash, pc int64, depth int64, op string, gas int64, extra string) {
	// add opcode logs for current tx
	trace = append(trace, Trace{
		Pc:     pc,
		Depth:  depth,
		Opcode: op,
		Gas:    gas,
		Extra:  extra,
	})
}

func WriteEntry(block big.Int, tx string, from string, to string, value int64, gp int64, gu int64, extra string) {
	// adds extra detail to logs such as blockid, tx,...

	stmt, err := logger.Prepare("INSERT INTO traces(blockID, tx, txTo, txFrom, gasPrice, gasUsed, logs, extra) VALUES(?,?,?,?,?,?,?,?)")

	if err != nil {
		log.Println(err, ". Unable to log transaction tx: ", tx)
		trace = []Trace{}
		return
	}

	logs, _ := json.MarshalIndent(trace, "", "  ")
	sLogs := string(logs)

	defer stmt.Close()

	_, err = stmt.Exec(block.int64(), tx, from, to, gp, gu, sLogs, extra)

	if err != nil {
		log.Println(err, ". Unable to log transaction tx: ", tx)
		trace = []Trace{}
		return
	}

	// reset current log
	trace = []Trace{}
} */
