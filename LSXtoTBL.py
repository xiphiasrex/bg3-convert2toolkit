import xmltodict
from pathlib import Path
from colorama import Fore, Back, Style
import colorama
import json, random
import os

class LSXconvert():
    data = None
    file = None
    uuid = None
    db = None
    auxIDfix = None

    with open('db.json', encoding="utf-8") as f:
        backup_db = json.load(f)

    lastName = ''

    # Init
    def __init__(self, db=None):
        self.db = db

    def setUUID(self, uuid=None):
        self.uuid = uuid

    # Main call convert function
    def convert(self, file):
        self.file = file
        if self.is_file_guid(os.path.basename(file).split(".")[0]):
            #raise Exception('Cannot convert to binary')
            print(f'{Fore.YELLOW}[info] Skipped file: {os.path.basename(self.file)} (Reason: Cannot convert binary){Fore.WHITE}')
            return False
        self.readxml(file)
        return self.writexml(self.convert_all())
    
    # Read data from xml file
    def readxml(self, file):
        self.file = file
        with open(file, 'r+b') as f:
            self.data = xmltodict.parse(f.read())
        return self.data

    # Write data to xml file
    def writexml(self, data, file = None):
        if file is None:
            file = self.file
        if data is None:
            return False
        out = file.replace('.lsx', '.tbl')
        with open(out, 'w') as f:
            f.write(xmltodict.unparse(data, pretty=True, indent='  '))
        return True

    # Convert function logic
    def convert_all(self):
        fname, fext = os.path.splitext(os.path.basename(self.file))

        if isinstance(self.data['save']['region'], list):
            self.ftype = self.data['save']['region'][0].get('@id', fname)
        else:
            self.ftype = self.data['save']['region'].get('@id', fname)
        if self.ftype == 'IconUVList' or self.ftype == 'TextureAtlasInfo':
            print(f'{Fore.YELLOW}[info] Skipped file: {os.path.basename(self.file)} (Reason: Atlas doesnt need conversion){Fore.WHITE}')
            return None

        if self.uuid is None:
            nodeUUID = ''
        else:
            nodeUUID = self.db['LSX'].get(self.ftype, self.uuid)
            if nodeUUID != self.uuid:
                print(f"{Fore.YELLOW}[lsx] ID Override for {os.path.basename(self.file)}: {nodeUUID} ({self.data['save']['region'].get('@id', None)}){Fore.WHITE}")

        construct = {'stats': {'@stat_object_definition_id': nodeUUID, 'stat_objects': {'stat_object': []}}}

        try:
            with open('auxdb_self_recovered.temp', encoding="utf-8") as f:
                self.auxIDfix = json.load(f)
        except Exception as e:
            self.auxIDfix = {}

        root = self.data['save']['region']['node']['children']['node']
        for x in root: # loop every node in root
            if isinstance(x, str): # root only contains 1 node
                t = self.loop_elements(root)
                construct['stats']['stat_objects']['stat_object'].append({'@is_substat': 'false', 'fields': {'field': t}})
                break
            else: # construct xml node
                t = self.loop_elements(x)
            construct['stats']['stat_objects']['stat_object'].append({'@is_substat': 'false', 'fields': {'field': t}})
        return construct

    # Loop all elements in node
    def loop_elements(self, elem):
        t = []
        for akey, aval in elem.items():
            t = self.loop_builder(t, akey, aval)

        if self.lastName == '':
            self.lastName = self.genUUID()
        if not self.nodeHasEntry(t, 'NameFS'):
            t.append({'@name':'NameFS','@type':'FixedStringTableFieldDefinition','@value':self.lastName})
        if not self.nodeHasEntry(t, 'Name'):
            t.append({'@name':'Name','@type':'NameTableFieldDefinition','@value':self.lastName})
        self.lastName = ''
        return t

    def loop_builder(self, t, akey, aval, lnode=None):
        if akey == 'attribute': # Add attribute to builder
            for node in aval:
                t.append(self.gen_dict(node))
        elif akey == 'children': # Combine children and add to builder
            builder = {}
            if isinstance(aval['node'], list): # 1 layer
                chk_node = aval['node']
            elif not aval['node'].get('children', None) is None: # Multilayer
                for xkey, xval in aval['node']['children'].items():
                    for ax in xval:
                        ax['@id'] = aval['node'].get('@id', None)
                        if builder.get(ax['@id'], None) is None:
                            builder[ax['@id']] = {'@name': ax['@id'], '@type': self.gen_dict_keytype(ax['@id']), '@value': f'{ax["attribute"]["@value"]}'}
                        else:
                            builder[ax['@id']]['@value'] = f'{builder[ax["@id"]]["@value"]};{ax["attribute"]["@value"]}'
                    for ax, bx in builder.items():
                        t.append(bx)
                return t
            else: # 1 layer but only one node
                chk_node = [aval['node']]

            for ax in chk_node:
                if not ax.get('children', None) is None:
                    t = self.loop_builder(t, ax['@id'], 'children', ax['children'])
                    continue
                if builder.get(ax['@id'], None) is None:
                    builder[ax['@id']] = {'@name': ax['@id'], '@type': self.gen_dict_keytype(ax['@id']), '@value': f'{ax["attribute"]["@value"]}'}
                else:
                    builder[ax['@id']]['@value'] = f'{builder[ax["@id"]]["@value"]};{ax["attribute"]["@value"]}'
            for ax, bx in builder.items():
                t.append(bx)
        return t

    # Generate dict lsx node from xml node
    def gen_dict(self, node):
        fname, fext = os.path.splitext(os.path.basename(self.file))
        try:
            ndict = {}

            # Attach values to keys
            for key, val in node.items():
                if key == '@id':
                    # Hardcoded lsx name fixes
                    if self.ftype == 'DefaultValues':
                        if val == 'TableUUID':
                            val = 'ProgressionUUID'
                        if val == 'OriginUUID':
                            val = 'Origin'
                        if val == 'TableUUID':
                            val = 'ProgressionUUID'
                        if val == 'TableUUID':
                            val = 'ProgressionUUID'
                        if val == 'Add' and fname != 'Spells':
                            val = 'DefaultValues'
                    if fname == 'ClassDescriptions' and val == 'ParentGuid':
                        val = 'ParentUUID'

                    ndict['@name'] = val
                    continue
                if key == '@type':
                    ndict[key] = self.gen_dict_keytype(ndict.get('@name', None), ndict.get('@name', None))
                    continue
                if key == '@value' and ndict.get('@type', None) == 'TranslatedStringTableFieldDefinition':
                    ndict['@handle'] = val
                    ndict['@version'] = '1'
                    continue

                # Enum specific fields
                if ndict.get('@type', None) == 'EnumerationTableFieldDefinition' or ndict.get('@type', None) == 'EnumerationListTableFieldDefinition':
                    ndict['@version'] = '1'
                    ndict['@enumeration_type_name'] = self.db['DataTypes']['EnumTypes'].get(ndict.get('@name', None), ndict.get('@name', None))
                    val = self.db['DataTypes']['EnumSubTypes'].get(ndict.get('@name', None), {})
                    if isinstance(val, dict):
                        ndict['@value'] = val.get(node['@value'], node['@value'])
                    else:
                        ndict['@value'] = node['@value']

                if ndict.get(key, None) is None:
                    if key == '@value' and ndict['@name'] == 'Name':
                        self.lastName = val
                    ndict[key] = val
            return ndict
        except Exception as e:
            print(f'[lsx] Exception: {e}; Ignored')

    # Translate lsx node type to tbl type
    def gen_dict_keytype(self, key = None, val = None):
        fname, fext = os.path.splitext(os.path.basename(self.file))
        dtype = self.db['DataTypes'].get(key, '')

        # Hardcoded lsx type fixes
        if dtype == 'IntegerTableFieldDefinition' and fname == 'Progressions':
            dtype = 'ByteTableFieldDefinition'
        if fname == 'ProgressionDescriptions' and val == 'Type':
            dtype = 'FixedStringTableFieldDefinition'
        if (fname == 'Spells' or fname == 'Abilities' or fname == 'Passives' or fname == 'Skills'):
            if val == 'SelectorId':
                dtype = 'StringTableFieldDefinition'
            if val == 'ClassUUID':
                dtype = 'GuidTableFieldDefinition'
        if self.ftype == 'CompanionPresets' and key == 'RootTemplate':
            dtype = 'GuidTableFieldDefinition'
        if self.ftype == 'Origins':
            if key == 'ClassUUID':
                dtype = 'GuidTableFieldDefinition'
            if key == 'Unique':
                dtype = 'BoolTableFieldDefinition'
        if self.ftype == 'Rulebook' and key == 'Weight':
            dtype = 'ModifierTableFieldDefinition'

        return dtype

    # Check if name or file is of guid type
    def is_file_guid(self, file):
        if len(file) == 36 and file[8:9:] == "-" and file[13:14:] == "-" and file[18:19:] == "-" and file[23:24:] == "-":
            return True
        return False

    # Safe list get without crash
    def list_get(self, l, idx, default):
        try:
            return l[idx]
        except IndexError:
            return default

    def genUUID(self):
        uuid = ""
        for i in range(36):
            if i == 8 or i == 13 or i == 18 or i == 23:
                uuid += "-"
            else:
                uuid += random.choice("abcdef0123456789")
        return uuid

    # Check if node contains element
    def nodeHasEntry(self, node, entry):
        try:
            for x in node:
                if x.get('@name', None) == entry:
                    return True
            return False
        except Exception:
            return False

# Convert every lsx file in dir
if __name__ == "__main__":
    conv = LSXconvert()
    for file in Path('.').rglob('*.lsx'):
        try:
            conv.convert(str(file))
            print(f'Converted {file}')
        except Exception as e:
            print(f'Failed to convert {file}:\n\t{e}')