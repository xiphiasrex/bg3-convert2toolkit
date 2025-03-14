import xmltodict
import random
from pathlib import Path
from colorama import Fore, Back, Style
import colorama
import json
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
        with open(file, encoding="utf-8-sig") as f:
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
        auxIDfix = {}

        # Special handling for awesome treasure tables
        if self.data.startswith(("treasure", "new treasuretable")):
            self.process_treasure_table(construct)
        else:
            # Read line by line
            t = []
            i = 0
            dupes = []

            for line in self.data.split("\n"):
                i += 1
                raw = line.split('"')[1::2]

                if len(raw) > 0: # Ignore duplicated entries
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
            print(f'{Fore.YELLOW}[stats] Missing parent entries in: {os.path.basename(self.file)}{Fore.WHITE}')
        with open('auxdb_self_recovered.temp', 'w') as f:
            f.write(json.dumps(auxIDfix, indent=4))
        return construct

    # Generate xml object to construct entry data
    def gen_dict(self, data, i):
        fname, fext = os.path.splitext(os.path.basename(self.file).replace("Spell_",""))
        try:
            builder = {'@name': data[0], '@type': self.db['DataTypes'].get(data[0], ''), '@value':''}
            if fname == 'Interrupt': # Hardcoded Properties checks
                if data[0] == 'Properties':
                    builder['@type'] = 'StringTableFieldDefinition'
                if data[0] == 'EnableContext':
                    data[0] = 'EnabledContext'
                    builder['@name'] = data[0]
                if data[0] == 'EnableCondition':
                    data[0] = 'EnabledConditions'
                    builder['@name'] = data[0]
            if self.db['DataTypes'].get(data[0], '') == "TranslatedStringTableFieldDefinition": # Translated entries
                builder['@handle'] = data[1].split(";")[0]
                builder['@version'] = "1"
            else: # All normal entries
                if data[1] == "":
                    return None
                if builder['@value'] == '':
                    builder['@value'] = data[1]
            if self.db['DataTypes'].get(data[0], '') == '' and i != 3: # i = 3; ignore types
                print(f'{Fore.YELLOW}[stats] Missing Pre-Configured Data Type: {data[0]}{Fore.WHITE}')
            if self.db['DataTypes'].get(data[0], '') == "EnumerationListTableFieldDefinition" or self.db['DataTypes'].get(data[0], '') == "EnumerationTableFieldDefinition": # Enum types
                builder['@enumeration_type_name'] = self.db['DataTypes']['EnumTypes'].get(data[0], data[0])
                builder['@version'] = "1"
            return builder
        except Exception as e:
            print(f'[stats] Exception: {e}; Ignored')
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

    def process_treasure_table(self, construct: dict):
        t = []
        has_subtable = False
        base_table_uuid = ""
        base_table_name = ""
        is_substat = 'false'

        for line in self.data.split("\n"):
            tokens = line.split(" ")

            # Skip
            if line == '' or line.startswith("treasure"):
                continue

            # If we have data and a new table or secondary subtable, output field to main dictionary
            if not (not t) and (line.startswith("new treasuretable") or line.startswith("new subtable") and has_subtable):
                construct['stats']['stat_objects']['stat_object'].append({'@is_substat': is_substat, 'fields': {'field': t}})
                t = []
                is_substat = 'false'
                if line.startswith("new subtable"):
                    is_substat = 'true'

            # Initialize new field section for new table
            if line.startswith("new treasuretable"):
                has_subtable = False
                base_table_uuid = self.genUUID()
                base_table_name = tokens[2].strip('"')
                t.append({'@name': 'UUID', '@type': 'IdTableFieldDefinition', '@value': base_table_uuid})
                t.append({'@name': 'Name', '@type': 'NameTableFieldDefinition', '@value': base_table_name})
                continue

            if line.startswith("new subtable"):
                if has_subtable:
                    builder = self.gen_dict(["Using", base_table_uuid], 1)
                    if not builder is None:
                        t.append(builder)
                    t.append({'@name': 'UUID', '@type': 'IdTableFieldDefinition', '@value': self.genUUID()})
                    t.append({'@name': 'Name', '@type': 'NameTableFieldDefinition', '@value': str(base_table_name + '_substat')})
                else:
                    has_subtable = True

                builder = self.gen_dict(["DropCount", tokens[2].strip('"')], 1)
                if not builder is None:
                    t.append(builder)
                continue

            if line.startswith("object category"):
                fields = tokens[2].strip('"').split(',')
                builder = self.gen_dict(["ObjectCategory", fields[0].strip('"')], 1)
                if not builder is None:
                    t.append(builder)
                builder = self.gen_dict(["Frequency", fields[1].strip('"')], 1)
                if not builder is None:
                    t.append(builder)
                continue

            if line.startswith(("MinLevel", "MaxLevel", "StartLevel", "EndLevel", "CanMerge")):
                field_name = tokens[0]
                field_value = tokens[1].strip('"')
                if field_name == "MinLevel" or field_name == "MaxLevel":
                    field_name = str(field_name + 'Diff')
                elif field_name == "CanMerge":
                    if field_value == '1':
                        field_value = 'Yes'
                    else:
                        field_value = 'No'
                builder = self.gen_dict([field_name, field_value], 1)
                if not builder is None:
                    t.append(builder)
                continue

        if not (not t):
            construct['stats']['stat_objects']['stat_object'].append({'@is_substat': is_substat, 'fields': {'field': t}})
