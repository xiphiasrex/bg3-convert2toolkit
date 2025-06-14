import json
import sys
from pathlib import Path

from colorama import Fore

from helpers.LSXtoTBL import LSXconvert
from helpers.Stats2kit import StatsConvert
from helpers.CompileDB import CompileDB
from helpers.FixLocale import FixLocale
from helpers.ProjectBuilder import ProjectBuilder


EXCLUSIONS = ['meta.lsx', 'metadata.lsf.lsx']
FORCE_FAIL = ['SpellSet.txt']


# Primary object for clients to call for conversion logic
class ConvertAPI:
    def __init__(self,
                 src_bg3_path: str,
                 path_to_root: Path,
                 path_to_templates: Path,
                 path_to_lslib: Path,
                 compile_aux_db: bool = False):
        self.path_to_root = path_to_root
        self._aux_db = self._get_auxiliary_db(src_bg3_path, compile_aux_db)
        self._db = self._get_db()
        self._stats_converter = StatsConvert(self._db, self._aux_db, self.path_to_root)
        self._lsx_converter = LSXconvert(self._db, path_to_lslib, self.path_to_root)
        self._locale_fixer = FixLocale()
        self._proj_builder = ProjectBuilder(path_to_templates, path_to_lslib)
        divine = Path(path_to_lslib)
        self._lslib_dll = divine.is_dir() and divine.joinpath("LSLib.dll") or divine.parent.joinpath("LSLib.dll")


    #region Public functions
    def convert(self, source_path: Path, output_dir: Path, is_cli: bool = True):
        """
            Main entry point for basic conversion.
            1. Converts Stat txt files to .stats
            2. Converts lsx files to .tbl
            3. Checks for issues in locale files
            4. If source path conforms to project structure, re-structure to tk folders

        :param source_path: Location of files to convert
        :param output_dir: Location to output converted files
        :param is_cli: Flag to indicate if caller is command line or GUI
        """
        # TODO: source could be loose file(s), project, or pak

        self.convert_stat_files(source_path)
        self.convert_lsx_files(source_path)
        self.fix_locales(source_path)
        self.build_tk_project(source_path, output_dir, is_cli)

    @staticmethod
    def is_project_dir(source_path: Path) -> bool:
        if not source_path.exists() or not source_path.is_dir():
            return False
        structure = ['Public/','Mods/']
        for s in structure:
            if not source_path.joinpath(Path(s)).exists():
                return False
        return True

    def is_valid_source(self, source_path: Path) -> bool:
        #TODO: need to check for loose files, project, or pak file
        return False

    def is_pak(self, source_path: Path) -> bool:
        #TODO: Need to decide how to determine if location is a pak file/contains pak file
        return False

    def unpack_file(self, source_path: Path) -> Path:
        #TODO: How to handle out dir?  generated temp location returned to caller?
        # self._unpack_internal(source_path, self.path_to_root / 'tmp')
        return self.path_to_root / 'tmp'

    def convert_stat_files(self, source_path: Path):
        print(f'{Fore.CYAN}[main] Converting Stats files:{Fore.RESET}')
        for file in source_path.rglob('*.txt'):
            if file.name in FORCE_FAIL:
                print(f'{Fore.YELLOW}[info] Skipped file: {file.name} (Reason: Not yet supported){Fore.RESET}')
                continue
            elif file.full_match('**/Mods/*/Story/**'):
                print(f'{Fore.YELLOW}[info] Skipped file: {file.name} (Reason: Osiris Script){Fore.RESET}')
                continue
            self._convert_internal(file, self._db['Stats'], self._stats_converter)

    def convert_lsx_files(self, source_path: Path):
        print(f'\n{Fore.CYAN}[main] Converting LSX files:{Fore.RESET}')
        for file in source_path.rglob('*.lsx'):
            if file.name in FORCE_FAIL:
                print(f'{Fore.YELLOW}[info] Skipped file: {file.name} (Reason: Not yet supported){Fore.RESET}')
                continue
            self._convert_internal(file, self._db['LSX'], self._lsx_converter)

    def fix_locales(self, source_path: Path):
        print(f'{Fore.CYAN}[main] Reviewing locale XML files:{Fore.RESET}')
        for file in source_path.rglob('*.xml'):
            if file.name[-8::] == '_fix.xml':
                continue
            if file.name in FORCE_FAIL:
                print(f'{Fore.YELLOW}[info] Skipped file: {file.name} (Reason: Not yet supported){Fore.RESET}')
                continue
            self._locale_fixer.fix(file, self._lsx_converter)

    def build_tk_project(self, source_path: Path, output_dir: Path, is_cli: bool = True):
        print(f'{Fore.CYAN}[main] Checking to construct tk project:{Fore.RESET}')
        projects = []

        for dir_path in source_path.iterdir():
            if dir_path.is_dir() and not dir_path in projects and self.is_project_dir(dir_path):
                projects.append(dir_path)

        self._proj_builder.build_all(projects, output_dir, is_cli)
    #endregion

    # region Private helper functions
    @staticmethod
    def _is_file_guid(file: str) -> bool:
        return len(file) == 36 and file[8:9:] == "-" and file[13:14:] == "-" and file[18:19:] == "-" and file[23:24:] == "-"

    def _get_auxiliary_db(self, src_bg3_path: str, compile_aux_db: bool) -> dict:
        try:
            if compile_aux_db:
                # Check if bg3 path valid
                if not Path(f"{src_bg3_path}/bin/bg3.exe").is_file():
                    raise FileNotFoundError('')

                compdb = CompileDB(src_bg3_path)
                print(f'{Fore.YELLOW}[config] bg3.exe found\n[db] Compiling auxiliary ID Database...{Fore.RESET}')
                return compdb.compileAuxiliaryDB()
            else:
                print(f'{Fore.YELLOW}[config] bg3.exe found\n[db] Loading auxiliary ID Database...{Fore.RESET}')
                with open(self.path_to_root / 'auxdb.json', encoding="utf-8") as aux_db_data:
                    return json.load(aux_db_data)
        except FileNotFoundError:
            return {}

    def _get_db(self) -> dict:
        with open(self.path_to_root / 'db.json', encoding="utf-8") as db_data:
            return json.load(db_data)

    def _convert_internal(self, file: Path, db: dict, converter) -> None:
        if file.name in EXCLUSIONS:
            return None
        try:
            fuuid = db.get(file.name.split('.')[0].replace('Spell_', ''), None)
            converter.setUUID(fuuid)
            chk = converter.convert(str(file))
            if chk:
                if fuuid is None:
                    print(f'{Fore.YELLOW}[info] Converted {file.name} (No UUID found: Incorrect filename){Fore.RESET}')
                else:
                    print(f'{Fore.GREEN}[info] Converted {file.name} (UUID: {fuuid}){Fore.RESET}')
        except Exception as e:
            if self._is_file_guid(file.name.split(".")[0]):
                print(f'{Fore.YELLOW}[info] Skipped file: {file.name} (Reason: Cannot convert binary){Fore.WHITE}')
            else:
                print(f'{Fore.RED}[info] Failed to convert {file.name}:\n\tError: {e}\n\tFile: {file}{Fore.RESET}')
        return None

    def _unpack_internal(self, source_file: Path, output_path: Path, verbose=True):
        if not self._lslib_dll.exists():
            if verbose:
                print(f'{Fore.RED}[lsf] Cant convert {source_file.name} (LSLib not found){Fore.RESET}')

        # Setting up lslib dll for use
        import pythonnet
        pythonnet.load('coreclr')
        import clr
        if not str(self._lslib_dll.parent.absolute()) in sys.path:
            sys.path.append(str(self._lslib_dll.parent.absolute()))

        print(sys.path)
        clr.AddReference("LSLib")  # type: ignore
        from LSLib.LS import Packager  # type: ignore

        packager = Packager()
        packager.UncompressPackage(str(source_file), str(output_path.absolute()))

        if verbose:
            print(f'{Fore.GREEN}[info] Unpacked {source_file.name} (Out dir) {str(output_path)}{Fore.RESET}')
    # endregion
