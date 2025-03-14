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

If you get an error when converting:<br>
&emsp;The file format is either wrong or its a format I havent made compatible yet.<br>
&emsp;Icon Atlases are not supported and will throw an error.<br>
If you get an error after conversion inside the toolkit:<br>
&emsp;Post your toolkit error so I can fix it, this means some entry used a different data type than the usual or configured ones.

You can also create merge requests to fix these issues or missing data types.