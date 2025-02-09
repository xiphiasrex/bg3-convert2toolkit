# bg3-lsx2tbl-converter
Convert LSX to TBL files<br>
For use when porting third party mods to the toolkit or when you lost your editor files.

run ``pip install -r requirements.txt`` to install the required libraries.

Put all files you want to convert into the folder of the script or vice versa and run it.

If you get an error when converting:<br>
&emsp;The file format is either not lsx or its a format I havent made compatible yet.<br>
If you get an error after conversion inside the toolkit:<br>
&emsp;Post your toolkit error so I can fix it, this means some entry used a different data type than the usual ones.

If the toolkit throws a ``stat_object_definition_id`` error, just copy that from a source file<br>
Example: Progressions.tbl -> ``stat_object_definition_id="53912403-fe14-4ce0-89aa-96acb1dee21a"``<br>
Im currently working on making this automatic.
