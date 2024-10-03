BEGIN TRANSACTION;
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
INSERT INTO "ext_categories" VALUES (1,NULL,'Why does the player externalize?','why',1727718051683,1,1,3);
INSERT INTO "ext_categories" VALUES (2,NULL,'How do players externalize? Relates to mechanics and visual encodings','how',1727767494858,1,1,3);
INSERT INTO "ext_categories" VALUES (3,NULL,'For how long do player''s externalizations persist?','how long',1727767567776,1,1,3);
INSERT INTO "ext_categories" VALUES (4,NULL,'What do player''s externalize?','what',1727767716377,1,1,3);
INSERT INTO "ext_categories" VALUES (5,3,'externalizations are fleeting, available only in the moment','transient',1727767760797,1,1,3);
INSERT INTO "ext_categories" VALUES (6,3,'externalizations persist for a long duration, e.g. the whole game session or beyond','persistent',1727767866285,1,1,3);
INSERT INTO "ext_categories" VALUES (7,3,'externalizations are related to a player action, e.g. they live until some action is taken, which may not relate directly to the externalization itself','action-based',1727767959256,1,1,3);
INSERT INTO "ext_categories" VALUES (8,1,'player externalize during sensemaking to support sensemaking','sensemaking',1727768039630,1,1,3);
INSERT INTO "ext_categories" VALUES (9,1,'players externalize to create a history they can reference in the future, e.g. to plan','provenance',1727768039630,1,1,3);
INSERT INTO "ext_categories" VALUES (10,1,'players externalize to communicate with other players','communication',1727768171738,1,1,3);
INSERT INTO "ext_categories" VALUES (11,1,'players externalize for fun, i.e. it does not have an explicit use','fun',1727768171738,1,1,3);
INSERT INTO "ext_categories" VALUES (12,2,'describes the mechanics (e.g. interactions) used to externalize','mechanics',1727768314667,1,1,3);
INSERT INTO "ext_categories" VALUES (13,2,'how the externalization is encoded (likely visually)','encoding',1727768416553,1,1,3);
INSERT INTO "ext_categories" VALUES (14,4,'players externalize intent (usually for communication)','intent',1727768488279,1,1,3);
INSERT INTO "ext_categories" VALUES (15,4,'externalizations concern descriptive information, they do not contain intent or a call to action','descriptive information',1727768563938,1,1,3);
INSERT INTO "ext_categories" VALUES (16,13,'externalizations are encoded as text','text',1727771444716,1,1,3);
INSERT INTO "ext_categories" VALUES (17,13,'externalization is encoded symbolically (e.g. icons or small drawings)','symbol',1727771524463,1,1,3);
INSERT INTO "ext_categories" VALUES (18,13,'externalization is encoded though a (tangible) object in the game world','object',1727771524463,1,1,3);
INSERT INTO "ext_categories" VALUES (19,13,'externalizations are encoded as visualized data (e.g. a value, relation, etc.)','visualization',1727771764191,1,1,3);
INSERT INTO "ext_categories" VALUES (20,12,'players enact the externalization, e.g by connecting items via dragging','enact',1727771861549,1,1,3);
INSERT INTO "ext_categories" VALUES (21,12,'externalization is created from interacting with a related object (e.g. pinging an item in DotA)','object-related',1727771977160,1,1,3);
INSERT INTO "ext_categories" VALUES (22,12,'externalizations are created freely without reference, e.g. by typing','free',1727772146545,1,1,3);
INSERT INTO "ext_cat_connections" VALUES (20,2,18);
INSERT INTO "ext_cat_connections" VALUES (21,2,21);
INSERT INTO "ext_cat_connections" VALUES (22,2,9);
INSERT INTO "ext_cat_connections" VALUES (23,2,7);
INSERT INTO "ext_cat_connections" VALUES (24,2,15);
INSERT INTO "ext_cat_connections" VALUES (25,3,19);
INSERT INTO "ext_cat_connections" VALUES (26,3,20);
INSERT INTO "ext_cat_connections" VALUES (27,3,21);
INSERT INTO "ext_cat_connections" VALUES (28,3,18);
INSERT INTO "ext_cat_connections" VALUES (29,3,8);
INSERT INTO "ext_cat_connections" VALUES (30,3,6);
INSERT INTO "ext_cat_connections" VALUES (31,3,15);
INSERT INTO "ext_cat_connections" VALUES (32,4,18);
INSERT INTO "ext_cat_connections" VALUES (33,4,16);
INSERT INTO "ext_cat_connections" VALUES (34,4,21);
INSERT INTO "ext_cat_connections" VALUES (35,4,22);
INSERT INTO "ext_cat_connections" VALUES (36,4,8);
INSERT INTO "ext_cat_connections" VALUES (37,4,9);
INSERT INTO "ext_cat_connections" VALUES (38,4,6);
INSERT INTO "ext_cat_connections" VALUES (39,4,15);
INSERT INTO "ext_cat_connections" VALUES (40,4,14);
INSERT INTO "ext_cat_connections" VALUES (62,1,16);
INSERT INTO "ext_cat_connections" VALUES (63,1,22);
INSERT INTO "ext_cat_connections" VALUES (64,1,8);
INSERT INTO "ext_cat_connections" VALUES (65,1,9);
INSERT INTO "ext_cat_connections" VALUES (66,1,6);
INSERT INTO "ext_cat_connections" VALUES (67,1,14);
INSERT INTO "ext_cat_connections" VALUES (68,1,15);
INSERT INTO "ext_tag_connections" VALUES (5,2,421);
INSERT INTO "ext_tag_connections" VALUES (6,2,422);
INSERT INTO "ext_tag_connections" VALUES (7,3,419);
INSERT INTO "ext_tag_connections" VALUES (8,4,422);
INSERT INTO "ext_tag_connections" VALUES (12,1,423);
INSERT INTO "externalizations" VALUES (1,'tagging system','players can tag video clips for various purposes, e.g. to group clips thematically, mark them for the future or reference the clip''s content',1,3,1727790339936,1);
INSERT INTO "externalizations" VALUES (2,'session','players can save a limited number of video clips in a session, which is always visible on the screen',1,3,1727798635822,1);
COMMIT;
