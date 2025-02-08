import xmltodict
from pathlib import Path

class LSXconvert():
    data = None
    file = None

    # Init
    def __init__(self):
        pass

    # Main call convert function
    def convert(self, file):
        self.file = file
        ftype, ext = file.split('.')
        self.readxml(file)
        self.writexml(self.convert_all())
    
    # Read data from xml file
    def readxml(self, file):
        self.file = file
        with open(file, 'r') as f:
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
        construct = {'stats': {'@stat_object_definition_id': '', 'stat_objects': {'stat_object': []}}}

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
            if akey == 'attribute': # Add attribute to builder
                for node in aval:
                    t.append(self.gen_dict(node))
            elif akey == 'children': # Combine children and add to builder
                builder = {}
                if isinstance(aval['node'], list): # 1 layer
                    chk_node = aval['node']
                else: # 2 layers
                    chk_node = aval['node']['children']['node']

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
        if (key == 'Description' or key == 'DisplayName') and (val == 'TranslatedString' or val == 'FixedString'):
            return 'TranslatedStringTableFieldDefinition'
        if key == 'Name' and val == 'FixedString':
            return 'NameTableFieldDefinition'
        if val == 'LSString':
            return 'ColorTableFieldDefinition'
        if val == 'TranslatedString':
            return 'TranslatedStringTableFieldDefinition'
        if val == 'guid' and key == 'UUID':
            return 'IdTableFieldDefinition'
        if val == 'guid':
            return 'GuidTableFieldDefinition'
        if val == 'LSString':
            return 'ColorTableFieldDefinition'
        if val == 'Tags' or val == 'Gods' or val == 'ExcludedGods' or val == 'HairColors' or val == 'HairHighlightColors' or val == 'HairGrayingColors' or val == 'SkinColors' or val == 'EyeColors' or val == 'TattooColors' or val == 'MakeupColors' or val == 'MergedInto':
            return 'GuidObjectListTableFieldDefinition'
        if val == 'uint8' or key == 'SlotName':
            return 'EnumerationTableFieldDefinition'
        return 'FixedStringTableFieldDefinition'

# Convert every lsx file in dir
if __name__ == "__main__":
    conv = LSXconvert()
    for file in Path('.').rglob('*.lsx'):
        try:
            conv.convert(str(file))
            print(f'Converted {file}')
        except Exception as e:
            print(f'Failed to convert {file}:\n\t{e}')