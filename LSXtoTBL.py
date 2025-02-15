import xmltodict
from pathlib import Path
from colorama import Fore, Back, Style
import colorama
import os

class LSXconvert():
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
        if self.is_file_guid(os.path.basename(file).split(".")[0]):
            raise Exception('Cannot convert to binary')
        self.readxml(file)
        self.writexml(self.convert_all())
    
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
        out = file.replace('.lsx', '.tbl')
        with open(out, 'w') as f:
            f.write(xmltodict.unparse(data, pretty=True, indent='  '))

    # Convert function logic
    def convert_all(self):
        if self.uuid is None:
            nodeUUID = ''
        else:
            nodeUUID = self.uuid
        construct = {'stats': {'@stat_object_definition_id': nodeUUID, 'stat_objects': {'stat_object': []}}}

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
                            builder[ax['@id']] = {'@name': ax['@id'], '@type': self.gen_dict_keytype(ax['@id'], ax['@id']), '@value': f'{ax["attribute"]["@value"]}'}
                        else:
                            builder[ax['@id']]['@value'] = f'{builder[ax["@id"]]["@value"]};{ax["attribute"]["@value"]}'
                    for ax, bx in builder.items():
                        t.append(bx)
                return t
            else: # 1 layer but only one node
                chk_node = [aval['node']]

            for ax in chk_node:
                if builder.get(ax['@id'], None) is None:
                    builder[ax['@id']] = {'@name': ax['@id'], '@type': self.gen_dict_keytype(ax['@id']), '@value': f'{ax["attribute"]["@value"]}'}
                else:
                    builder[ax['@id']]['@value'] = f'{builder[ax["@id"]]["@value"]};{ax["attribute"]["@value"]}'
            for ax, bx in builder.items():
                t.append(bx)
        return t

    # Generate dict lsx node from xml node
    def gen_dict(self, node):
        try:
            ndict = {}

            # Attach values to keys
            for key, val in node.items():
                if key == '@id':
                    ndict['@name'] = val
                    continue
                if key == '@type':
                    ndict[key] = self.gen_dict_keytype(val, ndict.get('@name', None))
                    continue
                if key == '@value' and ndict.get('@type', None) == 'TranslatedStringTableFieldDefinition':
                    ndict['@handle'] = val
                    ndict['@version'] = '1'
                    continue

                # Enum specific fields
                # TODO: Try making dynamic
                if ndict.get('@type', None) == 'EnumerationTableFieldDefinition':
                    ndict['@version'] = '1'
                    if ndict.get('@name', None) == 'BodyType' or ndict.get('@name', None) == 'DefaultForBodyType':
                        ndict['@enumeration_type_name'] = 'BodyType'
                        if node['@value'] == '0':
                            ndict['@value'] = 'Male'
                        elif node['@value'] == '1':
                            ndict['@value'] = 'Female'
                    if ndict.get('@name', None) == 'SlotName':
                        ndict['@enumeration_type_name'] = 'CharacterCreatorSlotNames'
                    if ndict.get('@name', None) == 'BodyShape':
                        ndict['@enumeration_type_name'] = 'BodyShape'
                        if node['@value'] == '0':
                            ndict['@value'] = 'Standard'
                        elif node['@value'] == '1':
                            ndict['@value'] = 'Strong'

                if ndict.get(key, None) is None:
                    ndict[key] = val
            return ndict
        except Exception as e:
            print(f'Exception: {e}; Ignored')

    # Translate lsx node type to tbl type
    def gen_dict_keytype(self, val, key = None):
        dtype = self.db['DataTypes'].get(key, '')
        if dtype == 'IntegerTableFieldDefinition':
            dtype = 'ByteTableFieldDefinition'
        return dtype

    # Check if name or file is of guid type
    def is_file_guid(self, file):
        if len(file) == 36 and file[8:9:] == "-" and file[13:14:] == "-" and file[18:19:] == "-" and file[23:24:] == "-":
            return True
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