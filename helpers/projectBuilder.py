from pathlib import Path
from colorama import Fore, Back, Style
import colorama
import os, re
import shutil
import random

from helpers.LSXtoTBL import LSXconvert

class projectBuilder():
    data = None
    prompt = False
    projects = []
    path_to_templates = None

    # Init
    def __init__(self, path_to_templates: Path):
        self.conv_lsx = LSXconvert()
        self.path_to_templates = path_to_templates

    # Check if path is a workspace resembling a project
    def isProject(self, dirs):
        pdir = Path(dirs)
        if not pdir.exists() or not pdir.is_dir():
            return False
        structure = ['Public/','Mods/']
        for s in structure:
            if not Path(f'{dirs}/{s}').exists():
                return False
        return True
    # Add workspace to projects
    def addProject(self, dirs):
        if not dirs in self.projects:
            self.projects.append(dirs)
        return True

    # Build all saved projects
    def buildAll(self, prompt = False):
        self.prompt = prompt
        for x in self.projects:
            self.build(x)

    # Build a projects for use with Toolkit
    def build(self, dirs):
        pname_raw = os.path.basename(os.path.dirname(dirs))
        if not self.isProject(dirs):
            print(f'{Fore.YELLOW}[Project] {pname_raw} is not a valid project{Fore.RESET}')
            return False

        # Vars
        pguid = self.genUUID()
        pname = ''.join(x for x in f'{pname_raw}_{pguid}' if x.isalnum() or x in ['_','-','(',')'])
        pdir = f'./convert/{pname}/'

        # Prompt user for input
        if self.prompt:
            print(f'{Fore.CYAN}[Project] Attempting to create Project \'{pname_raw}\'\nEnter Project name (type X to skip or leave empty to use default): {Fore.RESET}')
            name = input()
            if name == 'X' or name == 'x': # Skip
                return False
            name = ''.join(x for x in name if x.isalnum() or x in ['_','-','(',')'])
            if not name == '':
                pname = f'{name}_{pguid}'
                pdir = f'./convert/{pname}/'
                pname_raw = name

        try:
            # Workspace structure and metadata
            structure = [f'Editor/Mods/{pname}/', f'Generated/Public/{pname}/', f'Public/{pname}/RootTemplates/', f'Public/{pname}/Content/[PAK]_{pname_raw}/', f'Mods/{pname}/Localization/English/', f'Mods/{pname}/', f'Mods/{pname}/Scripts/', f'Mods/{pname}/GUI/', f'Projects/{pname}/']
            for s in structure:
                Path(f'{pdir}/{s}').mkdir(parents=True, exist_ok=True)
            self.createMeta(pdir, pname, pname_raw, pguid)

            # Copy all files to the correct location
            for file in Path(dirs).rglob('*'):
                if Path(file).is_dir():
                    continue
                fname = str(file).replace("\\", "/")
                psource = f'./{os.path.dirname(fname)}/'
                pdest = f'{pdir}/{os.path.dirname(fname.replace(f"convert/{os.path.basename(os.path.dirname(dirs))}/",""))}/'
                fsource = os.path.basename(fname)
                fdest = os.path.basename(fname)

                pdest = re.sub(r'/Public/.*?/', f'/Public/{pname}/', pdest)
                pdest = re.sub(r'/Mods/.*?/', f'/Mods/{pname}/', pdest)
                pdest = pdest.replace(f'/Stats/Generated/Data/', f'/Stats/')

                # Change destination if table or stats file
                if Path(fsource).suffix == '.tbl' or Path(fsource).suffix == '.stats':
                    pdest = pdest.replace(f'/Public/{pname}/', f'/Editor/Mods/{pname}/')
                    pdest = self.translateStructure(pdest, fdest)

                # Fix destination if generated
                if '/Generated/' in pdest and not '/Generated/Public/' in pdest and not '/Stats/Generated/Data/' in pdest:
                    pdest = pdest.replace('/Generated/', f'/Generated/Public/{pname}/')

                # Fix localization
                if '/Localization/' in pdest and not f'/Mods/{pname}/Localization/' in pdest:
                    pdest = pdest.replace('/Localization/', f'/Mods/{pname}/Localization/')

                ofile = f'{psource}{fsource}'.replace("//", "/")
                nfile = f'{pdest}{fdest}'.replace("//", "/")

                Path(pdest).mkdir(parents=True, exist_ok=True)
                if not Path(nfile).exists() and Path(ofile).exists():
                    shutil.copy(ofile, nfile)

                # Edit paths if lsf file and re-convert
                try:
                    ftype = self.conv_lsx.getDataType(nfile)
                    if not ftype in self.conv_lsx.lsftypes and not ftype in ['IconUVList','TextureAtlasInfo']:
                        continue # Ignore all non lsf files

                    with open(nfile, 'r', encoding="utf-8") as f:
                        data = f.read()

                    # Visual Resource Generated Path
                    if ftype in self.conv_lsx.lsftypes:
                        try:
                            loc = re.search(r'Generated/.*?/', data).group().split('/')
                            if not loc[1] == 'Public':
                                data = data.replace('Generated/', f'Generated/Public/{pname}/')
                        except Exception as e:
                            pass # Ignore outlier files
                    # UI Resource Public Path
                    data = re.sub(r'(?!.*Public\/Shared\/Assets\/)Public\/.*?\/Assets\/', f'Public/{pname}/Assets/', data)

                    with open(nfile, 'w', encoding="utf-8") as f:
                        f.write(data)

                    self.conv_lsx.lsx2lsf(nfile, False)
                except Exception as e:
                    continue # Failsafe

            # File Cleanup
            #TODO remove duplicate files, conversion leftovers or localization files

            print(f'{Fore.GREEN}[Project] Project {pname_raw} successfully created{Fore.RESET}')
            #raise Exception('Cleanup')
            return True
        except Exception as e:
            # Failed (failsafe catch)
            print(f'{Fore.RED}[Project] Failed to create project {pname_raw}\n\tReason: {e}{Fore.RESET}')
            if Path(pdir).exists():
                shutil.rmtree(pdir)
            return False

    # Create metadata
    def createMeta(self, pdir, pname, pname_raw, pguid):

        # Project Metadata
        with open(f'{self.path_to_templates}/project_meta.lsx', 'r', encoding="utf-8") as f:
            data = f.read()

        data = data.replace('$MODULE_ID', pguid)
        data = data.replace('$PROJECT_ID', self.genUUID())
        data = data.replace('$PROJECT_NAME', self.xmlesc(pname_raw))

        with open(f'{pdir}/Projects/{pname}/meta.lsx', 'w', encoding="utf-8") as f:
            f.write(data)

        # Mod Metadata
        with open(f'{self.path_to_templates}/mod_meta.lsx', 'r', encoding="utf-8") as f:
            data = f.read()

        data = data.replace('$MOD_FOLDER', self.xmlesc(pname))
        data = data.replace('$MOD_NAME', self.xmlesc(pname_raw))
        data = data.replace('$MOD_UUID', pguid)

        with open(f'{pdir}/Mods/{pname}/meta.lsx', 'w', encoding="utf-8") as f:
            f.write(data)

        return True

    # Generate a new UUID
    def genUUID(self):
        uuid = ""
        for i in range(36):
            if i == 8 or i == 13 or i == 18 or i == 23:
                uuid += "-"
            else:
                uuid += random.choice("abcdef0123456789")
        return uuid

    # Check if a given string is a valid GUID
    def is_guid(self, val):
        if len(val) == 36 and val[8:9:] == "-" and val[13:14:] == "-" and val[18:19:] == "-" and val[23:24:] == "-":
            return True
        return False

    # Escape string for xml
    def xmlesc(self, txt):
        table = str.maketrans({
            "<": "&lt;",
            ">": "&gt;",
            "&": "&amp;",
            "'": "&apos;",
            '"': "&quot;",
        })
        return txt.translate(table)

    # Translate lsx file structure to tbl
    def translateStructure(self, dirs, file):
        paths = {
            "/Stats/Generated/Data/": "/Stats/",
        }
        files = {
            "Character.stats": "/Stats/",
            "Interrupt.stats": "/Stats/",
            "Passive.stats": "/Stats/",
            "Weapon.stats": "/Stats/",
            "Status_BOOST.stats": "/StatusData/",
            "Status_DOWNED.stats": "/StatusData/",
            "Status_INVISIBLE.stats": "/StatusData/",
            "Status_POLYMORPHED.stats": "/StatusData/",
            "Status_SNEAKING.stats": "/StatusData/",
            "Projectile.stats": "/SpellData/",
            "Rush.stats": "/SpellData/",
            "Shout.stats": "/SpellData/",
            "Target.stats": "/SpellData/",
            "Teleportation.stats": "/SpellData/",
            "Zone.stats": "/SpellData/",
            "Equipment.stats": "/Equipment/",
        }
        for key, val in paths.items():
            dirs = dirs.replace(key, val)
        for key, val in files.items():
            if file == key:
                dirs = dirs.replace(f'/Stats/', f'/Stats/{val}')
        return dirs