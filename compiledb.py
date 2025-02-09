from pathlib import Path
import xmltodict
import json
import os

class CompileDB():
	data = None
	file = None
	db = None

	def __init__(self):
		pass

	def compile(self):
		self.db = {"LSX":{},"Stats":{},"DataTypes":{"EnumTypes":{}}}

		for file in Path('.').rglob('*.*'):
			self.file = file
			fname, fext = os.path.splitext(file)
			fname = os.path.basename(fname)

			if (fext != '.tbl' and fext != '.stats') or self.is_file_guid(fname):
				continue
			try:
				self.data = self.readxml(str(file))
				if fext == ".tbl":
					self.db['LSX'][fname] = self.data['stats']['@stat_object_definition_id']
				elif fext == ".stats":
					self.db['Stats'][fname] = self.data['stats']['@stat_object_definition_id']

				builder = self.data['stats']['stat_objects']['stat_object']
				if not isinstance(builder, list):
					builder = [builder]
				for node in builder:
					for subnode in node['fields']['field']:
						self.db['DataTypes'][subnode['@name']] = subnode['@type']
						if subnode['@type'] == 'EnumerationTableFieldDefinition':
							self.db['DataTypes']['EnumTypes'][subnode['@name']] = subnode['@enumeration_type_name']

				print(f'Compiled {file}')
			except Exception as e:
				if str(e) != "'NoneType' object is not subscriptable":
					print(f'Failed to compile {os.path.basename(file)}:\n\t{e}')

		print(f'\nCompile Completed')
		with open(f'./db.json', 'w') as f:
			f.write(json.dumps(self.db, indent=4))

	# Read data from xml file
	def readxml(self, file):
		with open(file, 'r+b') as f:
			data = xmltodict.parse(f.read())
		return data

	def is_file_guid(self, file):
		if len(file) == 36 and file[8:9:] == "-" and file[13:14:] == "-" and file[18:19:] == "-" and file[23:24:] == "-":
			return True
		return False

if __name__ == "__main__":
	cdb = CompileDB()
	cdb.compile()