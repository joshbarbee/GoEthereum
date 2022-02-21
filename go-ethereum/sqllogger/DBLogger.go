package sqllogger

import (
	"encoding/json"
	"log"
	"math/big"

	"database/sql"

	"github.com/ethereum/go-ethereum/common"
	_ "github.com/go-sql-driver/mysql"
)

type Trace struct {
	Pc     uint64
	Depth  uint64
	Opcode string
	Gas    uint64
	Extra  string
}

var (
	logger sql.DB
	trace  []Trace
)

func InitLogger() {
	db, err := sql.Open("mysql", "josh:password@tcp(127.0.0.1:3306)/blockchain")

	if err != nil {
		log.Fatal(err)
	}

	logger = *db

	// initialize log for current tx
	trace = []Trace{}

}

func AddEntryLogs(txhash common.Hash, pc uint64, depth uint64, op string, gas uint64, extra string) {
	// add opcode logs for current tx
	trace = append(trace, Trace{
		Pc:     pc,
		Depth:  depth,
		Opcode: op,
		Gas:    gas,
		Extra:  extra,
	})
}

func WriteEntry(block big.Int, tx string, from string, to string, value uint64, gp uint64, gu uint64, extra string) {
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

	_, err = stmt.Exec(block.Uint64(), tx, from, to, gp, gu, sLogs, extra)

	if err != nil {
		log.Println(err, ". Unable to log transaction tx: ", tx)
		trace = []Trace{}
		return
	}

	// reset current log
	trace = []Trace{}
}
