import xmltodict
import random
from pathlib import Path
from colorama import Fore, Back, Style
import colorama
import os

class StatsConvert():
    data = None
    file = None
    uuid = None
    db = None

    # Init
    def __init__(self, db=None):
        self.db = db

    def setUUID(self, uuid=None):
        self.uuid = uuid

    # Main call convert function
    def convert(self, file):
        self.file = file
        ftype, ext = file.split('.')
        with open(file) as f:
            self.data = f.read()
        self.convert_all()
        self.writexml(self.convert_all())

    # Write data to xml file
    def writexml(self, data, file = None):
        if file is None:
            file = self.file
        out = file.replace('.txt', '.stats').replace('Spell_', '')
        with open(out, 'w') as f:
            f.write(xmltodict.unparse(data, pretty=True, indent='  '))

    # Convert function logic
    def convert_all(self):
        if self.uuid is None:
            nodeUUID = ''
        else:
            nodeUUID = self.uuid
        construct = {'stats': {'@stat_object_definition_id': nodeUUID, 'stat_objects': {'stat_object': []}}}

        # Read line by line
        t = []
        i = 0
        for line in self.data.split("\n"):
            i += 1
            raw = line.split('"')[1::2]
            if line[:3:] == "new":
                t.append({'@name': 'UUID', '@type': 'IdTableFieldDefinition', '@value': self.genUUID()})
                t.append({'@name': 'Name', '@type': 'NameTableFieldDefinition', '@value': raw[0].replace(f'{os.path.basename(self.file).split(".")[0].replace("Spell_","")}_', '')})
                continue
            if line[:5:] == "using":
                t.append({'@name': 'Using', '@type': 'BaseClassTableFieldDefinition', '@value': ''})
                continue
            if line[:4:] == "data" and i != 3:
                builder = self.gen_dict(raw, i)
                if not builder is None:
                    t.append(builder)
                continue
            if line == '':
                if not (not t):
                    construct['stats']['stat_objects']['stat_object'].append({'@is_substat': 'false', 'fields': {'field': t}})
                t = []
                i = 0
        return construct

    def gen_dict(self, data, i):
        try:
            builder = {'@name': data[0], '@type': self.db['DataTypes'].get(data[0], '')}
            if self.db['DataTypes'].get(data[0], '') == "TranslatedStringTableFieldDefinition":
                builder['@handle'] = data[1].split(";")[0]
                builder['@version'] = "1"
            else:
                if data[1] == "":
                    return None
                builder['@value'] = data[1]
            if self.db['DataTypes'].get(data[0], '') == '' and i != 3:
                print(f'{Fore.YELLOW}Missing Pre-Configured Data Type: {data[0]}{Fore.WHITE}')
            if self.db['DataTypes'].get(data[0], '') == "EnumerationListTableFieldDefinition" or self.db['DataTypes'].get(data[0], '') == "EnumerationTableFieldDefinition":
                builder['@enumeration_type_name'] = self.db['DataTypes']['EnumTypes'].get(data[0], data[0])
                builder['@version'] = "1"
            return builder
        except Exception as e:
            print(f'Exception: {e}; Ignored')
            return None

    def genUUID(self):
        uuid = ""
        for i in range(36):
            if i == 8 or i == 13 or i == 18 or i == 23:
                uuid += "-"
            else:
                uuid += random.choice("abcdef0123456789")
        return uuid