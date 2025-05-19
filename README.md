# bg3-convert2toolkit
### Convert a third party Mod project to a Toolkit project
For use when porting third party mods to the toolkit or when you lost your editor files.

If you dropped an entire mod into the conversion folder it will try to set up a project to be used with the toolkit.

If you get any errors about files not existing you probably need to <b>enable long path names</b>.

If you have missing `Parent` entries you can try adding your BG3 install path to `settings.json` as follows: 

`C:/any/folder/until/Baldurs Gate 3/`

This will enable the converter to read all IDs from your BG3 installation and mods to try and recover them.

After project conversion, just paste the contents of the newly created folder into your BG3 Data folder:

`/convert/NewMod_uuid/` -> `/Baldurs Gate 3/Data/`

You need to paste the <b>contents</b> of the new `/NewMod_uuid/` folder into your Data folder, not the folder itself.


---
## File structure for project Stats conversion
If converting to a toolkit project, the generated data needs to conform to expected file names to be correctly
structured in the editor project.

Expected file names (note not all types may be supported currently)
```
\Public\[Modname]\Stats\Generated\
├── Data
│   ├── Armor.txt
│   ├── BloodTypes.txt
│   ├── Character.txt
│   ├── Crimes.lsx
│   ├── CriticalHitTypes.txt
│   ├── Data.txt
│   ├── Interrupt.txt
│   ├── ItemColor.txt
│   ├── ItemProgressionNames.txt
│   ├── ItemProgressionVisuals.txt
│   ├── Object.txt
│   ├── Passive.txt
│   ├── Requirements.txt
│   ├── Spell_Projectile.txt
│   ├── Spell_ProjectileStrike.txt
│   ├── Spell_Rush.txt
│   ├── Spell_Shout.txt
│   ├── Spell_Target.txt
│   ├── Spell_Teleportation.txt
│   ├── Spell_Throw.txt
│   ├── Spell_Wall.txt
│   ├── Spell_Zone.txt
│   ├── Status_BOOST.txt
│   ├── Status_DEACTIVATED.txt
│   ├── Status_DOWNED.txt
│   ├── Status_EFFECT.txt
│   ├── Status_FEAR.txt
│   ├── Status_HEAL.txt
│   ├── Status_INCAPACITATED.txt
│   ├── Status_INVISIBLE.txt
│   ├── Status_KNOCKED_DOWN.txt
│   ├── Status_POLYMORPHED.txt
│   ├── Status_SNEAKING.txt
│   ├── Weapon.txt
│   └── XPData.txt
├── CraftingStationsItemComboPreviewData.txt
├── Equipment.txt
├── ItemComboProperties.txt
├── ItemCombos.txt
├── ItemTypes.txt
├── ObjectCategoriesItemComboPreviewData.txt
├── SpellSet.txt
├── TreasureGroups.txt
├── TreasureTable.txt
```

---
## Settings
- `bg3path`
  - Path to BG3 installation
- `compileAux`
  - 0 or 1 to compile additional UUIDs from Editor projects<br>(recommended to set to 0 after running the first time or when needing to recompile)


---
## Running with python
run `pip install -r requirements.txt` to install the required libraries.

Put all files you want to convert into a folder named `convert` inside the root of the script.
You can also drop an entire project into it.

run `py Convert2Toolkit.py` to start conversion.


---
## Running the exe
- Download latest release, should contain Convert2Toolkit.exe, db.json, and settings.json
- Adjust settings as needed
- Create the `convert` directory in same location as the .exe
- Put all files/projects you want to convert into folder
- Run .exe


---
## Building the exe
- Make sure pyinstaller is installed: `pip install pyinstaller`
- From project dir run: `pyinstaller.exe --noconfirm .\Convert2Toolkit.spec`


---
## Future Features
- [ ] Add conversion for lsfx --> lsefx

- [ ] Add conversion for SpellSets.txt

- [X] Add conversion for Rulebooks.lsx

- [ ] Add support for direct conversion of pak files

- [ ] Add GUI version of converter


---
## Troubleshooting/Known Issues
- The game seems more relaxed than the toolkit in certain regards.  I observed while testing a case where a mod 
  defined multiple MultiEffectInfos in lsx with the **same** UUID.  The game seemed unconcerned, and the scripts
  were able to convert.  However, the toolkit MEI editor would crash unless I removed the duplicate.


---
## Contributing
You can also create merge requests to fix any issues or missing data types you come across.