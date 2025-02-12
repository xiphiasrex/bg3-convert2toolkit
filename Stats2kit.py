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
    auxdb = None

    # Init
    def __init__(self, db=None, auxdb=None):
        self.db = db
        self.auxdb = auxdb

    def setUUID(self, uuid=None):
        self.uuid = uuid

    # Main call convert function
    def convert(self, file):
        self.file = file
        with open(file) as f:
            self.data = f.read()
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
        if self.auxdb is None:
            self.auxdb = {}
        construct = {'stats': {'@stat_object_definition_id': nodeUUID, 'stat_objects': {'stat_object': []}}}

        # Read line by line
        t = []
        i = 0
        dupes = []
        auxIDfix = {}
        for line in self.data.split("\n"):
            i += 1
            raw = line.split('"')[1::2]
            if len(raw) > 0: # Ignore duplicaten entries
                if raw[0] in dupes:
                    continue
                dupes.append(raw[0])
            if line[:3:] == "new": # Data definition entries
                newUID = self.genUUID()
                nameval = raw[0].replace(f'{os.path.basename(self.file).split(".")[0].replace("Spell_","")}_', '')

                fname, fext = os.path.splitext(os.path.basename(self.file).replace("Spell_",""))
                if fname == "Projectile" or fname == "Target" or fname == "Zone" or fname == "Shout" or fname == "ProjectileStrike" or fname == "Rush" or fname == "Teleportation" or fname == "Throw":
                    auxIDfix[f'{fname}_{nameval}'] = newUID
                else:
                    auxIDfix[nameval] = newUID
                
                t.append({'@name': 'UUID', '@type': 'IdTableFieldDefinition', '@value': newUID})
                t.append({'@name': 'Name', '@type': 'NameTableFieldDefinition', '@value': nameval})
                continue
            if line[:5:] == "using": # Skip parent if IDs not in aux db
                t.append({'@name': 'Using', '@type': 'BaseClassTableFieldDefinition', '@value': self.auxdb.get(raw[0],raw[0])})
                continue
            if line[:4:] == "data": # Data entries
                builder = self.gen_dict(raw, i)
                if not builder is None:
                    t.append(builder)
                continue
            if line == '': # Data seperator
                if not (not t):
                    construct['stats']['stat_objects']['stat_object'].append({'@is_substat': 'false', 'fields': {'field': t}})
                t = []
                i = 0
                dupes = []

        # Try fixing parent IDs
        isRecovered = True
        for i, x in enumerate(construct['stats']['stat_objects']['stat_object']):
            for y, val in enumerate(x['fields']['field']):
                if val['@name'] == 'Using' and not self.is_guid(val['@value']):
                    construct['stats']['stat_objects']['stat_object'][i]['fields']['field'][y]['@value'] = auxIDfix.get(val['@value'],'')
                    if construct['stats']['stat_objects']['stat_object'][i]['fields']['field'][y]['@value'] == '':
                        isRecovered = False
        if not isRecovered:
            print(f'{Fore.YELLOW}Missing parent entries in: {os.path.basename(self.file)}{Fore.WHITE}')
        return construct

    # Generate xml object to construct entry data
    def gen_dict(self, data, i):
        try:
            builder = {'@name': data[0], '@type': self.db['DataTypes'].get(data[0], '')}
            if self.db['DataTypes'].get(data[0], '') == "TranslatedStringTableFieldDefinition": # Translated entries
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

    def is_guid(self, val):
        if len(val) == 36 and val[8:9:] == "-" and val[13:14:] == "-" and val[18:19:] == "-" and val[23:24:] == "-":
            return True
        return False