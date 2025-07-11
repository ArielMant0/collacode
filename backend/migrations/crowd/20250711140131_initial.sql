BEGIN TRANSACTION;
DROP TABLE IF EXISTS "item_sim_counts";
CREATE TABLE "item_sim_counts" (
	"id"	INTEGER NOT NULL UNIQUE,
	"dataset_id"	INTEGER NOT NULL CHECK("dataset_id" > 0),
	"target_id"	INTEGER NOT NULL CHECK("target_id" > 0),
	"item_id"	INTEGER NOT NULL CHECK("item_id" > 0),
	"count"	INTEGER NOT NULL,
	"last_update"	INTEGER NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	UNIQUE("item_id","target_id")
);
DROP TABLE IF EXISTS "item_sims";
CREATE TABLE "item_sims" (
	"id"	INTEGER NOT NULL UNIQUE,
	"dataset_id"	INTEGER NOT NULL CHECK("dataset_id" > 0),
	"target_id"	INTEGER NOT NULL CHECK("target_id" > 0),
	"item_id"	INTEGER NOT NULL CHECK("item_id" > 0),
	"guid"	TEXT NOT NULL,
	"game_id"	INTEGER NOT NULL,
	"value"	INTEGER NOT NULL,
	"timestamp"	INTEGER NOT NULL,
	"data"	BLOB,
	PRIMARY KEY("id" AUTOINCREMENT),
	UNIQUE("target_id","item_id","guid","game_id")
);
COMMIT;
