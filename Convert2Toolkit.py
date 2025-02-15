from pathlib import Path
from colorama import Fore, Back, Style
import colorama
import xmltodict
import json
import os

from LSXtoTBL import LSXconvert
from Stats2kit import StatsConvert
from compiledb import CompileDB
from fixlocale import FixLocale

exclusions = ['meta.lsx', 'CC_Icons.lsx']

def ConvertDB(file, db, converter):
	if os.path.basename(file) in exclusions:
		return
	try:
		fuuid = db.get(os.path.basename(file).split('.')[0].replace('Spell_', ''), None)
		converter.setUUID(fuuid)
		converter.convert(str(file))
		print(f'{Fore.GREEN}[info] Converted {os.path.basename(file)} (UUID: {fuuid}){Fore.WHITE}')
	except Exception as e:
		print(f'{Fore.RED}[info] Failed to convert {os.path.basename(file)}:\n\t{e}{Fore.WHITE}')

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
		
		compdb = CompileDB(settings.get('bg3path',''))
		if settings.get('compileAux',1):
			print(f'{Fore.YELLOW}[config] bg3.exe found\n[db] Compiling auxiliary ID Database...{Fore.WHITE}')
			auxdb = compdb.compileAuxiliaryDB()
		else:
			print(f'{Fore.YELLOW}[config] bg3.exe found\n[db] Loading auxiliary ID Database...{Fore.WHITE}')
			with open('auxdb.json', encoding="utf-8") as f:
				auxdb = json.load(f)
	except Exception as e:
		auxdb = None

	# Load DB
	with open('db.json', encoding="utf-8") as f:
		db = json.load(f)

	conv_lsx = LSXconvert(db)
	conv_stats = StatsConvert(db, auxdb)
	fix_locale = FixLocale()

	Path("./convert/").mkdir(parents=True, exist_ok=True)

	# Convert Stats
	print(f'{Fore.CYAN}[main] Converting Stats files:{Fore.WHITE}')
	for file in Path('./convert/').rglob('*.txt'):
		ConvertDB(file, db['Stats'], conv_stats)

	# Convert LSX
	print(f'\n{Fore.CYAN}[main] Converting LSX files:{Fore.WHITE}')
	for file in Path('./convert/').rglob('*.lsx'):
		ConvertDB(file, db['LSX'], conv_lsx)

	# Fix locales
	print('')
	for file in Path('./convert/').rglob('*.xml'):
		if os.path.basename(file)[-8::] == '_fix.xml':
			continue
		fix_locale.fix(file, conv_lsx)