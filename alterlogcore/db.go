package alterlogcore

import "database/sql"
	_ "modernc.org/sqlite"

/* Handles opening the db and executing queries */

func createDBConn() {
	db, err := sql.Open("sqlite", "./alterlog.db")
	if err != nil {
		return nil, err
	}
	return db, nil
}

