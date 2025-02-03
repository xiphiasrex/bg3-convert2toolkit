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
        for x in root:
            if isinstance(x, str):
                t = self.loop_elements(root)
                construct['stats']['stat_objects']['stat_object'].append(t)
                break
            else:
                t = self.loop_elements(x)
            construct['stats']['stat_objects']['stat_object'].append(t)
        return construct

    def loop_elements(self, elem):
        t = {'@is_substat': 'false', 'fields': {'field': []}}
        for akey, aval in elem.items():
            if akey == 'attribute':
                for node in aval:
                    t['fields']['field'].append(self.gen_dict(node))
            elif akey == 'children':
                builder = {}
                for ax in aval['node']:
                    if builder.get(ax['@id'], None) is None:
                        builder[ax['@id']] = {'@name': ax['@id'], '@type': self.gen_dict_keytype(ax['@id']), '@value': f'{ax["attribute"]["@value"]}'}
                    else:
                        builder[ax['@id']]['@value'] = f'{builder[ax["@id"]]["@value"]};{ax["attribute"]["@value"]}'
                for ax, bx in builder.items():
                    t['fields']['field'].append(bx)
        return t

    # Generate dict lsx node from xml node
    def gen_dict(self, node):
        try:
            nodedict = {}

            # Attach values to keys
            for key, val in node.items():
                if key == '@id':
                    nodedict['@name'] = val
                    continue
                if key == '@type':
                    nodedict[key] = self.gen_dict_keytype(val, nodedict.get('@name', None))
                    continue
                if key == '@value' and nodedict.get('@type', None) == 'TranslatedStringTableFieldDefinition':
                    nodedict['@handle'] = val
                    nodedict['@version'] = '1'
                    continue

                # Enum specific fields
                if nodedict.get('@type', None) == 'EnumerationTableFieldDefinition':
                    nodedict['@version'] = '1'
                    if nodedict.get('@name', None) == 'BodyType' or nodedict.get('@name', None) == 'DefaultForBodyType':
                        nodedict['@enumeration_type_name'] = 'BodyType'
                        if node['@value'] == '0':
                            nodedict['@value'] = 'Male'
                        elif node['@value'] == '1':
                            nodedict['@value'] = 'Female'
                    if nodedict.get('@name', None) == 'SlotName':
                        nodedict['@enumeration_type_name'] = 'CharacterCreatorSlotNames'
                    if nodedict.get('@name', None) == 'BodyShape':
                        nodedict['@enumeration_type_name'] = 'BodyShape'
                        if node['@value'] == '0':
                            nodedict['@value'] = 'Standard'
                        elif node['@value'] == '1':
                            nodedict['@value'] = 'Strong'
                if nodedict.get(key, None) is None:
                    nodedict[key] = val
            return nodedict
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