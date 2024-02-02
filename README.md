# fmt_RE_MESH-Noesis-Plugin
A plugin for Rich Whitehouse's Noesis to import and export RE Engine meshes, textures and animations

## SUPPORTED GAMES
- Resident Evil 2 Remake
- Resident Evil 3 Remake
- Resident Evil 4 Remake
- Resident Evil 7 (Ray Tracing)
- Resident Evil 8
- Devil May Cry 5
- Monster Hunter Rise
- Street Fighter 6
- ExoPrimal
- Apollo Justice: Ace Attorney Trilogy


## INSTALLATION:
Download Noesis from here: https://www.richwhitehouse.com/index.php?content=inc_projects.php&showproject=91
Once it is installed, navigate to your [Noesis Installation Path]/plugins/python folder and put fmt_RE_MESH.py in there, and re-launch the program.
Opening a mesh or tex file with Noesis will automatically load it, once the plugin is installed. 


## NOESIS MAXSCRIPT:
To use the optional Noesis Maxscript (REEM Noesis CMD), you should edit the included .ms file to tell it where your Noesis.exe is. 
Then you can run the maxscript in 3dsMax with Scripts -> Run Script, and use it to remote-control Noesis as to seamlessly import and export with a GUI inside 3dsmax.


### Tips
- The plugin supports opening RE Engine SCN files. These files can contain a list of meshes at certain positions, constituting a stage or map
- The plugin saves the location of your extracted re_chunk_000.pak folder ("Base Directory") for each game in a txt file next to the plugin. Edit this file if it is not correct
- In the mesh/animation import window, double click ".." to go up a parent directory, or paste in a directory into the text box to go there
- You can load multiple meshes together in addition to the mesh you first selected. They and their bones will be merged together into the same model
- When loading a mesh, click the "Select Animation" button to load motlist animations with it, useful for quickly testing rigging


### For more info on REEM, check out this guide:
https://residentevilmodding.boards.net/thread/15374/noesis-maxscript-custom-physics-guide


### More Info on the plugin:
https://residentevilmodding.boards.net/thread/13501/exporting-custom-models-dmc5-noesis


### Credits
Thanks to Gh0stblade for creating the original version of this plugin in 2019


### Support
If you have issues with the plugin, create an issue here or join [Modding Haven](https://discord.gg/acCRqRyUB2) and message me on Discord