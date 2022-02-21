USE blockchain;
DROP TABLE IF EXISTS traces;

CREATE TABLE traces (
    id int AUTO_INCREMENT,
    blockID bigint,
    tx varchar(66),
    txFrom varchar(66),
    txTo varchar(66),
    gasPrice bigint,
    gasUsed bigint,
    logs json,
    extra longtext,
    created date,
    PRIMARY KEY (id)
)