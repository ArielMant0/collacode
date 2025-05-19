BEGIN TRANSACTION;
DROP TABLE IF EXISTS "code_transitions";
CREATE TABLE "code_transitions" (
	"id"	integer,
	"old_code"	integer NOT NULL,
	"new_code"	integer NOT NULL,
	"started"	integer NOT NULL,
	"finished"	integer,
	PRIMARY KEY("id"),
	UNIQUE("old_code","new_code"),
	CONSTRAINT "fk_new_code" FOREIGN KEY("new_code") REFERENCES "codes"("id") ON DELETE CASCADE,
	CONSTRAINT "fk_old_code" FOREIGN KEY("old_code") REFERENCES "codes"("id") ON DELETE CASCADE
);
DROP TABLE IF EXISTS "codes";
CREATE TABLE "codes" (
	"id"	INTEGER,
	"dataset_id"	INTEGER NOT NULL,
	"name"	TEXT NOT NULL,
	"description"	TEXT NOT NULL,
	"created"	INTEGER NOT NULL,
	"created_by"	INTEGER NOT NULL,
	PRIMARY KEY("id"),
	CONSTRAINT "uc_combi" UNIQUE("name","dataset_id"),
	FOREIGN KEY("created_by") REFERENCES "users"("id"),
	FOREIGN KEY("dataset_id") REFERENCES "datasets"("id") ON DELETE CASCADE
);
DROP TABLE IF EXISTS "datasets";
CREATE TABLE "datasets" (
	"id"	INTEGER,
	"name"	TEXT NOT NULL UNIQUE,
	"item_name"	TEXT NOT NULL,
	"meta_item_name"	TEXT,
	"meta_table"	TEXT,
	"description"	TEXT,
	"schema"	BLOB,
	PRIMARY KEY("id")
);
DROP TABLE IF EXISTS "datatags";
CREATE TABLE "datatags" (
	"id"	INTEGER,
	"item_id"	INTEGER NOT NULL,
	"tag_id"	INTEGER NOT NULL,
	"code_id"	INTEGER NOT NULL,
	"created"	INTEGER NOT NULL,
	"created_by"	INTEGER NOT NULL,
	PRIMARY KEY("id"),
	UNIQUE("item_id","tag_id","created_by"),
	FOREIGN KEY("code_id") REFERENCES "codes"("id") ON DELETE CASCADE,
	FOREIGN KEY("created_by") REFERENCES "users"("id") ON DELETE CASCADE,
	FOREIGN KEY("item_id") REFERENCES "items"("id") ON DELETE CASCADE,
	FOREIGN KEY("tag_id") REFERENCES "tags"("id") ON DELETE CASCADE
);
DROP TABLE IF EXISTS "evidence";
CREATE TABLE "evidence" (
	"id"	INTEGER,
	"item_id"	INTEGER NOT NULL,
	"code_id"	INTEGER NOT NULL,
	"tag_id"	INTEGER,
	"description"	TEXT NOT NULL,
	"filepath"	TEXT,
	"created"	INTEGER NOT NULL,
	"created_by"	INTEGER NOT NULL,
	PRIMARY KEY("id"),
	FOREIGN KEY("code_id") REFERENCES "codes"("id") ON DELETE CASCADE,
	FOREIGN KEY("created_by") REFERENCES "users"("id") ON DELETE CASCADE,
	FOREIGN KEY("item_id") REFERENCES "items"("id") ON DELETE CASCADE,
	FOREIGN KEY("tag_id") REFERENCES "tags"("id") ON DELETE SET NULL
);
DROP TABLE IF EXISTS "expertise";
CREATE TABLE "expertise" (
	"id"	INTEGER NOT NULL UNIQUE,
	"item_id"	INTEGER NOT NULL,
	"user_id"	INTEGER NOT NULL,
	"value"	INTEGER NOT NULL DEFAULT 0,
	PRIMARY KEY("id" AUTOINCREMENT) ON CONFLICT REPLACE,
	FOREIGN KEY("item_id") REFERENCES "items"("id") ON DELETE CASCADE,
	FOREIGN KEY("user_id") REFERENCES "users"("id") ON DELETE CASCADE
);
DROP TABLE IF EXISTS "game_scores";
CREATE TABLE "game_scores" (
	"id"	INTEGER,
	"user_id"	INTEGER NOT NULL,
	"code_id"	INTEGER NOT NULL,
	"game_id"	INTEGER NOT NULL,
	"difficulty"	INTEGER NOT NULL,
	"played"	INTEGER NOT NULL,
	"wins"	INTEGER NOT NULL,
	"streak_current"	INTEGER DEFAULT 0,
	"streak_highest"	INTEGER DEFAULT 0,
	UNIQUE("game_id","difficulty","user_id","code_id"),
	PRIMARY KEY("id"),
	FOREIGN KEY("code_id") REFERENCES "codes"("id") ON DELETE CASCADE,
	FOREIGN KEY("user_id") REFERENCES "users"("id") ON DELETE CASCADE
);
DROP TABLE IF EXISTS "game_scores_items";
CREATE TABLE "game_scores_items" (
	"id"	INTEGER,
	"user_id"	INTEGER NOT NULL,
	"code_id"	INTEGER NOT NULL,
	"item_id"	INTEGER NOT NULL,
	"game_id"	INTEGER NOT NULL,
	"difficulty"	INTEGER NOT NULL,
	"win"	INTEGER NOT NULL,
	"created"	INTEGER NOT NULL,
	PRIMARY KEY("id"),
	FOREIGN KEY("code_id") REFERENCES "codes"("id") ON DELETE CASCADE,
	FOREIGN KEY("item_id") REFERENCES "items"("id") ON DELETE CASCADE,
	FOREIGN KEY("user_id") REFERENCES "users"("id") ON DELETE CASCADE
);
DROP TABLE IF EXISTS "game_scores_tags";
CREATE TABLE "game_scores_tags" (
	"id"	INTEGER,
	"user_id"	INTEGER NOT NULL,
	"code_id"	INTEGER NOT NULL,
	"tag_id"	INTEGER NOT NULL,
	"item_id"	INTEGER NOT NULL,
	"game_id"	INTEGER NOT NULL,
	"difficulty"	INTEGER NOT NULL,
	"win"	INTEGER NOT NULL,
	"created"	INTEGER NOT NULL,
	PRIMARY KEY("id"),
	FOREIGN KEY("code_id") REFERENCES "codes"("id") ON DELETE CASCADE,
	FOREIGN KEY("item_id") REFERENCES "tags"("id") ON DELETE CASCADE,
	FOREIGN KEY("item_id") REFERENCES "items"("id") ON DELETE CASCADE,
	FOREIGN KEY("user_id") REFERENCES "users"("id") ON DELETE CASCADE
);
DROP TABLE IF EXISTS "items";
CREATE TABLE "items" (
	"id"	INTEGER,
	"dataset_id"	INTEGER NOT NULL,
	"name"	TEXT NOT NULL,
	"description"	TEXT,
	"url"	TEXT,
	"teaser"	TEXT,
	PRIMARY KEY("id"),
	FOREIGN KEY("dataset_id") REFERENCES "datasets"("id") ON DELETE CASCADE
);
DROP TABLE IF EXISTS "logs";
CREATE TABLE "logs" (
	"id"	INTEGER NOT NULL UNIQUE,
	"user_id"	INTEGER,
	"timestamp"	INTEGER NOT NULL,
	"action"	TEXT NOT NULL,
	"data"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("user_id") REFERENCES "users"("id") ON DELETE SET NULL
);
DROP TABLE IF EXISTS "memo_links";
CREATE TABLE "memo_links" (
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
DROP TABLE IF EXISTS "memos";
CREATE TABLE "memos" (
	"id"	integer,
	"description"	text NOT NULL,
	"created"	integer NOT NULL,
	"created_by"	integer NOT NULL,
	PRIMARY KEY("id"),
	FOREIGN KEY("created_by") REFERENCES "users"("id")
);
DROP TABLE IF EXISTS "meta_agreements";
CREATE TABLE "meta_agreements" (
	"id"	INTEGER,
	"meta_id"	INTEGER NOT NULL,
	"created_by"	INTEGER NOT NULL,
	"value"	INTEGER NOT NULL,
	PRIMARY KEY("id"),
	FOREIGN KEY("created_by") REFERENCES "users"("id") ON DELETE CASCADE,
	FOREIGN KEY("meta_id") REFERENCES "meta_items"("id") ON DELETE CASCADE
);
DROP TABLE IF EXISTS "meta_cat_connections";
CREATE TABLE "meta_cat_connections" (
	"id"	INTEGER,
	"meta_id"	INTEGER NOT NULL,
	"cat_id"	INTEGER NOT NULL,
	PRIMARY KEY("id"),
	FOREIGN KEY("cat_id") REFERENCES "meta_categories"("id") ON DELETE CASCADE,
	FOREIGN KEY("meta_id") REFERENCES "meta_items"("id") ON DELETE CASCADE
);
DROP TABLE IF EXISTS "meta_categories";
CREATE TABLE "meta_categories" (
	"id"	INTEGER,
	"parent"	INTEGER,
	"description"	TEXT NOT NULL,
	"name"	TEXT NOT NULL,
	"created"	INTEGER NOT NULL,
	"created_by"	INTEGER NOT NULL,
	"dataset_id"	INTEGER NOT NULL,
	"code_id"	INTEGER NOT NULL,
	PRIMARY KEY("id"),
	FOREIGN KEY("created_by") REFERENCES "users"("id") ON DELETE CASCADE,
	FOREIGN KEY("dataset_id") REFERENCES "datasets"("id") ON DELETE CASCADE,
	FOREIGN KEY("parent") REFERENCES "meta_categories"("id") ON DELETE SET NULL
);
DROP TABLE IF EXISTS "meta_ev_connections";
CREATE TABLE "meta_ev_connections" (
	"id"	INTEGER,
	"meta_id"	INTEGER NOT NULL,
	"ev_id"	INTEGER NOT NULL,
	PRIMARY KEY("id"),
	FOREIGN KEY("ev_id") REFERENCES "evidence"("id") ON DELETE CASCADE,
	FOREIGN KEY("meta_id") REFERENCES "meta_items"("id") ON DELETE CASCADE
);
DROP TABLE IF EXISTS "meta_groups";
CREATE TABLE "meta_groups" (
	"id"	INTEGER,
	"name"	TEXT NOT NULL,
	"item_id"	INTEGER NOT NULL,
	"code_id"	INTEGER NOT NULL,
	"created"	INTEGER NOT NULL,
	"created_by"	INTEGER NOT NULL,
	PRIMARY KEY("id"),
	FOREIGN KEY("code_id") REFERENCES "codes"("id") ON DELETE CASCADE,
	FOREIGN KEY("created_by") REFERENCES "users"("id") ON DELETE CASCADE,
	FOREIGN KEY("item_id") REFERENCES "items"("id") ON DELETE CASCADE
);
DROP TABLE IF EXISTS "meta_items";
CREATE TABLE "meta_items" (
	"id"	INTEGER,
	"group_id"	INTEGER NOT NULL,
	"name"	TEXT NOT NULL,
	"cluster"	TEXT NOT NULL DEFAULT misc,
	"description"	TEXT NOT NULL,
	"created"	INTEGER NOT NULL,
	"created_by"	INTEGER NOT NULL,
	PRIMARY KEY("id"),
	FOREIGN KEY("created_by") REFERENCES "users"("id") ON DELETE CASCADE,
	FOREIGN KEY("group_id") REFERENCES "meta_groups"("id") ON DELETE CASCADE
);
DROP TABLE IF EXISTS "meta_tag_connections";
CREATE TABLE "meta_tag_connections" (
	"id"	INTEGER,
	"meta_id"	INTEGER NOT NULL,
	"tag_id"	INTEGER NOT NULL,
	PRIMARY KEY("id"),
	FOREIGN KEY("meta_id") REFERENCES "meta_items"("id") ON DELETE CASCADE,
	FOREIGN KEY("tag_id") REFERENCES "tags"("id") ON DELETE CASCADE
);
DROP TABLE IF EXISTS "migration_version";
CREATE TABLE "migration_version" (
	"version"	text
);
DROP TABLE IF EXISTS "objections";
CREATE TABLE "objections" (
	"id"	INTEGER,
	"user_id"	INTEGER NOT NULL,
	"code_id"	INTEGER NOT NULL,
	"item_id"	INTEGER DEFAULT NULL,
	"tag_id"	INTEGER DEFAULT NULL,
	"action"	INTEGER NOT NULL,
	"status"	INTEGER DEFAULT 1,
	"explanation"	TEXT NOT NULL,
	"resolution"	TEXT DEFAULT NULL,
	"created"	INTEGER NOT NULL,
	PRIMARY KEY("id"),
	FOREIGN KEY("code_id") REFERENCES "codes"("id") ON DELETE CASCADE,
	FOREIGN KEY("item_id") REFERENCES "items"("id") ON DELETE CASCADE,
	FOREIGN KEY("tag_id") REFERENCES "tags"("id") ON DELETE CASCADE,
	FOREIGN KEY("user_id") REFERENCES "users"("id") ON DELETE CASCADE
);
DROP TABLE IF EXISTS "project_users";
CREATE TABLE "project_users" (
	"id"	INTEGER,
	"user_id"	INTEGER NOT NULL,
	"dataset_id"	INTEGER NOT NULL,
	PRIMARY KEY("id"),
	UNIQUE("user_id","dataset_id"),
	FOREIGN KEY("dataset_id") REFERENCES "datasets"("id") ON DELETE CASCADE,
	FOREIGN KEY("user_id") REFERENCES "users"("id") ON DELETE CASCADE
);
DROP TABLE IF EXISTS "tag_assignments";
CREATE TABLE "tag_assignments" (
	"id"	integer,
	"old_code"	integer NOT NULL,
	"new_code"	integer NOT NULL,
	"old_tag"	integer NOT NULL,
	"new_tag"	integer NOT NULL,
	"description"	text,
	"created"	integer NOT NULL,
	PRIMARY KEY("id"),
	UNIQUE("old_code","new_code","old_tag","new_tag"),
	CONSTRAINT "fk_new_code" FOREIGN KEY("new_code") REFERENCES "codes"("id") ON DELETE CASCADE,
	CONSTRAINT "fk_new_tag" FOREIGN KEY("new_tag") REFERENCES "tags"("id") ON DELETE SET NULL,
	CONSTRAINT "fk_old_code" FOREIGN KEY("old_code") REFERENCES "codes"("id") ON DELETE CASCADE,
	CONSTRAINT "fk_old_tag" FOREIGN KEY("old_tag") REFERENCES "tags"("id") ON DELETE SET NULL
);
DROP TABLE IF EXISTS "tags";
CREATE TABLE "tags" (
	"id"	integer,
	"name"	text NOT NULL,
	"description"	text NOT NULL,
	"code_id"	integer NOT NULL,
	"created"	integer NOT NULL,
	"created_by"	integer NOT NULL,
	"parent"	integer,
	"is_leaf"	integer NOT NULL,
	UNIQUE("code_id","name"),
	PRIMARY KEY("id"),
	CONSTRAINT "fk_code" FOREIGN KEY("code_id") REFERENCES "codes"("id") ON DELETE CASCADE,
	FOREIGN KEY("created_by") REFERENCES "users"("id"),
	CONSTRAINT "fk_parent" FOREIGN KEY("parent") REFERENCES "tags"("id") ON DELETE CASCADE
);
DROP TABLE IF EXISTS "update_times";
CREATE TABLE "update_times" (
	"id"	INTEGER,
	"name"	TEXT NOT NULL,
	"dataset_id"	INTEGER NOT NULL,
	"timestamp"	INTEGER NOT NULL,
	PRIMARY KEY("id"),
	CONSTRAINT "uc_combi" UNIQUE("name","dataset_id"),
	FOREIGN KEY("dataset_id") REFERENCES "datasets"("id") ON DELETE CASCADE
);
DROP TABLE IF EXISTS "users";
CREATE TABLE "users" (
	"id"	INTEGER,
	"login_id"	TEXT,
	"name"	TEXT NOT NULL UNIQUE,
	"pw_hash"	TEXT NOT NULL,
	"role"	TEXT NOT NULL,
	"email"	TEXT,
	PRIMARY KEY("id")
);
COMMIT;
