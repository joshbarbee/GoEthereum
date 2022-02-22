package sqllogger

import (
	"log"
	"math/big"
	"os"

	"context"

	"github.com/ethereum/go-ethereum/common"
	"github.com/globalsign/mgo"
	"github.com/joho/godotenv"
)

type Collection struct {
	Block    int64
	Tx       string
	From     string
	To       string
	Value    int64
	GasPrice int64
	GasUsed  int64
	Logs     []Trace
}

type Trace struct {
	Pc     int64
	Depth  int64
	Opcode string
	Gas    int64
	Extra  string
}

var (
	logger *mgo.Session
	trace  []Trace
	db     *mgo.Database
	ctx    context.Context
	cancel func()
)

func InitLogger() {
	err := godotenv.Load("../.env")
	if err != nil {
		log.Fatal("Failed to log godotenv")
	}

	_ = os.Getenv("DBPASS")

	url := "mongodb://127.0.0.1:27017"

	// initialize log for current tx
	trace = []Trace{}

	session, err := mgo.Dial(url)

	if err != nil {
		log.Fatal(err)
	}

	logger = session

	db = session.DB("ethereum")
}

func AddEntryLogs(txhash common.Hash, pc uint64, depth uint64, op string, gas uint64, extra string) {
	// add opcode logs for current tx
	trace = append(trace, Trace{
		Pc:     int64(pc),
		Depth:  int64(depth),
		Opcode: op,
		Gas:    int64(gas),
		Extra:  extra,
	})
}

func WriteEntry(block big.Int, tx string, from string, to string, value uint64, gp uint64, gu uint64, extra string) {
	// adds extra detail to logs such as blockid, tx,...

	collection := Collection{
		Block:    block.Int64(),
		Tx:       tx,
		From:     from,
		To:       to,
		Value:    int64(value),
		GasUsed:  int64(gu),
		GasPrice: int64(gp),
		Logs:     trace,
	}

	err := db.C("traces").Insert(collection)
	if err != nil {
		log.Println(err, ". Unable to log transaction tx: ", tx)
		trace = []Trace{}
		return
	}

	// reset current log
	trace = []Trace{}
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
