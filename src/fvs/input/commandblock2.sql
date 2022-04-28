---
--- Creating and Populate the FVS_STANDINIT_PLOT_FT table
---
CREATE TABLE FVS_STANDINIT_PLOT_FT (
    STAND_ID VARCHAR (26),
    VARIANT VARCHAR (11),
    INV_YEAR FLOAT,
    --- The [...] are to delimit the inside incase you wanted spaces or smthg
    --- it's not really necessary
    --- see: https://stackoverflow.com/questions/9917196/meaning-of-square-brackets-in-ms-sql-table-designer
    [GROUPS] VARCHAR (200),
    ADDFILES VARCHAR (200),
    FVSKEYWORDS VARCHAR (200),
    REGION FLOAT,
    FOREST FLOAT,
    LOCATION FLOAT,
    AGE FLOAT,
    BASAL_AREA_FACTOR FLOAT,
    INV_PLOT_SIZE FLOAT,
    BRK_DBH FLOAT,
    NUM_PLOTS FLOAT,
    SAM_WT FLOAT,
    DG_TRANS FLOAT,
    DG_MEASURE FLOAT,
    SITE_SPECIES VARCHAR (8),
    SITE_INDEX FLOAT,
    STATE FLOAT --- No comma at the end !!!
);

--- Populate ID
INSERT INTO
    FVS_STANDINIT_PLOT_FT (STAND_ID)
SELECT
    DISTINCT STAND_ID
FROM
    FVS_PLOTINIT_PLOT;

--- Remove '/' character ("n/a" => "na")
UPDATE
    FVS_STANDINIT_PLOT_FT
SET
    STAND_ID = REPLACE(STAND_ID, '/', '') -- Could just be "na"
WHERE
    STAND_ID = "n/a";



-- AVG_AGE has 58 rows ???  => 105, 800 are added ???
-- This is because it's cominf from STANDINIT while the IDs came from PLOTINIT

--- Set Average Ages
CREATE VIEW IF NOT EXISTS AVG_AGE AS
SELECT
    STAND_ID,
    ROUND(AVG(AGE)) AS AVERAGE_AGE
FROM
    FVS_STANDINIT_PLOT
GROUP BY
    STAND_ID;

UPDATE
    FVS_STANDINIT_PLOT_FT
SET
    AGE = (
        SELECT
            AVERAGE_AGE
        FROM
            AVG_AGE
        WHERE
            AVG_AGE.STAND_ID = FVS_STANDINIT_PLOT_FT.STAND_ID
    );


--- Site Species
-- Step 1: Get info from STANDINIT
CREATE VIEW STANDINIT_CORES_BY_FT AS
SELECT
    STAND_ID,
    SITE_SPECIES,
    SITE_INDEX,
    COUNT(SITE_SPECIES) AS NUM_CORINGS,
    AVG(SITE_INDEX) AS AVG_SI
FROM
    FVS_STANDINIT_PLOT
WHERE
    SITE_SPECIES > 1
GROUP BY
    STAND_ID,
    SITE_SPECIES
ORDER BY
    STAND_ID,
    -NUM_CORINGS;


-- This only has 48 distinct stand_ids ??
CREATE VIEW STANDINIT_MAX_CORES_PER_FT_WITH_TIES AS
SELECT
    ALL_FT.*
FROM
    STANDINIT_CORES_BY_FT AS ALL_FT
    INNER JOIN (
        SELECT
            STAND_ID,
            MAX(NUM_CORINGS) AS MAX_CORINGS
        FROM
            STANDINIT_CORES_BY_FT
        GROUP BY
            STAND_ID
    ) AS MAX_PER_FT ON ALL_FT.STAND_ID = MAX_PER_FT.STAND_ID
    AND ALL_FT.NUM_CORINGS = MAX_PER_FT.MAX_CORINGS;


-- Tree View (used for tie breaks)

-- Count number of species per stand
CREATE VIEW TREEINIT_SPECIES_BY_FT AS
SELECT TREEINIT.STAND_ID, 
	TREEINIT.SPECIES AS SITE_SPECIES, 
	COUNT(TREEINIT.SPECIES) AS NUM_SPECIES 
FROM FVS_TREEINIT_PLOT AS TREEINIT
GROUP BY TREEINIT.STAND_ID, 
	TREEINIT.SPECIES;

-- Generate table of target num_species ( only has 47 rows though :(, 46 if distinct stand_id )
CREATE VIEW TREEINIT_MAX_SPECIES_PER_FT AS
SELECT STAND_ID, MAX(NUM_SPECIES) AS MAX_NUM_SPECIES
FROM TREEINIT_SPECIES_BY_FT INNER JOIN
	STANDINIT_MAX_CORES_PER_FT_WITH_TIES
USING (STAND_ID, SITE_SPECIES)
GROUP BY STAND_ID;


-- Huh so we do end up with 49 rows in the end, I wonder which table that's coming from 
-- Something is wrong right now, there are certain stands getting null SITE_SPECIES values :(

-- These two really can be turned into a natural join but izzz ok for now

CREATE VIEW STANDINIT_MAX_WITH_NUM_SPECIES AS
SELECT STAND_MAX.STAND_ID, STAND_MAX.SITE_SPECIES, TREE_SPECIES.NUM_SPECIES
FROM STANDINIT_MAX_CORES_PER_FT_WITH_TIES AS STAND_MAX
	INNER JOIN TREEINIT_SPECIES_BY_FT AS TREE_SPECIES
ON STAND_MAX.STAND_ID = TREE_SPECIES.STAND_ID AND
	STAND_MAX.SITE_SPECIES = TREE_SPECIES.SITE_SPECIES;


CREATE VIEW STANDINIT_STAND_ID_SITE_SPECIES AS 
SELECT S.STAND_ID, S.SITE_SPECIES, S.NUM_SPECIES
FROM STANDINIT_MAX_WITH_NUM_SPECIES AS S
	INNER JOIN TREEINIT_MAX_SPECIES_PER_FT AS T
ON
	S.STAND_ID = T.STAND_ID 
	AND S.NUM_SPECIES = T.MAX_NUM_SPECIES;

UPDATE FVS_STANDINIT_PLOT_FT
SET SITE_SPECIES = 
   (SELECT SITE_SPECIES 
	FROM STANDINIT_STAND_ID_SITE_SPECIES
	WHERE FVS_STANDINIT_PLOT_FT.STAND_ID = STANDINIT_STAND_ID_SITE_SPECIES.STAND_ID);

-- TODO: Figure out where the 9 rows are being filtered down from, 
--	for now though I just cut out with
-- DELETE FROM FVS_STANDINIT_PLOT_FT
-- WHERE SITE_SPECIES IS NULL;

-- I have NULL values for Stand_IDs
-- STAND_ID	AGE		SITE_SPECIES
-- "381"	"41.0"		NULL
-- "406"	"90.0"		NULL
-- "501"	"-54.0"		NULL
-- "509"	"45.0"		NULL
-- "514"	"2.0"		NULL
-- "703"	"5.0"		NULL
-- "902"	"19.0"		NULL
-- "995"	"29.0"		NULL
-- "na"		NULL		NULL
--
-- (9 rows)




-- 
-- 









