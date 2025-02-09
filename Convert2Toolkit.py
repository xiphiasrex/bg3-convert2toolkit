from pathlib import Path
from colorama import Fore, Back, Style
import colorama
import xmltodict
import json
import os

from LSXtoTBL import LSXconvert
from Stats2kit import StatsConvert

def ConvertDB(file, db, converter):
	if os.path.basename(file) in db["$exclusions$"]:
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
	with open('db.json', encoding="utf-8") as f:
		db = json.load(f)

	conv_lsx = LSXconvert()
	conv_stats = StatsConvert(db)

	Path("./convert/").mkdir(parents=True, exist_ok=True)

	print('Converting LSX files:')
	for file in Path('./convert/').rglob('*.lsx'):
		ConvertDB(file, db['LSX'], conv_lsx)

	print('\nConverting Stats files:')
	print(f'{Fore.YELLOW}Stats conversion not yet completely compatible.\nUncomment code block to enable anyways.{Fore.WHITE}')
	# for file in Path('./convert/').rglob('*.txt'):
	# 	ConvertDB(file, db['Stats'], conv_stats)