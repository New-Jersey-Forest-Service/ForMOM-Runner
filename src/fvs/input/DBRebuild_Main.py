'''
DBRebuild Main

This program takes a raw FIA database and makes it compatabile with FVS.

Michael Gorbunov (Automated manual process by Lauren)
Lauren Gazerwitz (Figured out how to make FVS accept the datatbase)

NJDEP
04/2022
'''

# TODO:
# [ ] Handle Malformed DB
#  - Check that all tables needed are found
#  - Never index into elements without checking their length
# [ ] Cleaner SQL
#  - Run everything through an auto-formatter
# [x] Better Feedback
#  - Debug progress of queries to console

import sqlite3
import re
import sys
import DBRebuild_StandID as dbStandID


# User Specified Constants
DB_FILEPATH = './FIADB_NJ.db'
DB_NAME = 'FIADB_NJ.db'
INV_YEARS = [2015, 2016, 2017, 2018, 2019, 2020]

# Programmer Specified Comments
DEFAULT_DB_REGEX = r'FS_FIADB_STATECD_\d{2,2}\.db'
# Convert to a string for easier formatting
INV_YEARS = [str(x) for x in INV_YEARS]


def main():
	global DB_FILEPATH

	db_con = sqlite3.connect(DB_FILEPATH)
	cur = db_con.cursor()

	print(" [[ STARTING ]] ")

	print()
	print("Deleting tables")
	delete_extra_tables(cur)

	print()
	print("Creating tables with specific inventory years")
	create_inventory_year_tables(cur)

	print()
	print("Updating groupaddfilesandkeywords")
	update_groupaddfilesandkeywords(cur)

	print()
	print("Doing ID Replace")
	dbStandID.do_id_replace(cur)

	print()
	print("Running command block 2")
	run_script(cur, './commandblock2.sql')

	print()
	print(" [[ FINISHED ]] ")

	db_con.commit()
	db_con.close()


def run_script(cur: sqlite3.Cursor, path: str) -> None:
	with open(path, 'r') as f:
		cur.executescript(f.read())



#
# Steps 1 -3
# 
# Deleting Tables, Creating Tables, Editing groupaddfilesandkeywords
#

def delete_extra_tables(cur: sqlite3.Cursor) -> None:
	'''
		Deletes all tables except for a couple specified ones.
		It will also terminate the program if a specified table is not found.
	'''
	TABLES_TO_KEEP = [
		'COND', 
		'COUNTY', 
		'FVS_GROUPADDFILESANDKEYWORDS',
		'FVS_PLOTINIT_PLOT',
		'FVS_STANDINIT_PLOT',
		'FVS_TREEINIT_PLOT',
		'PLOT',
		'POP_STRATUM',
		'REF_FOREST_TYPE',
		'REF_FOREST_TYPE_GROUP',
		'REF_SPECIES',
		'SEEDLING',
		'TREE'
	]

	sql_gettables = "SELECT name FROM sqlite_master WHERE type='table'"
	cur.execute(sql_gettables)
	all_tables = [str(x[0]) for x in cur.fetchall()]

	for table in all_tables:
		if table in TABLES_TO_KEEP:
			print(f' > Keep: {table}')

		else:
			print(f' > Remove: {table}')
			cur.execute(f"DROP TABLE {table}")




def create_inventory_year_tables(cur: sqlite3.Cursor) -> None:
	got_to_end = False

	with open('./commandblock1.sql', 'r') as f:
		entire_script = f.read()
		entire_script = entire_script.replace(
			"$$INVENTORY_YEARS$$", 
			", ".join(INV_YEARS)
		)
		cur.executescript(entire_script)
		got_to_end = True
	
	if not got_to_end:
		err_and_exit("Unable to create inventory year tables")

	print(f" > Succesfully created tables for years {', '.join(INV_YEARS)}")
	


def update_groupaddfilesandkeywords(cur: sqlite3.Cursor) -> None:
	TABLE_NAME = 'FVS_GROUPADDFILESANDKEYWORDS'
	DEFAULT_DBNAME = 'FS_FIADB_STATECD_34.db' # TODO: Pull this from the data (I think 34 is NJ's number)

	# Rename All_FIA_Plots to All_FIA_ForestTypes
	cur.execute(f'''
		UPDATE {TABLE_NAME}
		SET GROUPS = 'All_FIA_ForestTypes' WHERE GROUPS = 'All_FIA_Plots'
		''')

	# Now we have three rows, named 'All_FIA_Conditions', 'All_FIA_ForestTypes', and 'All_FIA_Subplots'
	# There's a column 'FVSKEYWORDS' that is basically a script and it needs some updating
	groups = ['All_FIA_Conditions', 'All_FIA_ForestTypes', 'All_FIA_Subplots']

	for group in groups:
		cur.execute(f'''
			SELECT FVSKEYWORDS FROM {TABLE_NAME} 
			WHERE GROUPS = '{group}'
			''')
		fvskeywords = str(cur.fetchall()[0][0])

		fvskeywords = re.sub(DEFAULT_DB_REGEX, DB_NAME, fvskeywords)	
		fvskeywords = re.sub("_CN =\s?'%Stand_CN%'", "_ID = '%StandID%'", fvskeywords)
		
		cur.execute(f'''
			UPDATE {TABLE_NAME}
			SET FVSKEYWORDS = "{fvskeywords}" WHERE GROUPS = '{group}'
			''')


def err_and_exit(err: str) -> None:
	print(f'\t[[ Error ]]\n{err}')
	print(f'Now aborting')
	sys.exit(1)


if __name__ == '__main__':
	main()

