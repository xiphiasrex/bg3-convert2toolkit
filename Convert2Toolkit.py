import json
from pathlib import Path

from core.ConvertAPI import ConvertAPI
from core.ConvertCLI import ConvertCLI

# Main entry for converter script or exe
if __name__ == "__main__":
	# Load Settings
	with open('settings.json', encoding="utf-8") as f:
		settings = json.load(f)
		bg3path = settings.get('bg3path', '')
		compileAux = settings.get('compileAux', 1)

	# Set up paths for file references (needed due to exe packing)
	path_to_root = Path('.').resolve()
	print(f'path_to_root: {path_to_root}')
	lib_path = Path(__file__).parent.resolve()
	path_to_templates = lib_path / 'lib/templates'
	path_to_lslib = lib_path / 'lib/LSLib'

	# primary logic for conversion is in api object
	convert_api = ConvertAPI(
		src_bg3_path=bg3path,
		path_to_root=path_to_root,
		path_to_templates=path_to_templates,
		path_to_lslib=path_to_lslib,
		compile_aux_db=compileAux
	)

	#TODO: Should this be a build prop/separate exe, setting, etc.?
	use_gui = False

	# Determine process command line vs GUI
	if use_gui:
		#TODO: tie in with ConvertGUI soon™
		pass
	else:
		ConvertCLI(convert_api, path_to_root).run()
