from pathlib import Path
from colorama import Fore, Back, Style
import colorama
import xmltodict
import json
import os

from LSXtoTBL import LSXconvert
from Stats2kit import StatsConvert
from compiledb import CompileDB

exclusions = ['meta.lsx', 'CC_Icons.lsx']

def ConvertDB(file, db, converter):
	if os.path.basename(file) in exclusions:
		return
	try:
		fuuid = db.get(os.path.basename(file).split('.')[0].replace('Spell_', ''), None)
		converter.setUUID(fuuid)
		converter.convert(str(file))
		print(f'{Fore.GREEN}Converted {os.path.basename(file)} (UUID: {fuuid}){Fore.WHITE}')
	except Exception as e:
		print(f'{Fore.RED}Failed to convert {os.path.basename(file)}:\n\t{e}{Fore.WHITE}')

# Convert any projects in convert folder
if __name__ == "__main__":
	# Load Settings
	auxdb = None
	try:
		with open('settings.json', encoding="utf-8") as f:
			settings = json.load(f)

		# Check if bg3 path valid
		if not Path(f"{settings.get('bg3path','')}/bin/bg3.exe").is_file():
			raise Exception('')
		print(f'{Fore.YELLOW}Path to bg3.exe found. Compiling auxiliary ID Database...{Fore.WHITE}')
		compdb = CompileDB(settings.get('bg3path',''))

		if settings.get('compileAux',1):
			auxdb = compdb.compileAuxiliaryDB()
		else:
			with open('auxdb.json', encoding="utf-8") as f:
				auxdb = json.load(f)
	except Exception as e:
		auxdb = None

	# Load DB
	with open('db.json', encoding="utf-8") as f:
		db = json.load(f)

	conv_lsx = LSXconvert()
	conv_stats = StatsConvert(db, auxdb)

	Path("./convert/").mkdir(parents=True, exist_ok=True)

	print('Converting LSX files:')
	for file in Path('./convert/').rglob('*.lsx'):
		ConvertDB(file, db['LSX'], conv_lsx)

	print('\nConverting Stats files:')
	for file in Path('./convert/').rglob('*.txt'):
		ConvertDB(file, db['Stats'], conv_stats)