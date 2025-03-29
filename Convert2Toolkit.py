from pathlib import Path
from colorama import Fore
import json
import os

from helpers.LSXtoTBL import LSXconvert
from helpers.Stats2kit import StatsConvert
from helpers.compiledb import CompileDB
from helpers.fixlocale import FixLocale
from helpers.projectBuilder import projectBuilder

exclusions = ['meta.lsx', 'metadata.lsf.lsx']
forcefail = ['Rulebook.lsx', 'SpellSet.txt']

def ConvertDB(file, db, converter):
	if os.path.basename(file) in exclusions:
		return
	try:
		fuuid = db.get(os.path.basename(file).split('.')[0].replace('Spell_', ''), None)
		converter.setUUID(fuuid)
		chk = converter.convert(str(file))
		if chk:
			if fuuid is None:
				print(f'{Fore.YELLOW}[info] Converted {os.path.basename(file)} (No UUID found: Incorrect filename){Fore.RESET}')
			else:
				print(f'{Fore.GREEN}[info] Converted {os.path.basename(file)} (UUID: {fuuid}){Fore.RESET}')
			return True
	except Exception as e:
		if is_file_guid(os.path.basename(file).split(".")[0]):
			print(f'{Fore.YELLOW}[info] Skipped file: {os.path.basename(file)} (Reason: Cannot convert binary){Fore.WHITE}')
			return True
		print(f'{Fore.RED}[info] Failed to convert {os.path.basename(file)}:\n\tError: {e}\n\tFile: {file}{Fore.RESET}')
		return False

# Check if name or file is of guid type
def is_file_guid(file):
	if len(file) == 36 and file[8:9:] == "-" and file[13:14:] == "-" and file[18:19:] == "-" and file[23:24:] == "-":
		return True
	return False

# Convert any projects in convert folder
if __name__ == "__main__":
	# Load Settings
	auxdb = None

	with open('settings.json', encoding="utf-8") as f:
		settings = json.load(f)
		bg3path = settings.get('bg3path', '')
		compileAux = settings.get('compileAux', 1)

	try:
		# Check if bg3 path valid
		if not Path(f"{bg3path}/bin/bg3.exe").is_file():
			raise Exception('')

		compdb = CompileDB(bg3path)

		if compileAux:
			print(f'{Fore.YELLOW}[config] bg3.exe found\n[db] Compiling auxiliary ID Database...{Fore.RESET}')
			auxdb = compdb.compileAuxiliaryDB()
		else:
			print(f'{Fore.YELLOW}[config] bg3.exe found\n[db] Loading auxiliary ID Database...{Fore.RESET}')
			with open('auxdb.json', encoding="utf-8") as f:
				auxdb = json.load(f)
	except Exception as e:
		auxdb = None

	# Load DB
	with open('db.json', encoding="utf-8") as f:
		db = json.load(f)

	path_to_templates = Path(__file__).parent.resolve() / 'helpers/templates'
	path_to_lslib = Path(__file__).parent.resolve() / 'LSLibDivine/Packed/Tools'

	conv_lsx = LSXconvert(db, path_to_lslib)
	conv_stats = StatsConvert(db, auxdb)
	fix_locale = FixLocale()
	proj_build = projectBuilder(path_to_templates)

	Path("./convert/").mkdir(parents=True, exist_ok=True)

	# Convert Stats
	print(f'{Fore.CYAN}[main] Converting Stats files:{Fore.RESET}')
	for file in Path('./convert/').rglob('*.txt'):
		if os.path.basename(file) in forcefail:
			print(f'{Fore.YELLOW}[info] Skipped file: {os.path.basename(file)} (Reason: Not yet supported){Fore.RESET}')
			continue
		ConvertDB(file, db['Stats'], conv_stats)

	# Convert LSX
	print(f'\n{Fore.CYAN}[main] Converting LSX files:{Fore.RESET}')
	for file in Path('./convert/').rglob('*.lsx'):
		if os.path.basename(file) in forcefail:
			print(f'{Fore.YELLOW}[info] Skipped file: {os.path.basename(file)} (Reason: Not yet supported){Fore.RESET}')
			continue
		ConvertDB(file, db['LSX'], conv_lsx)

	# Fix locales
	print('')
	for file in Path('./convert/').rglob('*.xml'):
		if os.path.basename(file)[-8::] == '_fix.xml':
			continue
		if os.path.basename(file) in forcefail:
			print(f'{Fore.YELLOW}[info] Skipped file: {os.path.basename(file)} (Reason: Not yet supported){Fore.RESET}')
			continue
		fix_locale.fix(file, conv_lsx)

	# Check and build Projects
	print('')
	for file in os.listdir('./convert/'):
		fname = f'./convert/{file}/'
		if Path(fname).is_dir():
			if proj_build.isProject(fname):
				proj_build.addProject(fname)
	proj_build.buildAll(True)