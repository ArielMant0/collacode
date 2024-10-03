BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "datasets" (
	"id"	integer,
	"name"	text NOT NULL UNIQUE,
	"description"	text,
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "games" (
	"id"	integer,
	"dataset_id"	integer NOT NULL,
	"name"	text NOT NULL UNIQUE,
	"year"	integer,
	"played"	integer NOT NULL,
	"url"	text NOT NULL,
	"teaser"	text,
	PRIMARY KEY("id"),
	CONSTRAINT "fk_dataset" FOREIGN KEY("dataset_id") REFERENCES "datasets"("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "users" (
	"id"	integer,
	"dataset_id"	integer NOT NULL,
	"name"	text NOT NULL UNIQUE,
	"role"	text NOT NULL,
	"email"	text,
	PRIMARY KEY("id"),
	CONSTRAINT "fk_dataset" FOREIGN KEY("dataset_id") REFERENCES "datasets"("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "codes" (
	"id"	integer,
	"dataset_id"	integer NOT NULL,
	"name"	text NOT NULL UNIQUE,
	"description"	text NOT NULL,
	"created"	integer NOT NULL,
	"created_by"	integer NOT NULL,
	PRIMARY KEY("id"),
	FOREIGN KEY("created_by") REFERENCES "users"("id"),
	CONSTRAINT "fk_dataset" FOREIGN KEY("dataset_id") REFERENCES "datasets"("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "datatags" (
	"id"	integer,
	"game_id"	integer NOT NULL,
	"tag_id"	integer NOT NULL,
	"code_id"	integer NOT NULL,
	"created"	integer NOT NULL,
	"created_by"	integer NOT NULL,
	PRIMARY KEY("id"),
	UNIQUE("game_id","tag_id","created_by"),
	CONSTRAINT "fk_code" FOREIGN KEY("code_id") REFERENCES "codes"("id") ON DELETE CASCADE,
	CONSTRAINT "fk_tag" FOREIGN KEY("tag_id") REFERENCES "tags"("id") ON DELETE CASCADE,
	FOREIGN KEY("created_by") REFERENCES "users"("id"),
	CONSTRAINT "fk_game" FOREIGN KEY("game_id") REFERENCES "games"("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "tags" (
	"id"	integer,
	"name"	text NOT NULL,
	"description"	text NOT NULL,
	"code_id"	integer NOT NULL,
	"created"	integer NOT NULL,
	"created_by"	integer NOT NULL,
	"parent"	integer,
	"is_leaf"	integer NOT NULL,
	PRIMARY KEY("id"),
	UNIQUE("code_id","name"),
	FOREIGN KEY("created_by") REFERENCES "users"("id"),
	CONSTRAINT "fk_code" FOREIGN KEY("code_id") REFERENCES "codes"("id") ON DELETE CASCADE,
	CONSTRAINT "fk_parent" FOREIGN KEY("parent") REFERENCES "tags"("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "tag_assignments" (
	"id"	integer,
	"old_code"	integer NOT NULL,
	"new_code"	integer NOT NULL,
	"old_tag"	integer NOT NULL,
	"new_tag"	integer,
	"description"	text,
	"created"	integer NOT NULL,
	PRIMARY KEY("id"),
	CONSTRAINT "fk_old_code" FOREIGN KEY("old_code") REFERENCES "codes"("id") ON DELETE CASCADE,
	CONSTRAINT "fk_old_tag" FOREIGN KEY("old_tag") REFERENCES "tags"("id") ON DELETE CASCADE,
	CONSTRAINT "fk_new_tag" FOREIGN KEY("new_tag") REFERENCES "tags"("id") ON DELETE CASCADE,
	CONSTRAINT "fk_new_code" FOREIGN KEY("new_code") REFERENCES "codes"("id") ON DELETE CASCADE,
	UNIQUE("old_code","new_code","old_tag","new_tag")
);
CREATE TABLE IF NOT EXISTS "memos" (
	"id"	integer,
	"description"	text NOT NULL,
	"created"	integer NOT NULL,
	"created_by"	integer NOT NULL,
	PRIMARY KEY("id"),
	FOREIGN KEY("created_by") REFERENCES "users"("id")
);
CREATE TABLE IF NOT EXISTS "memo_links" (
	"id"	integer,
	"memo_id"	integer NOT NULL,
	"link_type"	text NOT NULL,
	"link_id"	integer NOT NULL,
	"description"	text NOT NULL,
	"created"	integer NOT NULL,
	"created_by"	integer NOT NULL,
	PRIMARY KEY("id"),
	FOREIGN KEY("created_by") REFERENCES "users"("id")
);
CREATE TABLE IF NOT EXISTS "code_transitions" (
	"id"	integer,
	"old_code"	integer NOT NULL,
	"new_code"	integer NOT NULL,
	"started"	integer NOT NULL,
	"finished"	integer,
	PRIMARY KEY("id"),
	CONSTRAINT "fk_old_code" FOREIGN KEY("old_code") REFERENCES "codes"("id") ON DELETE CASCADE,
	CONSTRAINT "fk_new_code" FOREIGN KEY("new_code") REFERENCES "codes"("id") ON DELETE CASCADE,
	UNIQUE("old_code","new_code")
);
CREATE TABLE IF NOT EXISTS "evidence" (
	"id"	integer,
	"game_id"	integer NOT NULL,
	"code_id"	integer NOT NULL,
	"tag_id"	integer,
	"description"	text NOT NULL,
	"filepath"	text,
	"created"	integer NOT NULL,
	"created_by"	integer NOT NULL,
	PRIMARY KEY("id"),
	FOREIGN KEY("created_by") REFERENCES "users"("id"),
	CONSTRAINT "fk_tag" FOREIGN KEY("tag_id") REFERENCES "tags"("id") ON DELETE SET NULL,
	CONSTRAINT "fk_game" FOREIGN KEY("game_id") REFERENCES "games"("id") ON DELETE CASCADE,
	CONSTRAINT "fk_code" FOREIGN KEY("code_id") REFERENCES "codes"("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "ext_categories" (
	"id"	INTEGER NOT NULL UNIQUE,
	"parent"	INTEGER,
	"description"	TEXT NOT NULL,
	"name"	TEXT NOT NULL,
	"created"	INTEGER NOT NULL,
	"created_by"	INTEGER NOT NULL,
	"dataset"	INTEGER NOT NULL,
	"code_id"	INTEGER NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("created_by") REFERENCES "users"("id"),
	FOREIGN KEY("dataset") REFERENCES "datasets"("id"),
	FOREIGN KEY("parent") REFERENCES "ext_categories"("id")
);
CREATE TABLE IF NOT EXISTS "ext_cat_connections" (
	"id"	INTEGER NOT NULL UNIQUE,
	"ext_id"	INTEGER NOT NULL,
	"cat_id"	INTEGER NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("cat_id") REFERENCES "ext_categories"("id") ON DELETE CASCADE,
	FOREIGN KEY("ext_id") REFERENCES "externalizations"("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "ext_tag_connections" (
	"id"	INTEGER NOT NULL UNIQUE,
	"ext_id"	INTEGER NOT NULL,
	"tag_id"	INTEGER NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("ext_id") REFERENCES "externalizations"("id") ON DELETE CASCADE,
	FOREIGN KEY("tag_id") REFERENCES "tags"("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "externalizations" (
	"id"	INTEGER NOT NULL UNIQUE,
	"name"	TEXT NOT NULL,
	"description"	TEXT NOT NULL,
	"game_id"	INTEGER NOT NULL,
	"code_id"	INTEGER NOT NULL,
	"created"	INTEGER NOT NULL,
	"created_by"	INTEGER NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("game_id") REFERENCES "games"("id") ON DELETE CASCADE,
	FOREIGN KEY("code_id") REFERENCES "codes"("id") ON DELETE CASCADE,
	FOREIGN KEY("created_by") REFERENCES "users"("id") ON DELETE CASCADE
);
COMMIT;
