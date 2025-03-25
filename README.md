# bg3-convert2toolkit
Convert a third party Mod project to a Toolkit project<br>
For use when porting third party mods to the toolkit or when you lost your editor files.

run ``pip install -r requirements.txt`` to install the required libraries.

Put all files you want to convert into a folder named ``convert`` inside the root of the script.
You can also drop an entire project into it.

run ``py Convert2Toolkit.py`` to start conversion.

If you have missing ``Parent`` entries you can try adding your BG3 install path to ``settings.json`` as follows:<br>
``C:/any/folder/until/Baldurs Gate 3/``<br>
This will enable the converter to read all IDs from your BG3 installation and mods to try and recover them.

If you dropped an entire mod into the conversion folder it will try to setup a project to be used with the toolkit.<br>
If you get any errors about files not existing you probably need to <b>enable long path names</b>.<br>
After project conversion, just paste the contents of the newly created folder into your BG3 Data folder:<br>
``/convert/NewMod_uuid/`` -> ``/Baldurs Gate 3/Data/``<br>
You need to paste the <b>contents</b> of the new ``/NewMod_uuid/`` folder into your Data folder, not the folder itself.

You can also create merge requests to fix any issues or missing data types you come across.