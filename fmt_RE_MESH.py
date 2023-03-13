#RE Engine [PC] - ".mesh" plugin for Rich Whitehouse's Noesis
#Authors: alphaZomega, Gh0stblade 
#Special thanks: Chrrox, SilverEzredes 
Version = "v3.12 (March 13, 2023)"

#Options: These are global options that change or enable/disable certain features

#Var												Effect
#Export Extensions
bRayTracingExport			= True					#Enable or disable the export of RE2R, RE3R and RE7 RayTracing meshes and textures
bRE2Export 					= True					#Enable or disable export of mesh.1808312334 and tex.10 from the export list			
bRE3Export 					= True					#Enable or disable export of mesh.1902042334 and tex.190820018 from the export list
bDMCExport 					= True					#Enable or disable export of mesh.1808282334 and tex.11 from the export list
bRE7Export 					= True					#Enable or disable export of mesh.32 and tex.8 from the export list
bREVExport 					= True					#Enable or disable export of mesh.2102020001 from the export list (and tex.31)
bRE8Export 					= True					#Enable or disable export of mesh.2101050001 from the export list (and tex.30)
bMHRiseExport 				= False					#Enable or disable export of mesh.2008058288 from the export list (and tex.28) 
bMHRiseSunbreakExport 		= True					#Enable or disable export of mesh.2109148288 from the export list (and tex.28)
bSF6Export					= True					#Enable or disable export of mesh.220721329 from the export list (and tex.36)
bRE4Export					= True					#Enable or disable export of mesh.221108797 from the export list (and tex.143221013)


#Mesh Global
fDefaultMeshScale 			= 100.0 				#Override mesh scale (default is 1.0)
bMaterialsEnabled 			= True					#Load MDF Materials
bRenderAsPoints 			= False					#Render mesh as points without triangles drawn (1 = on, 0 = off)
bImportAllLODs 				= False					#Imports all LODGroups (as separate models)

#Vertex Components (Import)
bNORMsEnabled 				= True					#Normals
bTANGsEnabled 				= True					#Tangents
bUVsEnabled 				= True					#UVs
bSkinningEnabled 			= True					#Enable skin weights
bColorsEnabled				= True					#Enable Vertex Colors
bDebugNormals 				= False					#Debug normals as RGBA
bDebugTangents 				= False					#Debug tangents as RGBA

#Import Options
bPrintMDF 					= False					#Prints debug info for MDF files
bDebugMESH 					= False					#Prints debug info for MESH files
bPopupDebug 				= True					#Pops up debug window on opening MESH with MDF
bPrintFileList 				= True					#Prints a list of files used by the MDF
bColorize 					= False					#Colors the materials of the model and lists which material is which color
bUseOldNamingScheme 		= False					#Names submeshes by their material ID (like in the MaxScript) rather than by their order in the file 
bRenameMeshesToFilenames 	= False					#For use with Noesis Model Merger. Renames submeshes to have their filenames in the mesh names
bImportMaterialNames		= True					#Imports material name data for each mesh, appending it to the end of each Submesh's name
bShorterNames				= True					#Imports meshes named like "LOD_1_Main_1_Sub_1" instead of "LODGroup_1_MainMesh_1_SubMesh_1"
bImportMips 				= False					#Imports texture mip maps as separate images
texOutputExt				= ".tga"				#File format used when linking FBX materials to images
doConvertMatsForBlender		= False					#Load alpha maps as reflection maps, metallic maps as specular maps and roughness maps as bump maps for use with modified Blender FBX importer

#Export Options
bNewExportMenu				= False					#Show a custom Noesis window on mesh export
bAlwaysRewrite				= False					#Always try to rewrite the meshfile on export
bAlwaysWriteBones			= False					#Always write new skeleton to mesh
bNormalizeWeights 			= False					#Makes sure that the weights of every vertex add up to 1.0, giving the remainder to the bone with the least influence
bCalculateBoundingBoxes		= True					#Calculates the bounding box for each bone
BoundingBoxSize				= 1.0					#With bCalculateBoundingBoxes False, change the size of the bounding boxes created for each rigged bone when exporting with -bones or -rewrite
bRigToCoreBones				= False					#Assign non-matching bones to the hips and spine, when exporting a mesh without -bones or -rewrite
bSetNumModels				= True					#Sets the header byte "NumModels" to defaults when exporting without -rewrite, preventing crashes
bForceRootBoneToBone0		= True					#If the root bone is detected as the last bone in the bones list, this will move it to be the first bone in the list

#Import/Export:
bAddBoneNumbers 			= 2						#Adds bone numbers and colons before bone names to indicate if they are active. 0 = Off, 1 = On, 2 = Auto
bRotateBonesUpright			= False					#Rotates bones to be upright for editing and then back to normal for exporting
bReadGroupIds				= True					#Import/Export with the GroupID as the MainMesh number

from inc_noesis import *
from collections import namedtuple
import noewin
import math
import os
import re
import copy
import time

def registerNoesisTypes():

	def addOptions(handle):
		noesis.setTypeExportOptions(handle, "-noanims -notex")
		noesis.addOption(handle, "-bones", "Write new skeleton on export", 0)
		noesis.addOption(handle, "-rewrite", "Rewrite submeshes and materials structure", 0)
		noesis.addOption(handle, "-flip", "Reverse handedness from DirectX to OpenGL", 0)
		noesis.addOption(handle, "-bonenumbers", "Add bone numbers to imported bones", 0)
		noesis.addOption(handle, "-meshfile", "Export using a given source mesh filename", noesis.OPTFLAG_WANTARG)
		noesis.addOption(handle, "-b", "Run as a batch process", 0)
		noesis.addOption(handle, "-adv", "Show Advanced Export Options window", 0)
		noesis.addOption(handle, "-vfx", "Export as VFX mesh", 0)
		return handle
		
	handle = noesis.register("RE Engine MESH [PC]", ".1902042334;.1808312334;.1808282334;.2008058288;.2102020001;.2101050001;.2109108288;.2109148288;.220128762;.220301866;.220721329;.221108797;.NewMesh")
	noesis.setHandlerTypeCheck(handle, meshCheckType)
	noesis.setHandlerLoadModel(handle, meshLoadModel)
	noesis.addOption(handle, "-noprompt", "Do not prompt for MDF file", 0)
	noesis.setTypeSharedModelFlags(handle, (noesis.NMSHAREDFL_WANTGLOBALARRAY))
	
	handle = noesis.register("RE Engine Texture [PC]", ".10;.190820018;.11;.8;.28;.stm;.30;.31;.34;.35;.36;.143221013")
	noesis.setHandlerTypeCheck(handle, texCheckType)
	noesis.setHandlerLoadRGBA(handle, texLoadDDS)

	handle = noesis.register("RE Engine UVS [PC]", ".5;.7")
	noesis.setHandlerTypeCheck(handle, UVSCheckType)
	noesis.setHandlerLoadModel(handle, UVSLoadModel)
	
	handle = noesis.register("RE Engine SCN [PC]", ".19;.20")
	noesis.setHandlerTypeCheck(handle, SCNCheckType)
	noesis.setHandlerLoadModel(handle, SCNLoadModel)
	
	handle = noesis.register("RE Engine MOTLIST [PC]", ".60;.85;.99;.484;.486;.524;.528;.653;.663")
	noesis.setHandlerTypeCheck(handle, motlistCheckType)
	noesis.setHandlerLoadModel(handle, motlistLoadModel)

	if bRE2Export:
		handle = noesis.register("RE2 Remake Texture [PC]", ".10")
		noesis.setHandlerWriteRGBA(handle, texWriteRGBA)
		handle = noesis.register("RE2 MESH", (".1808312334"))
		noesis.setHandlerTypeCheck(handle, meshCheckType)
		noesis.setHandlerWriteModel(handle, meshWriteModel)
		addOptions(handle)
		
	if bRE3Export:
		handle = noesis.register("RE3 Remake Texture [PC]", ".190820018")
		noesis.setHandlerWriteRGBA(handle, texWriteRGBA)
		handle = noesis.register("RE3 MESH", (".1902042334"))
		noesis.setHandlerTypeCheck(handle, meshCheckType)
		noesis.setHandlerWriteModel(handle, meshWriteModel)
		addOptions(handle)
	
	#fbxskel export is disabled
	#handle = noesis.register("fbxskel", (".fbxskel.3")) 
	#noesis.setHandlerWriteModel(handle, skelWriteFbxskel)
	#noesis.setTypeExportOptions(handle, "-noanims -notex")
		
	if bDMCExport:
		handle = noesis.register("Devil May Cry 5 Texture [PC]", ".11")
		noesis.setHandlerTypeCheck(handle, texCheckType)
		noesis.setHandlerWriteRGBA(handle, texWriteRGBA)
		handle = noesis.register("DMC5 MESH", (".1808282334"))
		noesis.setHandlerTypeCheck(handle, meshCheckType)
		noesis.setHandlerWriteModel(handle, meshWriteModel)
		addOptions(handle)
		
	if bREVExport or bRE8Export:
		handle = noesis.register("RE8 / ReVerse Texture [PC]", ".30")
		noesis.setHandlerTypeCheck(handle, texCheckType)
		noesis.setHandlerWriteRGBA(handle, texWriteRGBA);
		
	if bREVExport:
		handle = noesis.register("ReVerse MESH", (".2102020001"))
		noesis.setHandlerTypeCheck(handle, meshCheckType)
		noesis.setHandlerWriteModel(handle, meshWriteModel)
		addOptions(handle)
		
	if bRE8Export:
		handle = noesis.register("RE8 MESH", (".2101050001"))
		noesis.setHandlerTypeCheck(handle, meshCheckType)
		noesis.setHandlerWriteModel(handle, meshWriteModel)
		addOptions(handle)
		
	if bMHRiseExport or bMHRiseSunbreakExport:
		handle = noesis.register("MHRise Texture [PC]", ".28;.stm")
		noesis.setHandlerTypeCheck(handle, texCheckType)
		noesis.setHandlerWriteRGBA(handle, texWriteRGBA);
		if bMHRiseExport:
			handle = noesis.register("MHRise MESH", (".2008058288"))
			noesis.setHandlerTypeCheck(handle, meshCheckType)
			noesis.setHandlerWriteModel(handle, meshWriteModel)
			addOptions(handle)
		if bMHRiseSunbreakExport:
			handle = noesis.register("MHRise Sunbreak MESH", (".2109148288"))
			noesis.setHandlerTypeCheck(handle, meshCheckType)
			noesis.setHandlerWriteModel(handle, meshWriteModel)
			addOptions(handle)
		
	if bRE7Export:
		handle = noesis.register("Resident Evil 7 Texture [PC]", ".8")
		noesis.setHandlerTypeCheck(handle, texCheckType)
		noesis.setHandlerWriteRGBA(handle, texWriteRGBA)
		#RE7 MESH support is disabled for this version
		
	if bRayTracingExport:
		handle = noesis.register("RE2,3 RayTracing Texture [PC]", ".34")
		noesis.setHandlerTypeCheck(handle, texCheckType)
		noesis.setHandlerWriteRGBA(handle, texWriteRGBA);
		handle = noesis.register("RE7 RayTracing Texture [PC]", ".35")
		noesis.setHandlerTypeCheck(handle, texCheckType)
		noesis.setHandlerWriteRGBA(handle, texWriteRGBA);
		handle = noesis.register("RE2+3 RayTracing MESH", (".2109108288"))
		noesis.setHandlerTypeCheck(handle, meshCheckType)
		noesis.setHandlerWriteModel(handle, meshWriteModel)
		addOptions(handle)
		handle = noesis.register("RE7 RayTracing MESH", (".220128762"))
		noesis.setHandlerTypeCheck(handle, meshCheckType)
		noesis.setHandlerWriteModel(handle, meshWriteModel)
		addOptions(handle)
	
	if bSF6Export:
		handle = noesis.register("Street Fighter 6 Texture [PC]", ".36")
		noesis.setHandlerTypeCheck(handle, texCheckType)
		noesis.setHandlerWriteRGBA(handle, texWriteRGBA);
		handle = noesis.register("Street Fighter 6 Mesh", (".220721329"))
		noesis.setHandlerTypeCheck(handle, meshCheckType)
		noesis.setHandlerWriteModel(handle, meshWriteModel)
		addOptions(handle)
		
	if bRE4Export:
		handle = noesis.register("RE4 Remake Texture [PC]", ".143221013")
		noesis.setHandlerTypeCheck(handle, texCheckType)
		noesis.setHandlerWriteRGBA(handle, texWriteRGBA);
		handle = noesis.register("RE4 Remake Mesh", (".221108797"))
		noesis.setHandlerTypeCheck(handle, meshCheckType)
		noesis.setHandlerWriteModel(handle, meshWriteModel)
		addOptions(handle)
		
	noesis.logPopup()
	return 1
		
#Default global variables for internal use:
sGameName = "RE2"
sExportExtension = ".1808312334"
bWriteBones = False
bDoVFX = False
bReWrite = False
openOptionsDialog = None
w1 = 127
w2 = -128

formats = {
	"RE7":			{ "modelExt": ".-1", 		 "texExt": ".8", 		 "mmtrExt": ".69", 		   "nDir": "x64", "mdfExt": ".mdf2.6",  "meshVersion": 0, "mdfVersion": 0, "mlistExt": ".60" },
	"RE2":			{ "modelExt": ".1808312334", "texExt": ".10",		 "mmtrExt": ".1808160001", "nDir": "x64", "mdfExt": ".mdf2.10", "meshVersion": 1, "mdfVersion": 1, "mlistExt": ".85" },
	"DMC5":			{ "modelExt": ".1808282334", "texExt": ".11", 		 "mmtrExt": ".1808168797", "nDir": "x64", "mdfExt": ".mdf2.10", "meshVersion": 1, "mdfVersion": 1, "mlistExt": ".85" },
	"RE3": 			{ "modelExt": ".1902042334", "texExt": ".190820018", "mmtrExt": ".1905100741", "nDir": "stm", "mdfExt": ".mdf2.13", "meshVersion": 1, "mdfVersion": 2, "mlistExt": ".99" },
	"RE8": 			{ "modelExt": ".2101050001", "texExt": ".30", 		 "mmtrExt": ".2102188797", "nDir": "stm", "mdfExt": ".mdf2.19", "meshVersion": 2, "mdfVersion": 3, "mlistExt": ".486" },
	"MHRise":		{ "modelExt": ".2008058288", "texExt": ".28", 		 "mmtrExt": ".2109301553", "nDir": "stm", "mdfExt": ".mdf2.19", "meshVersion": 2, "mdfVersion": 3, "mlistExt": ".484" },
	"MHRSunbreak":	{ "modelExt": ".2109148288", "texExt": ".28", 		 "mmtrExt": ".220427553",  "nDir": "stm", "mdfExt": ".mdf2.23", "meshVersion": 2, "mdfVersion": 3, "mlistExt": ".528" },
	"ReVerse":		{ "modelExt": ".2102020001", "texExt": ".31", 		 "mmtrExt": ".2108110001", "nDir": "stm", "mdfExt": ".mdf2.20", "meshVersion": 2, "mdfVersion": 3, "mlistExt": ".486" },
	"RERT": 		{ "modelExt": ".2109108288", "texExt": ".34", 		 "mmtrExt": ".2109101635", "nDir": "stm", "mdfExt": ".mdf2.21", "meshVersion": 2, "mdfVersion": 3, "mlistExt": ".524" },
	"RE7RT": 		{ "modelExt": ".220128762",  "texExt": ".35", 		 "mmtrExt": ".2109101635", "nDir": "stm", "mdfExt": ".mdf2.21", "meshVersion": 2, "mdfVersion": 3, "mlistExt": ".524" },
	"SF6": 			{ "modelExt": ".220721329",  "texExt": ".36", 		 "mmtrExt": ".220720447",  "nDir": "stm", "mdfExt": ".mdf2.31", "meshVersion": 3, "mdfVersion": 4, "mlistExt": ".653" },
	"ExoPrimal": 	{ "modelExt": ".220721329",  "texExt": ".36", 		 "mmtrExt": ".220720447",  "nDir": "stm", "mdfExt": ".mdf2.31", "meshVersion": 3, "mdfVersion": 4, "mlistExt": ".653" },
	"RE4": 			{ "modelExt": ".221108797",  "texExt": ".143221013", "mmtrExt": ".221007879",  "nDir": "stm", "mdfExt": ".mdf2.32", "meshVersion": 3, "mdfVersion": 4, "mlistExt": ".663" },
}

extToFormat = { #incomplete, just testing
	"10": {
		"albm":   [99,5],
		"albmsc": [99,5],
		"alba":	  [99,1],
		"alb":    [72,0],
		"nrmr":   [98,6],
		"nrm":	  [98,1],
		"iam":	  [99,8],
		"atos":   [71,4],
		"msk1":   [80,3],
	},
	"34": {
		"albm":   [99,5],
		"albmsc": [99,5],
		"alba":	  [99,1],
		"alb":    [72,0],
		"nrmr":   [98,6],
		"nrm":	  [98,1],
		"iam":	  [99,8],
		"atos":   [71,4],
		"msk1":   [80,3],
	},
}
extToFormat["8"] = extToFormat["10"]
extToFormat["11"] = extToFormat["10"]
extToFormat["190820018"] = extToFormat["10"]
extToFormat["30"] = extToFormat["34"]
extToFormat["35"] = extToFormat["34"]
extToFormat["28"] = extToFormat["34"]
extToFormat["143221013"] = extToFormat["34"]
extToFormat["28.stm"] = extToFormat["28"]


tex_format_list = {
	0: "UNKNOWN",
	1: "R32G32B32A32_TYPELESS",
	2: "R32G32B32A32_FLOAT",
	3: "R32G32B32A32_UINT",
	4: "R32G32B32A32_SINT",
	5: "R32G32B32_TYPELESS",
	6: "R32G32B32_FLOAT",
	7: "R32G32B32_UINT",
	8: "R32G32B32_SINT",
	9: "R16G16B16A16_TYPELESS",
	10: "R16G16B16A16_FLOAT",
	11: "R16G16B16A16_UNORM",
	12: "R16G16B16A16_UINT",
	13: "R16G16B16A16_SNORM",
	14: "R16G16B16A16_SINT",
	15: "R32G32_TYPELESS",
	16: "R32G32_FLOAT",
	17: "R32G32_UINT",
	18: "R32G32_SINT",
	19: "R32G8X24_TYPELESS",
	20: "D32_FLOAT_S8X24_UINT",
	21: "R32_FLOAT_X8X24_TYPELESS",
	22: "X32_TYPELESS_G8X24_UINT",
	23: "R10G10B10A2_TYPELESS",
	24: "R10G10B10A2_UNORM",
	25: "R10G10B10A2_UINT",
	26: "R11G11B10_FLOAT",
	27: "R8G8B8A8_TYPELESS",
	28: "R8G8B8A8_UNORM",
	29: "R8G8B8A8_UNORM_SRGB",
	30: "R8G8B8A8_UINT",
	31: "R8G8B8A8_SNORM",
	32: "R8G8B8A8_SINT",
	33: "R16G16_TYPELESS",
	34: "R16G16_FLOAT",
	35: "R16G16_UNORM",
	36: "R16G16_UINT",
	37: "R16G16_SNORM",
	38: "R16G16_SINT",
	39: "R32_TYPELESS",
	40: "D32_FLOAT",
	41: "R32_FLOAT",
	42: "R32_UINT",
	43: "R32_SINT",
	44: "R24G8_TYPELESS",
	45: "D24_UNORM_S8_UINT",
	46: "R24_UNORM_X8_TYPELESS",
	47: "X24_TYPELESS_G8_UINT",
	48: "R8G8_TYPELESS",
	49: "R8G8_UNORM",
	50: "R8G8_UINT",
	51: "R8G8_SNORM",
	52: "R8G8_SINT",
	53: "R16_TYPELESS",
	54: "R16_FLOAT",
	55: "D16_UNORM",
	56: "R16_UNORM",
	57: "R16_UINT",
	58: "R16_SNORM",
	59: "R16_SINT",
	60: "R8_TYPELESS",
	61: "R8_UNORM",
	62: "R8_UINT",
	63: "R8_SNORM",
	64: "R8_SINT",
	65: "A8_UNORM",
	66: "R1_UNORM",
	67: "R9G9B9E5_SHAREDEXP",
	68: "R8G8_B8G8_UNORM",
	69: "G8R8_G8B8_UNORM",
	70: "BC1_TYPELESS",
	71: "BC1_UNORM",
	72: "BC1_UNORM_SRGB",
	73: "BC2_TYPELESS",
	74: "BC2_UNORM",
	75: "BC2_UNORM_SRGB",
	76: "BC3_TYPELESS",
	77: "BC3_UNORM",
	78: "BC3_UNORM_SRGB",
	79: "BC4_TYPELESS",
	80: "BC4_UNORM",
	81: "BC4_SNORM",
	82: "BC5_TYPELESS",
	83: "BC5_UNORM",
	84: "BC5_SNORM",
	85: "B5G6R5_UNORM",
	86: "B5G5R5A1_UNORM",
	87: "B8G8R8A8_UNORM",
	88: "B8G8R8X8_UNORM",
	89: "R10G10B10_XR_BIAS_A2_UNORM",
	90: "B8G8R8A8_TYPELESS",
	91: "B8G8R8A8_UNORM_SRGB",
	92: "B8G8R8X8_TYPELESS",
	93: "B8G8R8X8_UNORM_SRGB",
	94: "BC6H_TYPELESS",
	95: "BC6H_UF16",
	96: "BC6H_SF16",
	97: "BC7_TYPELESS",
	98: "BC7_UNORM",
	99: "BC7_UNORM_SRGB",
	100: "AYUV",
	101: "Y410",
	102: "Y416",
	103: "NV12",
	104: "P010",
	105: "P016",
	106: "_420_OPAQUE",
	107: "YUY2",
	108: "Y210",
	109: "Y216",
	110: "NV11",
	111: "AI44",
	112: "IA44",
	113: "P8",
	114: "A8P8",
	115: "B4G4R4A4_UNORM",
	130: "P208",
	131: "V208",
	132: "V408",
	0xffffffff:  "FORCE_UINT" 
}

def sort_human(List):
	convert = lambda text: float(text) if text.isdigit() else text
	return sorted(List, key=lambda mesh: [convert(c) for c in re.split('([-+]?[0-9]*\.?[0-9]*)', mesh.name)])

def meshCheckType(data):
	bs = NoeBitStream(data)
	magic = bs.readUInt()
	
	if magic == 0x4853454D:
		return 1
	else: 
		print("Fatal Error: Unknown file magic: " + str(hex(magic) + " expected 'MESH'!"))
		return 0

def texCheckType(data):
	bs = NoeBitStream(data)
	magic = bs.readUInt()
	if magic == 0x00584554:
		return 1
	else: 
		print("Fatal Error: Unknown file magic: " + str(hex(magic) + " expected TEX!"))
		return 0

def UVSCheckType(data):
	bs = NoeBitStream(data)
	magic = bs.readUInt()
	if magic == 1431720750:
		return 1
	else: 
		print("Fatal Error: Unknown file magic: " + str(hex(magic) + " expected ' SVU'!"))
		return 0
		
def readUIntAt(bs, readAt):
	pos = bs.tell()
	bs.seek(readAt)
	value = bs.readUInt()
	bs.seek(pos)
	return value
	
def readUShortAt(bs, tell):
	pos = bs.tell()
	bs.seek(tell)
	out = bs.readUShort()
	bs.seek(pos)
	return out
	
def readUByteAt(bs, tell):
	pos = bs.tell()
	bs.seek(tell)
	out = bs.readUByte()
	bs.seek(pos)
	return out

def ReadUnicodeString(bs):
	numZeroes = 0
	resultString = ""
	while(numZeroes < 2):
		c = bs.readUByte()
		if c == 0:
			numZeroes+=1
			continue
		else:
			numZeroes = 0
		resultString += chr(c)
	return resultString

def readUnicodeStringAt(bs, tell):
	string = []
	pos = bs.tell()
	bs.seek(tell)
	while(readUShortAt(bs, bs.tell()) != 0):
		string.append(bs.readByte())
		bs.seek(1,1)
	bs.seek(pos)
	buff = struct.pack("<" + 'b'*len(string), *string)
	return str(buff, 'utf-8')
		
def GetRootGameDir(path=""):
	path = rapi.getDirForFilePath(path or rapi.getInputName())
	while len(path) > 3:
		lastFolderName = os.path.basename(os.path.normpath(path)).lower()
		if lastFolderName == "stm" or lastFolderName == "x64":
			break
		else:
			path = os.path.normpath(os.path.join(path, ".."))
	return path	+ "\\"
	
def LoadExtractedDir(gameName=None):
	gameName = gameName or sGameName
	nativesPath = ""
	try: 
		with open(noesis.getPluginsPath() + '\python\\' + gameName + 'NativesPath.txt') as fin:
			nativesPath = fin.read()
			fin.close()
	except IOError:
		pass
	if not os.path.isdir(nativesPath):
		return ""
	return nativesPath	
		
def SaveExtractedDir(dirIn, gameName=None):
	gameName = gameName or sGameName
	try: 
		print (noesis.getPluginsPath() + 'python\\' + gameName + 'NativesPath.txt')
		with open(noesis.getPluginsPath() + 'python\\' + gameName + 'NativesPath.txt', 'w') as fout:
			print ("Writing string: " + dirIn + " to " + noesis.getPluginsPath() + 'python\\' + gameName + 'NativesPath.txt')
			fout.flush()
			fout.write(str(dirIn))
			fout.close()
	except IOError:
		print ("Failed to save natives path: IO Error")
		return 0
	return 1
	
def findRootDir(path):
	idx = path.find("\\natives\\")
	if idx != -1:
		return path[:(idx + 9)]
	return path
	
def getGlobalMatrix(noebone, bonesList): #doesnt work 100%?
	mat = noebone.getMatrix()
	parent = bonesList[noebone.parentIndex] if noebone.parentIndex != -1 else None
	if parent:
		mat *= parent.getMatrix().inverse()
	return mat.transpose()
	
def getChildBones(parentBone, boneList, doRecurse=False):
	children = []
	for bone in boneList:
		if bone.parentName == parentBone.name and bone not in children:
			children.append(bone)
			if doRecurse:
				children.extend(getChildBones(bone, boneList, True))
			break
	return children
	
def cleanBoneName(name):
	splitted = name.split(":", 1)
	return splitted[len(splitted)-1]

def generateBoneMap(mdl):
	usedBones = [False for bone in mdl.bones]
	boneNames = [bone.name.lower() for bone in mdl.bones]
	boneMapCount = 0
	for bone in mdl.bones:
		if bone.parentIndex != -1 and bone.parentName:
			bone.parentIndex = boneNames.index(bone.parentName.lower())
	for mesh in mdl.meshes:
		for weightList in mesh.weights:
			for idx in weightList.indices:
				usedBones[idx] = True
	for i, bone in enumerate(mdl.bones):
		bone.name = cleanBoneName(bone.name)
		if usedBones[i]:
			bone.name = "b" + "{:03d}".format(boneMapCount) + ":" + bone.name
			boneMapCount += 1
	for bone in mdl.bones:
		if bone.parentIndex != -1:
			bone.parentName = mdl.bones[bone.parentIndex].name

def collapseBones(mdl, threshold=0.01):
	print("Collapsing skeleton")
	newBones = []
	newBoneMap = []
	newBoneMapNames = []
	allBoneNames = [cleanBoneName(bone.name).lower() for bone in mdl.bones]
	for i, bone in enumerate(mdl.bones):
		boneMapId = i
		name = allBoneNames[i].split(".", 1)[0]
		sameBoneIdx = allBoneNames.index(name)
		#if sameBoneIdx != i and (getGlobalMatrix(mdl.bones[sameBoneIdx], mdl.bones)[3] - getGlobalMatrix(bone, mdl.bones)[3]).length() < threshold * fDefaultMeshScale:
		if sameBoneIdx != i: # and (mdl.bones[sameBoneIdx].getMatrix()[3] - bone.getMatrix()[3]).length() < threshold * fDefaultMeshScale:
			boneMapId = sameBoneIdx
		elif bone.parentIndex != bone.index:
			newBones.append(bone)
		newBoneMapNames.append(mdl.bones[boneMapId].name.lower())
	for i, bone in enumerate(newBones):
		bone.index = i
		if bone.parentIndex != -1:
			mat = bone.getMatrix() * mdl.bones[bone.parentIndex].getMatrix().inverse()
			bone.parentName = newBoneMapNames[bone.parentIndex]
			bone.setMatrix(mat * mdl.bones[allBoneNames.index(bone.parentName)].getMatrix()) #relocate bone
		elif i > 0:
			bone.parentName = newBones[0].name
	newBoneNames = [bone.name.lower() for bone in newBones]
	for i, boneName in enumerate(newBoneMapNames):
		newBoneMap.append(newBoneNames.index(boneName))
	for mesh in mdl.meshes:
		for weightList in mesh.weights:
			weightList.indices = list(weightList.indices)
			for i, idx in enumerate(weightList.indices):
				weightList.indices[i] = newBoneMap[idx]
	'''for anim in mdl.anims:
		anim.bones = newBones
		for kfBone in anim.kfBones:
			kfBone.boneIndex = newBoneMap[kfBone.boneIndex]'''
			
	mdl.setBones(newBones)
	
def recombineNoesisMeshes(mdl):
	
	meshesBySourceName = {}
	for mesh in mdl.meshes:
		meshesBySourceName[mesh.sourceName] = meshesBySourceName.get(mesh.sourceName) or []
		meshesBySourceName[mesh.sourceName].append(mesh)
		
	combinedMeshes = []
	for sourceName, meshList in meshesBySourceName.items():
		newPositions = []
		newUV1 = []
		newUV2 = []
		newUV3 = []
		newTangents = []
		newWeights = []
		newIndices = []
		newColors = []
		for mesh in meshList:
			tempIndices = []
			for index in mesh.indices:
				tempIndices.append(index + len(newPositions))
			newPositions.extend(mesh.positions)
			newUV1.extend(mesh.uvs)
			newUV2.extend(mesh.lmUVs)
			newUV3.extend(mesh.uvxList[0] if len(mesh.uvxList) > 0 else [])
			newColors.extend(mesh.colors)
			newTangents.extend(mesh.tangents)
			newWeights.extend(mesh.weights)
			newIndices.extend(tempIndices)
			
		combinedMesh = NoeMesh(newIndices, newPositions, meshList[0].sourceName, meshList[0].sourceName, mdl.globalVtx, mdl.globalIdx)
		combinedMesh.setTangents(newTangents)
		combinedMesh.setWeights(newWeights)
		combinedMesh.setUVs(newUV1)
		combinedMesh.setUVs(newUV2, 1)
		combinedMesh.setUVs(newUV3, 2)
		combinedMesh.setColors(newColors)
		if len(combinedMesh.positions) > 65535:
			print("Warning: Mesh exceeds the maximum of 65535 vertices (has", str(len(combinedMesh.positions)) + "):\n	", combinedMesh.name)
		else:
			combinedMeshes.append(combinedMesh)
		
	return combinedMeshes

#murmur3 hash algorithm, credit to Darkness for adapting this:
def hash(key, getUnsigned=False):
	
	seed = 0xffffffff
	key = bytearray(key, 'utf8')

	def fmix(h):
		h ^= h >> 16
		h = (h * 0x85ebca6b) & 0xFFFFFFFF
		h ^= h >> 13
		h = (h * 0xc2b2ae35) & 0xFFFFFFFF
		h ^= h >> 16
		return h

	length = len(key)
	nblocks = int(length / 4)

	h1 = seed

	c1 = 0xcc9e2d51
	c2 = 0x1b873593

	for block_start in range(0, nblocks * 4, 4):
		k1 = key[block_start + 3] << 24 | \
			 key[block_start + 2] << 16 | \
			 key[block_start + 1] << 8 | \
			 key[block_start + 0]

		k1 = (c1 * k1) & 0xFFFFFFFF
		k1 = (k1 << 15 | k1 >> 17) & 0xFFFFFFFF
		k1 = (c2 * k1) & 0xFFFFFFFF

		h1 ^= k1
		h1 = (h1 << 13 | h1 >> 19) & 0xFFFFFFFF
		h1 = (h1 * 5 + 0xe6546b64) & 0xFFFFFFFF

	tail_index = nblocks * 4
	k1 = 0
	tail_size = length & 3

	if tail_size >= 3:
		k1 ^= key[tail_index + 2] << 16
	if tail_size >= 2:
		k1 ^= key[tail_index + 1] << 8
	if tail_size >= 1:
		k1 ^= key[tail_index + 0]

	if tail_size > 0:
		k1 = (k1 * c1) & 0xFFFFFFFF
		k1 = (k1 << 15 | k1 >> 17) & 0xFFFFFFFF
		k1 = (k1 * c2) & 0xFFFFFFFF
		h1 ^= k1

	unsigned_val = fmix(h1 ^ length)
	if getUnsigned or unsigned_val & 0x80000000 == 0:
		return unsigned_val
	else:
		return -((unsigned_val ^ 0xFFFFFFFF) + 1)

def hash_wide(key, getUnsigned=False):
    key_temp = ''
    for char in key:
        key_temp += char + '\x00'
    return hash(key_temp, getUnsigned)
	
def forceFindTexture(FileName, startExtension=""):
	global sGameName
	for i in range(8):
		if i == 0:
			if startExtension != "":
				ext = startExtension
			else:
				sGameName = "RE2"
				ext = ".10"
		elif i == 1:
			sGameName == "RERT"
			ext = ".34"
		elif i == 2:
			sGameName == "RERT"
			ext = ".35"
		elif i == 3:
			sGameName = "RE3"
			ext = ".190820018"
		elif i == 4:
			sGameName = "RE7"
			ext = ".8"
		elif i == 5:
			sGameName = "RE8"
			ext = ".30"
		elif i == 6:
			sGameName = "DMC5"
			ext = ".11"
		elif i == 7:
			sGameName = "MHRise"
			ext = ".28"
		elif i == 8:
			sGameName = "ReVerse"
			ext = ".30"

		texFile = LoadExtractedDir() + FileName + ext
		#print ("texFile:", texFile)
		if rapi.checkFileExists(texFile):
			return texFile, ext
			
	return 0, 0

def readTextureData(texData, mipWidth, mipHeight, format):
	
	fmtName = tex_format_list[format] if format in tex_format_list else ""
	
	if format == 71 or format == 72: #ATOS
		texData = rapi.imageDecodeDXT(texData, mipWidth, mipHeight, noesis.FOURCC_DXT1)
	elif format == 77 or format == 78 or fmtName.find("BC3") != -1: #BC3
		texData = rapi.imageDecodeDXT(texData, mipWidth, mipHeight, noesis.FOURCC_BC3)
	elif format == 80 or fmtName.find("BC4") != -1: #BC4 wetmasks
		texData = rapi.imageDecodeDXT(texData, mipWidth, mipHeight, noesis.FOURCC_BC4)
	elif format == 83 or fmtName.find("BC5") != -1: #BC5
		texData = rapi.imageDecodeDXT(texData, mipWidth, mipHeight, noesis.FOURCC_BC5)
		texData = rapi.imageEncodeRaw(texData, mipWidth, mipHeight, "r16g16")
		texData = rapi.imageDecodeRaw(texData, mipWidth, mipHeight, "r16g16")
	elif format == 95 or format == 96 or fmtName.find("BC6") != -1:
		texData = rapi.imageDecodeDXT(texData, mipWidth, mipHeight, noesis.FOURCC_BC6H)
	elif format == 98 or format == 99 or fmtName.find("BC7") != -1:
		texData = rapi.imageDecodeDXT(texData, mipWidth, mipHeight, noesis.FOURCC_BC7)
	elif re.search("[RB]\d\d?", fmtName):
		fmtName = fmtName.split("_")[0].lower()
		texData = rapi.imageDecodeRaw(texData, mipWidth, mipHeight, fmtName)
	else:
		print("Fatal Error: Unsupported texture type: " + str(format))
		return 0
	#print("Detected texture format:", fmtName)
	return texData, fmtName


def isImageBlank(imgData, width=None, height=None, threshold=1):
	first = imgData[0]
	if width and height and width * height > 4096:
		imgData = rapi.imageResample(imgData, width, height, 64, 64)
	for i, b in enumerate(imgData):
		if (i+1) % 4 != 0 and abs(b - first) > threshold: #skip alpha
			return False
	return True
	
def invertRawRGBAChannel(imgData, channelID, bpp=4):
	for i in range(int(len(imgData)/4)):
		imgData[i*4+channelID] = 255 - imgData[i*4+channelID]
	return imgData

def moveChannelsRGBA(sourceBytes, sourceChannel, sourceWidth, sourceHeight, targetBytes, targetChannels, targetWidth, targetHeight):
	outputTargetBytes = copy.copy(targetBytes)
	if sourceBytes == targetBytes and sourceChannel >= 0:
		for ch in targetChannels:
			outputTargetBytes = rapi.imageCopyChannelRGBA32(outputTargetBytes, sourceChannel, ch)
	else:
		resizedSourceBytes = rapi.imageResample(sourceBytes, sourceWidth, sourceHeight, targetWidth, targetHeight)
		nullValue = 1 if sourceChannel == -1 else 255 if sourceChannel == -2 else None
		for i in range(int(len(resizedSourceBytes)/16)):
			for b in range(4):
				for ch in targetChannels:
					outputTargetBytes[i*16 + b*4 + ch] = nullValue or resizedSourceBytes[i*16 + b*4 + sourceChannel]
	return outputTargetBytes

def generateDummyTexture4px(rgbaColor, name="Dummy"):
	imageByteList = []
	for i in range(16):
		imageByteList.extend(rgbaColor)
	imageData = struct.pack("<" + 'B'*len(imageByteList), *imageByteList)
	imageData = rapi.imageDecodeRaw(imageData, 4, 4, "r8g8b8a8")
	return NoeTexture(name, 4, 4, imageData, noesis.NOESISTEX_RGBA32)	

def texLoadDDS(data, texList, texName=""):
	texName = texName or rapi.getInputName()
	bs = NoeBitStream(data)
	magic = bs.readUInt()
	version = bs.readUInt()
	width = bs.readUShort()
	height = bs.readUShort()
	unk00 = bs.readUShort()
	if version == 190820018:
		version = 10
	if version == 143221013:
		version = 36
	
	if version > 27:
		numImages = bs.readUByte()
		oneImgMipHdrSize = bs.readUByte()
		mipCount = int(oneImgMipHdrSize / 16)
	else:
		mipCount = bs.readUByte()
		numImages = bs.readUByte()
	
	format = bs.readUInt()
	unk02 = bs.readUInt()
	unk03 = bs.readUInt()
	unk04 = bs.readUInt()
	
	if version > 27:
		bs.seek(8,1)
	
	mipData = []
	for i in range(numImages):
		mipDataImg = []
		for j in range(mipCount):
			mipDataImg.append([bs.readUInt64(), bs.readUInt(), bs.readUInt()]) #[0]offset, [1]pitch, [2]size
		mipData.append(mipDataImg)
		#bs.seek((mipCount-1)*16, 1) #skip small mipmaps
		
	texFormat = noesis.NOESISTEX_RGBA32
	
	tex = False
	for i in range(numImages):
		mipWidth = width
		mipHeight = height
		for j in range(mipCount):
			try:
				bs.seek(mipData[i][j][0])
				texData = bs.readBytes(mipData[i][j][2])
			except:
				if i > 0:
					numImages = i - 1
					print ("Multi-image load stopped early")
					break
				else:
					return 0
			try:
				texData, fmtName = readTextureData(texData, mipWidth, mipHeight, format)
			except:
				print("Failed", mipWidth, mipHeight, format, texData)
				texData, fmtName = readTextureData(texData, mipWidth, mipHeight, format)
			if texData == 0:
				return 0
			
			tex = NoeTexture(texName, int(mipWidth), int(mipHeight), texData, texFormat)
			texList.append(tex)
			
			if not bImportMips:
				break
			if mipWidth > 4: 
				mipWidth = int(mipWidth / 2)
			if mipHeight > 4: 
				mipHeight = int(mipHeight / 2)
				
	return tex
	
def getNoesisDDSType(imgType):
	ddsFmt = noesis.NOE_ENCODEDXT_BC7
	if imgType == 71 or imgType == 72: ddsFmt = noesis.NOE_ENCODEDXT_BC1
	elif imgType == 80: ddsFmt = noesis.NOE_ENCODEDXT_BC4
	elif imgType == 83: ddsFmt = noesis.NOE_ENCODEDXT_BC5
	elif imgType == 95: ddsFmt = noesis.NOE_ENCODEDXT_BC6H
	elif imgType == 98 or imgType == 99: ddsFmt = noesis.NOE_ENCODEDXT_BC7
	elif imgType == 28 or imgType == 29: ddsFmt = "r8g8b8a8"
	elif imgType == 77: ddsFmt = noesis.NOE_ENCODEDXT_BC3;
	elif imgType == 10 or imgType == 95: ddsFmt = "r16g16b16a16"
	elif imgType == 61: ddsFmt = "r8"
	return ddsFmt

def findSourceTexFile(version_no, outputName=None):
	newTexName = outputName or rapi.getOutputName().lower()
	while newTexName.find("out.") != -1: 
		newTexName = newTexName.replace("out.",".")
	newTexName =  newTexName.replace(".dds","").replace(".tex","").replace(".10","").replace(".190820018","").replace(".143221013","").replace(".11","").replace(".8","").replace(".28","").replace(".34","").replace(".35","").replace(".30","").replace(".jpg","").replace(".png","").replace(".tga","").replace(".gif","")
	ext = ".tex." + str(version_no)
	if not rapi.checkFileExists(newTexName + ext):
		for other_ext, subDict in extToFormat.items():
			if rapi.checkFileExists(newTexName + ".tex." + other_ext):
				ext = ".tex." + other_ext
	return newTexName + ext, ext
	
def convertTexVersion(version_no): #because RE3R and RE4R randomly decide to use timestamps for version numbers, which doesnt work well with using the others as versions
	if version_no == 143221013:
		return 36
	if version_no == 190820018:
		return 10
	return version_no

def texWriteRGBA2(data, width, height, bs, version_no):
	sourceFile = findSourceTexFile(10)
	#print(str(sourceFile))
	tex = texFile(data, width, height, sourceFile[0], rapi.getOutputName())
	if not hasattr(tex, "error"):
		bs = tex.writeTexHeader(bs)
		tex.writeTexImageData(bs, 1)
		return 1
	else:
		sourceFile = (sourceFile and sourceFile[0]) or rapi.getOutputName()
		print("No format detected for " + sourceFile)
	return 0

def texWriteRGBA(data, width, height, bs):
	
	print ("\n			----RE Engine TEX Export----\n")
	
	version_no = int(os.path.splitext(rapi.getOutputName())[1][1:])
	if noesis.optWasInvoked("-b"): # and version_no >= 28 and version_no < 1000: #batch / no-prompt
		return texWriteRGBA2(data, width, height, bs, version_no)
		
	def getExportName(fileName):		
		if fileName == None:
			newTexName = rapi.getOutputName().lower()
		else: 
			newTexName = fileName
		nonlocal version_no
		guessedName, ext = findSourceTexFile(version_no)
		
		newTexName = noesis.userPrompt(noesis.NOEUSERVAL_FILEPATH, "Export over tex", "Choose a tex file to export over", guessedName, None)
		
		if newTexName == None:
			print("Aborting...!")
			return
		return newTexName
		
	fileName = None
	newTexName = getExportName(fileName)
	if newTexName == None:
		return 0
		
	while not (rapi.checkFileExists(newTexName)):
		print ("File not found")
		newTexName = getExportName(fileName)	
		fileName = newTexName
		if newTexName == None:
			return 0	
	
	bTexAsSource = False		
	newTEX = rapi.loadIntoByteArray(newTexName)
	oldDDS = rapi.loadIntoByteArray(rapi.getInputName())
	
	print(newTexName.lower())
	print(rapi.getInputName().lower())
	
	f = NoeBitStream(newTEX)
	og = NoeBitStream(oldDDS)
	
	magic = f.readUInt()
	version = f.readUInt()
	fWidth = f.readUShort()
	fHeight = f.readUShort()
	reVerseSize = 0
	
	version = convertTexVersion(version)
	
	f.seek(14)
	if version  > 27:
		reVerseSize = 8
		numImages = f.readUByte()
		oneImgMipHdrSize = f.readUByte()
		maxMips = int(oneImgMipHdrSize / 16)
	else:
		maxMips = f.readUByte()
		numImages = f.readUByte()
	
	ddsMagic = og.readUInt()
	bDoEncode = False
	if magic != 5784916:
		print ("Selected file is not a TEX file!\nAborting...")
		return 0
	
	f.seek(16)
	imgType = f.readUInt()
	print ("TEX type:", imgType)
	
	ddsFmt = 0
	bQuitIfEncode = False
	try:
		if imgType == 71 or imgType == 72: ddsFmt = noesis.NOE_ENCODEDXT_BC1
		elif imgType == 80: ddsFmt = noesis.NOE_ENCODEDXT_BC4
		elif imgType == 83: ddsFmt = noesis.NOE_ENCODEDXT_BC5
		elif imgType == 95: ddsFmt = noesis.NOE_ENCODEDXT_BC6H
		elif imgType == 98 or imgType == 99: ddsFmt = noesis.NOE_ENCODEDXT_BC7
		elif imgType == 28 or imgType == 29: ddsFmt = "r8g8b8a8"
		elif imgType == 77: ddsFmt = noesis.NOE_ENCODEDXT_BC3;
		elif imgType == 10 or imgType == 95: ddsFmt = "r16g16b16a16"
		elif imgType == 61: ddsFmt = "r8"
		else: 
			print ("Unknown TEX type:", imgType)
			if imgType != 10:
				return 0
	except: 
		bQuitIfEncode = True

	print ("Exporting over \"" + rapi.getLocalFileName(newTexName)+ "\"")
	
	texFmt = ddsFmt
	#ogHeaderSize = 0
	if og and ddsMagic == 542327876: #DDS
		ogHeaderSize = og.readUInt() + 4
		og.seek(84)
		if og.readUInt() == 808540228: #DX10
			ogHeaderSize += 20
			if ddsFmt == noesis.NOE_ENCODEDXT_BC1:
				print ("Source DDS encoding (BC7) does not match TEX file (BC1).\nEncoding image...")
				bDoEncode = True
		elif ddsFmt == noesis.NOE_ENCODEDXT_BC7:
			print ("Source DDS encoding (BC1) does not match TEX file (BC7).\nEncoding image...")
			bDoEncode = True
	elif og and ddsMagic == 5784916: #TEX
		bTexAsSource = True
		og.seek(4)
		ogVersion = convertTexVersion(og.readUInt())
		
		if ((ogVersion > 27) and int(os.path.splitext(rapi.getOutputName())[1][1:]) < 27) or ((ogVersion < 27 and int(os.path.splitext(rapi.getOutputName())[1][1:]) > 27)):
			print("\nWARNING: Source tex version does not match your output tex version\n	Selected Output:      tex" + str(os.path.splitext(rapi.getOutputName())[1]), "\n	Source Tex version: tex." + str(ogVersion) + "\n")
		og.seek(8)
		ogWidth = og.readUShort()
		ogHeight = og.readUShort()
		if ogWidth != width or ogHeight != height: 
			print ("Input TEX file uses a different resolution from Source TEX file.\nEncoding image...")
			bDoEncode = True
		og.seek(14)
		
		ogHeaderSize = og.readUByte() * 16 + 32
		if ogVersion  > 27: 
			ogHeaderSize = 40 + og.readUByte()
		og.seek(16)
		srcType = og.readUInt()  
		if srcType == 71 or srcType == 72: texFmt = noesis.NOE_ENCODEDXT_BC1
		elif srcType == 80: texFmt = noesis.NOE_ENCODEDXT_BC4
		elif srcType == 83: texFmt = noesis.NOE_ENCODEDXT_BC5
		elif srcType == 95: texFmt = noesis.NOE_ENCODEDXT_BC6H
		elif srcType == 98 or srcType == 99: texFmt = noesis.NOE_ENCODEDXT_BC7
		elif srcType == 28 or srcType == 29: texFmt = "r8g8b8a8"
		elif srcType == 77: texFmt = noesis.NOE_ENCODEDXT_BC3;
		elif srcType == 10 or srcType == 95: texFmt = "r16g16b16a16"
		elif srcType == 61: texFmt = "r8"
		else: 
			print ("Unknown TEX type:", srcType)
			return 0
		if texFmt != ddsFmt or (os.path.splitext(newTexName)[1] == ".30" and os.path.splitext(rapi.getInputName())[1] != ".30"): 
			print ("Input TEX file uses a different compression or format from Source TEX file.\nEncoding image...")
			bDoEncode = True
	else: 
		print ("Input file is not a DDS or TEX file\nEncoding image...")
		bDoEncode = True
	
	mipSize = width * height
	if texFmt == noesis.NOE_ENCODEDXT_BC1: mipSize = int(mipSize / 2)
	if not bDoEncode and mipSize < int((os.path.getsize(rapi.getInputName())) / 4):
		print ("Unexpected source image size\nEncoding image...")
		bDoEncode = True
		
	if not bDoEncode: 
		print ("Copying image data from \"" + rapi.getLocalFileName(rapi.getInputName()) + "\"")
		
	elif bQuitIfEncode:
		print ("Fatal Error: BC7 Encoding not supported!\nUpdate to Noesis v4434 (Oct 14, 2020) or later to encode BC7 images\nAborting...\n")
		return 0
		
	#copy header
	f.seek(0)
	bs.writeBytes(f.readBytes(32 + reVerseSize))
	
	numMips = 0
	output_mips = 0
	dataSize = 0
	totalData = 0
	sizeArray = []
	fileData = []
	mipWidth = width
	mipHeight = height
	
	exportCycles = 1
	if numImages > 1:
		imgToReplace = 0
		imgToReplace = noesis.userPrompt(noesis.NOEUSERVAL_FILEPATH, "Multi-image texture", "Which image do you want to replace? [0-" + str(numImages-1) + "]", "All", None)
		if imgToReplace == None:
			return 0
		try:
			int(imgToReplace)
		except:
			exportCycles = numImages #if not a number, copy all images
		mipWidth = fWidth
		mipHeight = fHeight
		bs.writeBytes(f.readBytes(os.path.getsize(newTexName) - f.tell())) #copy whole file
	
	print ("Format:", ddsFmt)
	for img in range(exportCycles):
			
		#write mipmap headers & encode image
		if img == 0:
			while mipWidth > 4 or mipHeight > 4:
				if ddsFmt == "r8" and numMips > 1:
					break
				numMips += 1
				output_mips += 1
				if bDoEncode:
					mipData = rapi.imageResample(data, width, height, mipWidth, mipHeight)
					try:
						dxtData = rapi.imageEncodeDXT(mipData, 4, mipWidth, mipHeight, ddsFmt)
					except:
						dxtData = rapi.imageEncodeRaw(mipData, mipWidth, mipHeight, ddsFmt)
					mipSize = len(dxtData)
					fileData.append(dxtData)
					
				else:
					mipSize = mipWidth * mipHeight
					if texFmt == noesis.NOE_ENCODEDXT_BC1:
						mipSize = int(mipSize / 2)
					
				sizeArray.append(dataSize)
				dataSize += mipSize
				
				pitch = mipWidth
				if ddsFmt == noesis.NOE_ENCODEDXT_BC1:
					pitch *= 2
				elif ddsFmt != "r8":
					pitch *= 4
					
				bs.writeUInt64(0)
				bs.writeUInt(pitch)
				bs.writeUInt(mipSize)
				
                
				print ("Mip", numMips, ": ", mipWidth, "x", mipHeight, "\n            ", pitch, "\n            ", mipSize)
				if mipWidth > 4: mipWidth = int(mipWidth / 2)
				if mipHeight > 4: mipHeight = int(mipHeight / 2)
		
		if numImages > 1: #multi image images seek to their image data and encode at the same size 
			if exportCycles > 1:
				mipOffset = readUIntAt(f, (32 + reVerseSize + 16 * (int(img) * maxMips)) ) #copy same image data over the other images
				print ("Img",  img+1, "of", exportCycles)
			else:
				mipOffset = readUIntAt(f, (32 + reVerseSize + 16 * (int(imgToReplace) * maxMips)) )
		
		if bDoEncode: 
			if numImages > 1:
				bs.seek(mipOffset)
			for d in range(len(fileData)): #write image data
				bs.writeBytes(fileData[d])
		elif not numImages > 1:
			og.seek(ogHeaderSize) #copy image data
			bs.writeBytes(og.readBytes(os.path.getsize(rapi.getInputName()) - ogHeaderSize))
		else:
			og.seek(ogHeaderSize)
			bs.seek(mipOffset) #seek to image-to-replace
			bs.writeBytes(og.readBytes(os.path.getsize(rapi.getInputName()) - ogHeaderSize))
		
		#adjust header
		if numImages == 1:
			bs.seek(28)
			if readUByteAt(f, 28) > 127:
				bs.writeUByte(128) #ReVerse streaming
			else: 
				bs.writeUByte(0) #streaming texture
				
			bs.seek(8)
			bs.writeUShort(width)
			bs.writeUShort(height)
			if version  > 27:
				bs.seek(15)
				bs.writeUByte(numMips * 16)
			else:
				bs.seek(14)
				bs.writeUByte(numMips)
			
			bsHeaderSize = output_mips * 16 + 32 + reVerseSize
			bs.seek(32 + reVerseSize)
			
			for mip in range(numMips):
				bs.writeUInt64(sizeArray[mip] + bsHeaderSize)
				bs.seek(8, 1)	
		else:
			if numImages > 1:
				bs.seek(mipOffset)
			for d in range(len(fileData)): #write image data
				bs.writeBytes(fileData[d])

	return 1

class DialogOptions:
	def __init__(self):
		self.doLoadTex = False
		self.doConvertTex = True
		self.doLODs = False
		self.loadAllTextures = False
		self.reparentHelpers = True
		self.doCreateBoneMap = True
		self.doForceCenter = False
		self.doSync = True
		self.doForceMergeAnims = False
		self.doConvertMatsForBlender = doConvertMatsForBlender
		self.width = 600
		self.height = 850
		self.texDicts = None
		self.gameName = sGameName
		self.currentDir = ""
		self.motDialog = None
		self.dialog = None

dialogOptions = DialogOptions()

DoubleClickTimer = namedtuple("DoubleClickTimer", "name idx timer")

gamesList = [ "RE7", "RE7RT", "RE2", "RERT", "RE3", "RE4", "RE8", "MHRSunbreak", "DMC5", "SF6", "ReVerse" ]
fullGameNames = [
	"Resident Evil 7",
	"Resident Evil 7 RT",
	"Resident Evil 2",
	"Resident Evil 2/3 RT",
	"Resident Evil 3",
	"Resident Evil 4",
	"Resident Evil 8",
	"MH Rise Sunbreak",
	"Devil May Cry 5",
	"Street Fighter 6",
	"Resident Evil ReVerse"
]
		
class openOptionsDialogImportWindow:
	
	def __init__(self, width=dialogOptions.width, height=dialogOptions.height, args={}):
		global dialogOptions
		
		self.width = width
		self.height = height
		self.args = args
		self.pak = args.get("motlist") or args.get("mesh")
		self.isMotlist = args.get("isMotlist")
		self.path = self.pak.path if self.pak else rapi.getInputName()
		self.loadItems = [rapi.getLocalFileName(self.path)] if not self.isMotlist else []
		self.fullLoadItems = [self.path] if not self.isMotlist else []
		if self.isMotlist: 
			if dialogOptions.motDialog and dialogOptions.motDialog.pak:
				self.pak = dialogOptions.motDialog.pak
				self.path = dialogOptions.motDialog.pak.path
				self.loadItems = dialogOptions.motDialog.loadItems
				self.fullLoadItems = dialogOptions.motDialog.fullLoadItems
			if self.pak:
				self.motItems = [mot.name for mot in self.pak.mots]
		self.name = rapi.getLocalFileName(self.path)
		self.localDir = rapi.getDirForFilePath(self.path)
		dialogOptions.currentDir = dialogOptions.currentDir or self.localDir
		self.currentDir = dialogOptions.currentDir
		self.localRoot = findRootDir(self.path)
		self.baseDir = LoadExtractedDir(sGameName)
		self.allFiles = []
		self.pakFiles = []
		self.subDirs = []
		self.motItems = []
		self.loadedMlists = {}
		self.pakIdx = 0
		self.baseIdx = -1
		self.loadIdx = 0
		self.dirIdx = 0
		self.gameIdx = 0
		self.localIdx = 0
		self.clicker = DoubleClickTimer(name="", idx=0, timer=0)
		dialogOptions.dialog = self
		self.isOpen = True
		self.isCancelled = False
		if self.isMotlist and dialogOptions.motDialog:
			self.motItems = dialogOptions.motDialog.motItems
		
	def openMotlistDialogButton(self, noeWnd, controlId, wParam, lParam):
		if not dialogOptions.motDialog or not dialogOptions.motDialog.isOpen:
			dialogOptions.motDialog = openOptionsDialogImportWindow(None, None, {"isMotlist": True})
			self.noeWnd.closeWindow()
			#dialogOptions.motDialog.createMotlistWindow()
		
	def openOptionsButtonLoadEntry(self, noeWnd, controlId, wParam, lParam):
		self.isOpen = False
		if self.isMotlist:
			self.loadedMlists = {}
			bones = self.pak.bones
			totalFrames = self.pak.totalFrames
			mdlBoneNames = [bone.name for bone in bones]
			for path in self.fullLoadItems:
				if ".motlist." in path.lower() and path not in self.loadedMlists and rapi.checkFileExists(path):
					self.loadedMlists[path] = motlistFile(rapi.loadIntoByteArray(path), path)
					self.loadedMlists[path].bones = bones
					self.loadedMlists[path].readBoneHeaders(self.loadItems)
			for i, motName in enumerate(self.loadItems):
				if motName.find("[ALL] - ") == 0:
					fullPath = self.fullLoadItems[i]
					for mot in self.loadedMlists[fullPath].mots:
						if mot.name not in self.loadItems:
							self.loadItems.append(mot.name)
							self.fullLoadItems.append(fullPath)
		self.noeWnd.closeWindow()
			
	def openOptionsButtonCancel(self, noeWnd, controlId, wParam, lParam):
		self.isCancelled = True
		self.isOpen = False
		self.noeWnd.closeWindow()
		
	def openOptionsButtonParentDir(self, noeWnd, controlId, wParam, lParam):
		if self.localIdx == 0: 
			self.localRoot = os.path.dirname(self.localRoot)
		else:
			self.baseDir = os.path.dirname(self.baseDir)
		self.setDirList()
		self.setPakList()
		if self.subDirs:
			self.dirList.selectString(self.subDirs[0])
			
	def pressLoadListUpButton(self, noeWnd, controlId, wParam, lParam):
		selIdx = self.loadList.getSelectionIndex()
		if selIdx > 0:
			self.loadItems[selIdx], self.loadItems[selIdx-1], self.fullLoadItems[selIdx], self.fullLoadItems[selIdx-1] = self.loadItems[selIdx-1], self.loadItems[selIdx], self.fullLoadItems[selIdx-1], self.fullLoadItems[selIdx]
			for item in self.loadItems: self.loadList.removeString(item)
			for item in self.loadItems: self.loadList.addString(item)
			self.loadList.selectString(self.loadItems[selIdx-1])
			
	def pressLoadListDownButton(self, noeWnd, controlId, wParam, lParam):
		selIdx = self.loadList.getSelectionIndex()
		if selIdx != -1 and selIdx < len(self.loadItems)-1:
			self.loadItems[selIdx], self.loadItems[selIdx+1], self.fullLoadItems[selIdx], self.fullLoadItems[selIdx+1] = self.loadItems[selIdx+1], self.loadItems[selIdx], self.fullLoadItems[selIdx+1], self.fullLoadItems[selIdx]
			for item in self.loadItems: self.loadList.removeString(item)
			for item in self.loadItems: self.loadList.addString(item)
			self.loadList.selectString(self.loadItems[selIdx+1])
	
	def selectBaseListItem(self, noeWnd, controlId, wParam, lParam):
		self.baseIdx = self.baseList.getSelectionIndex()
		dialogOptions.baseSkeleton = self.baseList.getStringForIndex(self.baseIdx)
	
	def selectMotlistItem(self, noeWnd, controlId, wParam, lParam):
		self.motIdx = self.motLoadList.getSelectionIndex()
		if self.clicker.name == "motList" and self.motIdx == self.clicker.idx and time.time() - self.clicker.timer < 0.25:
			addedName = self.motLoadList.getStringForIndex(self.motIdx)
			if addedName not in self.loadItems:
				self.loadItems.append(addedName)
				self.fullLoadItems.append(self.pak.path)
				self.loadList.addString(addedName)
		self.clicker = DoubleClickTimer(name="motList", idx=self.motIdx, timer=time.time())
	
	def selectPakListItem(self, noeWnd, controlId, wParam, lParam):
		self.pakIdx = self.pakList.getSelectionIndex()
		if self.clicker.name == "pakList" and self.pakIdx == self.clicker.idx and time.time() - self.clicker.timer < 0.25:
			path = dialogOptions.currentDir + "\\" + self.pakList.getStringForIndex(self.pakIdx)
			if self.pakIdx == 0: #parent directory
				if dialogOptions.currentDir[-1:] == "\\":
					dialogOptions.currentDir = os.path.dirname(dialogOptions.currentDir)
				lastDir = rapi.getLocalFileName(dialogOptions.currentDir)
				dialogOptions.currentDir = os.path.dirname(dialogOptions.currentDir)
				self.setPakList()
				self.pakList.selectString(lastDir)
			elif self.pakIdx <= len(self.subDirs):
				dialogOptions.currentDir += "\\" + self.pakList.getStringForIndex(self.pakIdx)
				self.setPakList()
			elif self.isMotlist:
				self.pak = motlistFile(rapi.loadIntoByteArray(path), path)
				self.setMotLoadList([mot.name for mot in self.pak.mots]) 
			elif self.pakList.getStringForIndex(self.pakIdx) not in self.loadItems:
				self.loadItems.append(self.pakList.getStringForIndex(self.pakIdx))
				self.fullLoadItems.append(path)
				self.loadList.addString(self.pakList.getStringForIndex(self.pakIdx))
				#self.fullLoadItems = [x for _, x in sorted(zip(self.loadItems, self.fullLoadItems))]
				#self.loadItems = sorted(self.loadItems)
		self.clicker = DoubleClickTimer(name="pakList", idx=self.pakIdx, timer=time.time())
		self.currentDir = dialogOptions.currentDir
	
	def selectLoadListItem(self, noeWnd, controlId, wParam, lParam):
		self.loadIdx = self.loadList.getSelectionIndex()
		if self.clicker.name == "loadList" and self.loadIdx == self.clicker.idx and time.time() - self.clicker.timer < 0.25 and (self.isMotlist or self.loadItems[self.loadIdx] != self.name):
			self.loadList.removeString(self.loadItems[self.loadIdx])
			del self.loadItems[self.loadIdx]
			if not self.isMotlist:
				del self.fullLoadItems[self.loadIdx]
			self.loadIdx = self.loadIdx if self.loadIdx < len(self.loadItems) else self.loadIdx - 1
			if abs(self.loadIdx) < len(self.loadItems):
				self.loadList.selectString(self.loadItems[self.loadIdx])
		self.clicker = DoubleClickTimer(name="loadList", idx=self.loadIdx, timer=time.time())
		self.currentDir = dialogOptions.currentDir
		
	def selectGameBoxItem(self, noeWnd, controlId, wParam, lParam):
		global sGameName
		if self.gameIdx != self.gameBox.getSelectionIndex():
			self.gameIdx = self.gameBox.getSelectionIndex()
			restOfPath = dialogOptions.currentDir.replace(self.baseDir, "").replace(formats[sGameName]["nDir"]+"\\", "")
			sGameName = gamesList[self.gameIdx]
			self.baseDir = LoadExtractedDir(sGameName) #BaseDirectories[sGameName]
			if self.localBox.getStringForIndex(self.localIdx) == "Base Directory":
				dialogOptions.currentDir = self.baseDir
				if restOfPath and os.path.isdir(self.baseDir + restOfPath):
					dialogOptions.currentDir = self.baseDir + restOfPath
				self.setPakList()
		self.currentDir = dialogOptions.currentDir
				
	def selectLocalBoxItem(self, noeWnd, controlId, wParam, lParam):
		if self.localIdx != self.localBox.getSelectionIndex():
			self.localIdx = self.localBox.getSelectionIndex()
			restOfPath = dialogOptions.currentDir.replace(self.localRoot, "").replace(self.baseDir, "").replace(formats[sGameName]["nDir"]+"\\", "")
			if self.localBox.getStringForIndex(self.localIdx) == "Base Directory":
				dialogOptions.currentDir = self.baseDir
				if restOfPath and os.path.isdir(self.baseDir + restOfPath):
					dialogOptions.currentDir = self.baseDir + restOfPath
			else:
				dialogOptions.currentDir = os.path.dirname(self.path)
				if restOfPath and os.path.isdir(self.localRoot + restOfPath):
					dialogOptions.currentDir = self.localRoot + restOfPath
			self.setPakList()
		self.currentDir = dialogOptions.currentDir
		
	def setGameBox(self, list_object=None, current_item=None):
		for i, name in enumerate(fullGameNames):
			self.gameBox.addString(name)
		self.gameBox.selectString(fullGameNames[gamesList.index(sGameName)])
		self.gameIdx = self.gameBox.getSelectionIndex()
		
	def setLocalBox(self, list_object=None, current_item=None):
		for name in ["Local Folder", "Base Directory"]:
			self.localBox.addString(name)
		self.localBox.selectString("Local Folder")
		self.localIdx = self.localBox.getSelectionIndex()
	
	def checkLoadTexCheckbox(self, noeWnd, controlId, wParam, lParam):
		dialogOptions.doLoadTex = not dialogOptions.doLoadTex
		self.loadTexCheckbox.setChecked(dialogOptions.doLoadTex)
		
	def checkLODsCheckbox(self, noeWnd, controlId, wParam, lParam):
		dialogOptions.doLODs = not dialogOptions.doLODs
		self.LODsCheckbox.setChecked(dialogOptions.doLODs)
		
	def checkConvTexCheckbox(self, noeWnd, controlId, wParam, lParam):
		dialogOptions.doConvertTex = not dialogOptions.doConvertTex
		self.convTexCheckbox.setChecked(dialogOptions.doConvertTex)
		
	def checkFlipUVsCheckbox(self, noeWnd, controlId, wParam, lParam):
		dialogOptions.doFlipUVs = not dialogOptions.doFlipUVs
		self.flipUVsCheckbox.setChecked(dialogOptions.doFlipUVs)
		
	def checkLoadAllTexCheckbox(self, noeWnd, controlId, wParam, lParam):
		dialogOptions.loadAllTextures = not dialogOptions.loadAllTextures
		self.loadAllTexCheckbox.setChecked(dialogOptions.loadAllTextures)
		
	def checkReparentCheckbox(self, noeWnd, controlId, wParam, lParam):
		dialogOptions.reparentHelpers = not dialogOptions.reparentHelpers
		self.reparentCheckbox.setChecked(dialogOptions.reparentHelpers)
		
	def checkFCenterCheckbox(self, noeWnd, controlId, wParam, lParam):
		dialogOptions.doForceCenter = not dialogOptions.doForceCenter
		self.FCenterCheckbox.setChecked(dialogOptions.doForceCenter)
		
	def checkSyncCheckbox(self, noeWnd, controlId, wParam, lParam):
		dialogOptions.doSync = not dialogOptions.doSync
		self.syncCheckbox.setChecked(dialogOptions.doSync)
		
	def checkForceMergeCheckbox(self, noeWnd, controlId, wParam, lParam):
		dialogOptions.doForceMergeAnims = not dialogOptions.doForceMergeAnims
		self.forceMergeCheckbox.setChecked(dialogOptions.doForceMergeAnims)
		
	def setMotLoadList(self, motItems=[]):
		for name in self.motItems:
			self.motLoadList.removeString(name)
		self.motItems = []
		if motItems:
			motItems.insert(0, "[ALL] - " + self.pak.name)
			for name in motItems:
				self.motLoadList.addString(name)
			self.motItems = motItems
			self.motLoadList.selectString(self.motItems[0])
		
	def setLoadList(self, loadItems=[]):
		for item in self.loadItems:
			self.loadList.removeString(item)
		if loadItems:
			self.loadItems = loadItems
			for item in self.loadItems:
				self.loadList.addString(item)
			self.loadList.selectString(self.loadItems[0])
		else:
			self.loadItems = [self.name] if not self.isMotlist else []
			if self.loadItems:
				self.loadList.addString(self.loadItems[0])
		self.loadList.selectString((self.pak and self.pak.path) or rapi.getInputName())
		
	def setPakList(self):
		for name in self.allFiles:
			self.pakList.removeString(name)
		self.allFiles = [".."]
		self.pakFiles = []
		self.subDirs = []
		exts = [formatTbl["mlistExt" if self.isMotlist else "modelExt"] for gameName, formatTbl in formats.items()]
		for item in os.listdir(dialogOptions.currentDir):
			if os.path.isdir(os.path.join(dialogOptions.currentDir, item)):
				self.subDirs.append(item)
			if os.path.isfile(os.path.join(dialogOptions.currentDir, item)) and "." in item and os.path.splitext(item)[1] in exts:
				self.pakFiles.append(item)
		self.subDirs = sorted(self.subDirs)
		self.pakFiles = sorted(self.pakFiles)
		self.allFiles.extend(self.subDirs)
		self.allFiles.extend(self.pakFiles)
		for item in self.allFiles:
			self.pakList.addString(item)
		if self.name in self.allFiles:
			self.pakIdx = self.allFiles.index(self.name)
			self.pakList.selectString(self.name)
		elif self.pak and rapi.getLocalFileName(self.pak.path) in self.allFiles:
			self.pakIdx = self.allFiles.index(rapi.getLocalFileName(self.pak.path))
			self.pakList.selectString(self.pakList.getStringForIndex(self.pakIdx))
		elif self.pakIdx < len(self.allFiles):
			self.pakList.selectString(self.pakList.getStringForIndex(self.pakIdx))
		else:
			self.pakIdx = 0
			self.pakList.selectString(self.pakList.getStringForIndex(0))
		self.currentDirEditBox.setText(dialogOptions.currentDir)
		
	def inputCurrentDirEditBox(self, noeWnd, controlId, wParam, lParam):
		text = self.currentDirEditBox.getText().lower()
		if text != dialogOptions.currentDir.lower() and os.path.exists(text):
			dialogOptions.currentDir = os.path.dirname(text) if os.path.isfile(text) else text
			self.setPakList()
			if os.path.isfile(text):
				lowerAllFiles = [name.lower() for name in self.allFiles]
				if rapi.getLocalFileName(text) in lowerAllFiles:
					self.pakList.selectString(self.pakList.getStringForIndex(lowerAllFiles.index(rapi.getLocalFileName(text))))
				if self.isMotlist and ".motlist" in text:
					self.pak = motlistFile(rapi.loadIntoByteArray(text), text)
					self.setMotLoadList([mot.name for mot in self.pak.mots]) 
					
	def inputGlobalScaleEditBox(self, noeWnd, controlId, wParam, lParam):
		global fDefaultMeshScale
		try:
			if self.globalScaleEditBox.getText():
				newScale = float(self.globalScaleEditBox.getText())
				if newScale:
					fDefaultMeshScale = newScale
		except ValueError:
			print("Non-numeric scale input, resetting to ", fDefaultMeshScale)
			self.globalScaleEditBox.setText(str(fDefaultMeshScale))
			
	def create(self, width=dialogOptions.width, height=dialogOptions.height):
		self.noeWnd = noewin.NoeUserWindow("RE Engine '.mesh' Plugin                                " + rapi.getLocalFileName(self.name), "HTRAWWindowClass", width, height) 
		noeWindowRect = noewin.getNoesisWindowRect()
		if noeWindowRect:
			windowMargin = 100
			self.noeWnd.x = noeWindowRect[0] + windowMargin
			self.noeWnd.y = noeWindowRect[1] + windowMargin  
		return self.noeWnd.createWindow()
		
	def createMotlistWindow(self, width=dialogOptions.width, height=dialogOptions.height):
		
		if self.create(width, height):
			self.noeWnd.setFont("Futura", 14)
			
			self.noeWnd.createStatic("Motlist files from:", 5, 5, width-20, 20)
			index = self.noeWnd.createEditBox(5, 25, width-20, 45, dialogOptions.currentDir, self.inputCurrentDirEditBox) #EB
			self.currentDirEditBox = self.noeWnd.getControlByIndex(index)
			
			index = self.noeWnd.createListBox(5, 80, width-20, 160, self.selectPakListItem, noewin.LBS_NOTIFY | noewin.WS_VSCROLL | noewin.WS_BORDER) #LB
			self.pakList = self.noeWnd.getControlByIndex(index)
			
			self.noeWnd.createStatic("Motions:", 5, 240, width-20, 20)
			index = self.noeWnd.createListBox(5, 260, width-20, 240, self.selectMotlistItem, noewin.LBS_NOTIFY | noewin.WS_VSCROLL | noewin.WS_BORDER) #LB
			self.motLoadList = self.noeWnd.getControlByIndex(index)
			
			self.noeWnd.createStatic("Motions to load:", 5, 505, width-20, 20)
			index = self.noeWnd.createListBox(5, 525, width-40, 150, self.selectLoadListItem, noewin.LBS_NOTIFY | noewin.WS_VSCROLL | noewin.WS_BORDER) #LB
			self.loadList = self.noeWnd.getControlByIndex(index)
			
			self.noeWnd.createButton("↑", width-30, 565, 20, 30, self.pressLoadListUpButton)
			self.noeWnd.createButton("↓", width-30, 605, 20, 30, self.pressLoadListDownButton)
			
			if True:
				index = self.noeWnd.createCheckBox("Force Center", 10, 685, 100, 30, self.checkFCenterCheckbox)
				self.FCenterCheckbox = self.noeWnd.getControlByIndex(index)
				self.FCenterCheckbox.setChecked(dialogOptions.doForceCenter)
				
				index = self.noeWnd.createCheckBox("Sync by Frame Count", 10, 715, 160, 30, self.checkSyncCheckbox)
				self.syncCheckbox = self.noeWnd.getControlByIndex(index)
				self.syncCheckbox.setChecked(dialogOptions.doSync)
				
				index = self.noeWnd.createCheckBox("Force Merge All", 10, 745, 160, 30, self.checkForceMergeCheckbox)
				self.forceMergeCheckbox = self.noeWnd.getControlByIndex(index)
				self.forceMergeCheckbox.setChecked(dialogOptions.doForceMergeAnims)

			self.noeWnd.createStatic("Game:", width-218, height-160, 60, 20)
			index = self.noeWnd.createComboBox(width-170, height-165, 150, 20, self.selectGameBoxItem, noewin.CBS_DROPDOWNLIST) #CB
			self.gameBox = self.noeWnd.getControlByIndex(index)
			
			self.noeWnd.createStatic("View:", width-210, height-130, 60, 20)
			index = self.noeWnd.createComboBox(width-170, height-135, 150, 20, self.selectLocalBoxItem, noewin.CBS_DROPDOWNLIST) #CB
			self.localBox = self.noeWnd.getControlByIndex(index)
			
			self.noeWnd.createStatic("Scale:", width-215, height-100, 60, 20)
			index = self.noeWnd.createEditBox(width-170, height-100, 80, 20, str(fDefaultMeshScale), self.inputGlobalScaleEditBox, False) #EB
			self.globalScaleEditBox = self.noeWnd.getControlByIndex(index)
			
			self.noeWnd.createButton("Load" if not self.isMotlist or self.args.get("motlist") else "OK", 5, height-70, width-160, 30, self.openOptionsButtonLoadEntry)
			self.noeWnd.createButton("Cancel", width-96, height-70, 80, 30, self.openOptionsButtonCancel)
			
			self.setMotLoadList([mot.name for mot in self.pak.mots] if self.pak else [])
			self.setLoadList(self.loadItems)
			self.setPakList()
			self.setGameBox(self.gameBox)
			self.setLocalBox(self.localBox)
			
			self.noeWnd.doModal()
	
	def createPakWindow(self, width=dialogOptions.width, height=dialogOptions.height):
		
		if self.create(width, height):
			self.noeWnd.setFont("Futura", 14)
			
			self.noeWnd.createStatic("Mesh files from:", 5, 45, width-20, 20)
			index = self.noeWnd.createEditBox(5, 65, width-20, 45, dialogOptions.currentDir, self.inputCurrentDirEditBox) #EB
			self.currentDirEditBox = self.noeWnd.getControlByIndex(index)
			
			index = self.noeWnd.createListBox(5, 120, width-20, 380, self.selectPakListItem, noewin.LBS_NOTIFY | noewin.WS_VSCROLL | noewin.WS_BORDER) #LB
			self.pakList = self.noeWnd.getControlByIndex(index)
			
			self.noeWnd.createStatic("Files to load:", 5, 505, width-20, 20)
			index = self.noeWnd.createListBox(5, 525, width-40, 150, self.selectLoadListItem,  noewin.LBS_NOTIFY | noewin.WS_VSCROLL | noewin.WS_BORDER) #LB
			self.loadList = self.noeWnd.getControlByIndex(index)
			
			self.noeWnd.createButton("↑", width-30, 565, 20, 30, self.pressLoadListUpButton)
			self.noeWnd.createButton("↓", width-30, 605, 20, 30, self.pressLoadListDownButton)
			
			
			if True:
				index = self.noeWnd.createCheckBox("Load Textures", 10, 685, 130, 30, self.checkLoadTexCheckbox)
				self.loadTexCheckbox = self.noeWnd.getControlByIndex(index)
				self.loadTexCheckbox.setChecked(dialogOptions.doLoadTex)
				
				
				index = self.noeWnd.createCheckBox("Load All Textures", 150, 685, 160, 30, self.checkLoadAllTexCheckbox)
				self.loadAllTexCheckbox = self.noeWnd.getControlByIndex(index)
				self.loadAllTexCheckbox.setChecked(dialogOptions.loadAllTextures)
				
				index = self.noeWnd.createCheckBox("Convert Textures", 10, 715, 130, 30, self.checkConvTexCheckbox)
				self.convTexCheckbox = self.noeWnd.getControlByIndex(index)
				self.convTexCheckbox.setChecked(dialogOptions.doConvertTex)
				
				index = self.noeWnd.createCheckBox("Collapse Bones", 150, 715, 120, 30, self.checkReparentCheckbox)
				self.reparentCheckbox = self.noeWnd.getControlByIndex(index)
				self.reparentCheckbox.setChecked(dialogOptions.reparentHelpers)
				
				index = self.noeWnd.createCheckBox("Import LODs", 10, 745, 100, 30, self.checkLODsCheckbox)
				self.LODsCheckbox = self.noeWnd.getControlByIndex(index)
				self.LODsCheckbox.setChecked(dialogOptions.doLODs)
				
				self.noeWnd.createButton("Select Animations", 150, 745, 200, 30, self.openMotlistDialogButton)

			self.noeWnd.createStatic("Game:", width-248, 690, 60, 20)
			index = self.noeWnd.createComboBox(width-200, 685, 180, 20, self.selectGameBoxItem, noewin.CBS_DROPDOWNLIST) #CB
			self.gameBox = self.noeWnd.getControlByIndex(index)
			
			self.noeWnd.createStatic("View:", width-240, 720, 60, 20)
			index = self.noeWnd.createComboBox(width-200, 715, 180, 20, self.selectLocalBoxItem, noewin.CBS_DROPDOWNLIST) #CB
			self.localBox = self.noeWnd.getControlByIndex(index)
			
			self.noeWnd.createStatic("Scale:", width-145, 750, 60, 20)
			index = self.noeWnd.createEditBox(width-100, 750, 80, 20, str(fDefaultMeshScale), self.inputGlobalScaleEditBox, False) #EB
			self.globalScaleEditBox = self.noeWnd.getControlByIndex(index)
			
			self.noeWnd.createButton("Load", 5, height-70, width-160, 30, self.openOptionsButtonLoadEntry)
			#self.noeWnd.createButton("Select Animations", width-240, height-70, 130, 30, self.openMotlistDialogButton)
			self.noeWnd.createButton("Cancel", width-96, height-70, 80, 30, self.openOptionsButtonCancel)
			
			self.setLoadList(self.loadItems)
			self.setPakList()
			self.setGameBox(self.gameBox)
			self.setLocalBox(self.localBox)
			
			self.noeWnd.doModal()
	
class openOptionsDialogExportWindow:
	
	def __init__(self, width, height, args):
		self.width = width
		self.height = height
		self.filepath = args.get("filepath") or ""
		self.texformat = args.get("texformat") or 98
		self.exportType = args.get("exportType") or os.path.splitext(rapi.getOutputName())[-1]
		self.sourceList = args.get("sourceList") or getSameExtFilesInDir(self.filepath)
		self.currentIdx = 0
		self.doWriteBones = False
		self.doRewrite = False
		self.doCancel = True
		self.failed = False
		self.doVFX = noesis.optWasInvoked("-vfx")
		self.indices = []
		self.LODDist = 0.02667995
		self.flag = -1
		
	def openOptionsVFXCheckbox(self, noeWnd, controlId, wParam, lParam):
		self.doVFX = not self.doVFX
		self.vfxCheckbox.setChecked(self.doVFX)
		
	def openOptionsButtonRewrite(self, noeWnd, controlId, wParam, lParam):
		self.doCancel = False
		self.doRewrite = True
		self.noeWnd.closeWindow()
	
	def openOptionsButtonExport(self, noeWnd, controlId, wParam, lParam):
		self.doCancel = False
		self.noeWnd.closeWindow()
		
	def openOptionsButtonExportBones(self, noeWnd, controlId, wParam, lParam):
		self.doCancel = False
		self.doWriteBones = True
		self.noeWnd.closeWindow()
		
	def openOptionsButtonCancel(self, noeWnd, controlId, wParam, lParam):
		self.noeWnd.closeWindow()
		
	def openBrowseMenu(self, noeWnd, controlId, wParam, lParam):
		filepath = noesis.userPrompt(noesis.NOEUSERVAL_FILEPATH, "Export over " + self.exportType.upper(), "Choose a " + self.exportType.upper() + " file to export over", self.filepath, None)
		if filepath:
			self.filepath = filepath
			#self.meshFile.setText(self.filepath)
			#if rapi.checkFileExists(filepath):
			self.clearComboBoxList()
			self.sourceList = getSameExtFilesInDir(self.filepath)
			self.setComboBoxList(self.meshFileList, self.filepath)
			
	def openOptionsButtonCancel(self, noeWnd, controlId, wParam, lParam):
		self.noeWnd.closeWindow()
	
	def inputMeshFileEditBox(self, noeWnd, controlId, wParam, lParam):
		self.meshEditText = self.meshFile.getText()
		self.meshFile.setText(self.meshEditText)
		if rapi.checkFileExists(self.meshEditText):
			self.filepath = self.meshEditText
			self.clearComboBoxList()
			self.sourceList = getSameExtFilesInDir(self.filepath)
			self.setComboBoxList(self.meshFileList, self.filepath)
		
	def inputFlagEditBox(self, noeWnd, controlId, wParam, lParam):
		if self.FlagBox.getText() != "":
			self.flag = int(self.FlagBox.getText())
		
	def inputLODDistEditBox(self, noeWnd, controlId, wParam, lParam):
		self.LODDist = float(self.LODEditBox.getText())
	
	def selectTexListItem(self, noeWnd, controlId, wParam, lParam):
		self.currentIdx = self.texType.getSelectionIndex()
		self.texformat = self.indices[self.currentIdx]
		filepath = rapi.getOutputName()
		filename = rapi.getExtensionlessName(filepath)
		self.outputFileName = filepath.replace(filename, filename + "." + str(self.texformat))
		print(self.outputFileName)
		
	def selectSourceListItem(self, noeWnd, controlId, wParam, lParam):
		self.currentIdx = self.meshFileList.getSelectionIndex()
		if self.sourceList and self.currentIdx:
			self.filepath = self.sourceList[self.currentIdx]
	
	def clearComboBoxList(self, list_object=None):
		#list_object = list_object or self.meshFileList
		for item in self.sourceList:
			self.meshFileList.removeString(item)
		#list_object.resetContent()
		
	def setComboBoxList(self, list_object=None, current_item=None):
		for item in self.sourceList:
			self.meshFileList.addString(item)
		self.meshFileList.selectString(current_item)
		self.currentIdx = self.meshFileList.getSelectionIndex()
	
	def create(self, width=None, height=None):
		width = width or self.width
		height = height or self.height
		self.noeWnd = noewin.NoeUserWindow("RE Engine MESH Options", "HTRAWWindowClass", width, height) 
		noeWindowRect = noewin.getNoesisWindowRect()
		if noeWindowRect:
			windowMargin = 100
			self.noeWnd.x = noeWindowRect[0] + windowMargin
			self.noeWnd.y = noeWindowRect[1] + windowMargin  
		return self.noeWnd.createWindow()
		
	def createMeshWindow(self, width=None, height=None):
		width = width or self.width
		height = height or self.height
		if self.create(width, height):
			row1_y = 0
			row2_y = 30
			exportRow_y = 60
			#row4_y = 100
			self.noeWnd.setFont("Futura", 14)
			
			#self.noeWnd.createStatic("Export Over Mesh", 5, row1_y, 140, 20)
			#index = self.noeWnd.createEditBox(5, 25, width-20, 20, self.filepath, self.inputMeshFileEditBox)
			#self.meshFile = self.noeWnd.getControlByIndex(index)
			
			index = self.noeWnd.createCheckBox("VFX Mesh", 5, row1_y, 80, 30, self.openOptionsVFXCheckbox)
			self.vfxCheckbox = self.noeWnd.getControlByIndex(index)
			self.vfxCheckbox.setChecked(self.doVFX)
			
			index = self.noeWnd.createComboBox(5, row2_y, width-20, 20, self.selectSourceListItem, noewin.CBS_DROPDOWNLIST)
			self.meshFileList = self.noeWnd.getControlByIndex(index)
			self.setComboBoxList(self.meshFileList, self.filepath)
			
			self.noeWnd.createButton("Browse", 5, exportRow_y, 80, 30, self.openBrowseMenu)
			if rapi.checkFileExists(self.filepath):
				self.noeWnd.createButton("Export", width-416, exportRow_y, 80, 30, self.openOptionsButtonExport)
				self.noeWnd.createButton("Export New Bones", width-326, exportRow_y, 130, 30, self.openOptionsButtonExportBones)
			self.noeWnd.createButton("Rewrite", width-186, exportRow_y, 80, 30, self.openOptionsButtonRewrite)
			self.noeWnd.createButton("Cancel", width-96, exportRow_y, 80, 30, self.openOptionsButtonCancel)
			
			
			self.noeWnd.createStatic("Rewrite Options:", 450, 100, 140, 20)
			self.noeWnd.createStatic("Flag:", 5, 130, 140, 20)
			index = self.noeWnd.createEditBox(45, 125, 40, 30, "", self.inputFlagEditBox, False)
			self.FlagBox = self.noeWnd.getControlByIndex(index)
			
			self.noeWnd.createStatic("LOD0 Factor:", 775, 130, 140, 20)
			index = self.noeWnd.createEditBox(885, 125, 100, 30, str(self.LODDist), self.inputLODDistEditBox, False)
			self.LODEditBox = self.noeWnd.getControlByIndex(index)
			
			self.noeWnd.doModal()
		else:
			print("Failed to create Noesis Window")
			self.failed = True
			
	def createTexWindow(self, width=None, height=None):
		width = width or self.width
		height = height or self.height
		if self.create(width, height):
			index = self.noeWnd.createComboBox(5, 5, 180, 20, self.selectTexListItem, noewin.CBS_DROPDOWNLIST)
			self.texType = self.noeWnd.getControlByIndex(index)
			for fmt in tex_format_list:
				fmtName = tex_format_list[fmt]
				self.texType.addString(fmtName)
				self.indices.append(fmt)
				if fmt == self.texformat:
					self.texType.selectString(fmtName)
					self.currentIdx = len(self.indices)
			self.noeWnd.createButton("Import", 190, 5, 80, 30, self.openOptionsButtonImport)
			self.noeWnd.createButton("Cancel", 190, 40, 80, 30, self.openOptionsButtonCancel)
			self.noeWnd.doModal()
		else:
			print("Failed to create Noesis Window")
			self.failed = True
			
def UVSLoadModel(data, mdlList):
	global sGameName
	bs = NoeBitStream(data)
	magic = bs.readUInt()
	textureNum = bs.readUInt()
	sequenceNum = bs.readUInt()
	patternNum = bs.readUInt()
	attribute = bs.readUInt()
	reserve = bs.readUInt()
	texturePtr = bs.readUInt64()
	sequencePtr = bs.readUInt64()
	
	patternPtr = bs.readUInt64()
	stringPtr = bs.readUInt64()
		
	uvsTexList = []
	uvsMatList = []
	textures = []
	
	bs.seek(texturePtr)
	texFile = ""
	sGameName = "RE2"
	ext = ".10"
	aspectRatios = []
	for i in range(textureNum):
		aspectRatios.append((1,1))
		mStateHolder = bs.readUInt64()
		mDataPtr = bs.readUInt64()
		mTextureHandleTbl = [bs.readUInt64(), bs.readUInt64(), bs.readUInt64()]
		Name = readUnicodeStringAt(bs, stringPtr + mDataPtr * 2)
		textures.append([mStateHolder, mDataPtr, mTextureHandleTbl, Name])
		
		if texFile != 0:
			texFile, ext = forceFindTexture(Name, ext)
			if texFile != 0:
				textureData = rapi.loadIntoByteArray(texFile)
				matName = rapi.getExtensionlessName(rapi.getExtensionlessName(rapi.getLocalFileName(texFile)))
				noetex = texLoadDDS(textureData, uvsTexList, matName)
				if noetex:
					aspectRatios[len(aspectRatios)-1] = (noetex.width / noetex.height, 1)
					noetex.name = matName
					uvsMatList.append(NoeMaterial(matName, texFile)) 
	
	bs.seek(sequencePtr)
	
	for i in range(sequenceNum):
		ctx = rapi.rpgCreateContext()
		#print ("sequence", bs.tell())
		patternCount = bs.readUInt()
		patternTbl = bs.readUInt()
		pos = bs.tell()
		
		UVs = []
		patterns = []
		bs.seek(patternPtr + patternTbl*32)
		for j in range(patternCount):
			#print("sequence at", bs.tell())
			uvTrans = bs.readUInt64()
			top = bs.readFloat()
			left = bs.readFloat()
			bottom = bs.readFloat()
			right = bs.readFloat()
			textureIndex = bs.readInt()
			cutoutUVCount = bs.readInt()
			patterns.append([uvTrans, left, top, right, bottom, textureIndex, cutoutUVCount])
			topLeft = (top, left, 0)
			bottomLeft = (bottom, left, 0)
			topRight = (top, right, 0)
			bottomRight = (bottom, right, 0)
			UVs = [topLeft, bottomRight, bottomLeft, topRight, bottomRight, topLeft]
			cutOutUVs = []
			for k in range(cutoutUVCount):
				cutoutUV = (bs.readFloat(), bs.readFloat(), 0)
				cutOutUVs.append(cutoutUV)
			cutOutUVsFaces = []
			for k in range(len(cutOutUVs)):
				if k == len(cutOutUVs) - 2:
					cutOutUVsFaces.extend([cutOutUVs[k], cutOutUVs[k+1], cutOutUVs[0]])
				elif k == len(cutOutUVs) - 1:
					cutOutUVsFaces.extend([cutOutUVs[k], cutOutUVs[0], cutOutUVs[1]])
				else:
					cutOutUVsFaces.extend([cutOutUVs[k], cutOutUVs[k+1], cutOutUVs[k+2]])
			UVs.extend(cutOutUVsFaces)
			rapi.rpgSetTransform((NoeVec3((1,0,0)), NoeVec3((0,-1,0)), NoeVec3((0,0,-1)), NoeVec3((0,0,0)))) 
			rapi.rpgSetName("Sequence" + str(i) + "_Pattern_" + str(j))
			if len(uvsMatList) > textureIndex:
				rapi.rpgSetMaterial(uvsMatList[textureIndex].name)
			rapi.immBegin(noesis.RPGEO_TRIANGLE)
			#print ("AR is", aspectRatios[textureIndex][0], aspectRatios[textureIndex][1])
			for k in range(0, len(UVs)):
				stretched = [UVs[k][0] * aspectRatios[textureIndex][0], UVs[k][1] * aspectRatios[textureIndex][1], 0]
				rapi.immUV2(UVs[k])
				rapi.immVertex3(stretched)
			rapi.immEnd()
			
		mdl = rapi.rpgConstructModel()
		if uvsTexList and uvsMatList:
			mdl.setModelMaterials(NoeModelMaterials(uvsTexList, uvsMatList)) 
		mdlList.append(mdl)
		rapi.rpgClearBufferBinds() 
		
		bs.seek(pos)
	return 1

def SCNCheckType(data):
	bs = NoeBitStream(data)
	magic = bs.readUInt()
	if magic == 5129043:
		return 1
	else: 
		print("Fatal Error: Unknown file magic: " + str(hex(magic) + " expected 'SCN '!"))
		return 0

def SCNLoadModel(data, mdlList):
	
	global sGameName
	fName = rapi.getInputName().upper()
	guessedName = "RE8" if "RE8" in fName else "RE7" if "RE7" in fName else "RE2" if "RE2" in fName else "RE3" if "RE3" in fName else "RE7" if "RE7" in fName else "SF6" if "SF6" in fName else "MHRSunbreak" if "MHR" in fName else "RE4" if "RE4" in fName else "DMC5"
	guessedName = guessedName + "RT" if (guessedName + "RT") in fName else guessedName
	inputName = noesis.userPrompt(noesis.NOEUSERVAL_FILEPATH, "SCN Import", "Input the game name", guessedName, None)
	if not inputName: 
		return 0
	inputName = inputName.upper()
	isRTRemake = (inputName != "RE7RT" and "RT" in inputName)
	inputName = inputName.replace("RT", "") if isRTRemake else inputName
	if inputName not in formats:
		print ("Not a valid game!")
		return 0
	sGameName = inputName
	current_pak_location = LoadExtractedDir(sGameName)
	sGameName = "RERT" if isRTRemake else sGameName
	print("Loading mesh/mdf/tex files from," current_pak_location)
	
	def getAlignedOffset(tell, alignment):
		if alignment == 2: return tell + (tell % 2)
		elif alignment == 4: return (tell+3) & 0xFFFFFFFFFFFFFFFC
		elif alignment == 8: return (tell+7) & 0xFFFFFFFFFFFFFFF8
		elif alignment == 16: return (tell+15) & 0xFFFFFFFFFFFFFFF0
		else: return tell
	
	def readByteAndReturn(bs):
		output = bs.readByte()
		bs.seek(-1,1)
		return output
	
	def detectedFloat(bs):
		if bs.tell() + 4 > bs.getSize():
			return False
		flt = abs(bs.readFloat())
		return (flt == 0 or (flt >= 0.000000001 and flt <= 100000000.0))
	
	def detectedBools(bs, atAddress):
		returnPos = bs.tell()
		nonBoolTotal = 0
		bs.seek(atAddress) #seek_set
		for i in range(4):
			if abs(bs.readByte()) > 1:
				nonBoolTotal += 1
		bs.seek(returnPos)
		return (nonBoolTotal == 0)
	
	def detectedXform(bs):
		if bs.tell() + 32 >= bs.getSize():
			return False
		returnPos = bs.tell()
		detected = True
		bs.seek(getAlignedOffset(returnPos, 16))
		for i in range(12):
			if not detectedFloat(bs) and (i < 4 or i > 7): #Skip rotation, as valid quaternions can have values like 1.02e^-40
				detected = False
				break
		bs.seek(returnPos)
		return detected
 
	def detectedString(bs, offset):
		returnPos = bs.tell()
		result = False
		bs.seek(offset)
		if bs.readByte() != 0 and bs.readByte() == 0 and bs.readByte() != 0 and bs.readByte() == 0  and bs.readByte() != 0 and bs.readByte() == 0:
			result = True
		bs.seek(returnPos)
		return result

	def redetectStringBehind(bs, is_second_time):
		pos = bs.tell()
		slash_detected = False
		if detectedString(bs, bs.tell()):
			while detectedString(bs, bs.tell()):
				bs.seek(-2, 1)
				slash_detected = slash_detected or ((readByteAndReturn(bs)) == 47)
			bs.seek(-2, 1)
		if not is_second_time and detectedString(bs, bs.tell()):
			bs.seek(-10, 1)
			redetectStringBehind(bs, True)
			if not detectedString(bs, bs.tell()+4):
				bs.seek(pos)
		if slash_detected:
			bs.seek(pos)
	
	viaGameObject = namedtuple('viaGameObject', ['Name', 'Tag', 'DrawSelf', 'UpdateSelf', 'TimeScale'])
	
	def readViaGameObject(bs, timescale_offset):
		bs.seek(getAlignedOffset(bs.tell(), 4)+4)
		Name = ReadUnicodeString(bs)
		bs.seek(getAlignedOffset(bs.tell(), 4)+4)
		Tag = ReadUnicodeString(bs)
		DrawSelf = bs.readByte()
		UpdateSelf = bs.readByte()
		bs.seek(timescale_offset)
		TimeScale = bs.readFloat()
		return viaGameObject(Name, Tag, DrawSelf, UpdateSelf, TimeScale)
	
	viaTransform = namedtuple('viaTransform', ['LocalPosition', 'LocalRotation', 'LocalScale', 'ParentBoneSize', 'ParentBone', 'SameJointsConstraints', 'AbsoluteScaling'])

	def readViaTransform(bs):
		bs.seek(getAlignedOffset(bs.tell(), 16))
		LocalPosition = NoeVec3((bs.readFloat(), bs.readFloat(), bs.readFloat()))
		bs.seek(4,1)
		LocalRotation = NoeQuat((bs.readFloat(), bs.readFloat(), bs.readFloat(), bs.readFloat()))
		LocalScale = NoeVec3((bs.readFloat(), bs.readFloat(), bs.readFloat()))
		bs.seek(4,1)
		bs.seek(getAlignedOffset(bs.tell(), 4))
		ParentBoneSize = bs.readInt()
		ParentBone = ReadUnicodeString(bs)
		SameJointsConstraints = bs.readByte()
		AbsoluteScaling = bs.readByte()
		return viaTransform(LocalPosition, LocalRotation, LocalScale, ParentBoneSize, ParentBone, SameJointsConstraints, AbsoluteScaling)
	
	def findMesh(bs, limitPoint):
		pos = bs.tell()
		meshPath = ReadUnicodeString(bs)
		output = [None, None]
		print("Scanning from", pos, "to", limitPoint, "for meshes")
		while meshPath.find(".mesh") == -1:
			if bs.tell() >= limitPoint: break
			while not detectedString(bs, bs.tell()):
				if bs.tell() >= limitPoint: break
				bs.seek(4,1)
			bs.seek(getAlignedOffset(bs.tell()-2, 4))
			meshPath = ReadUnicodeString(bs)
			bs.seek(getAlignedOffset(bs.tell()+1, 4))
		if meshPath.find(".mesh") != -1 and meshPath.lower().find("occ") == -1:
			meshPath = meshPath.replace("/", "\\")
			meshPath = current_pak_location + meshPath + formats[sGameName]["modelExt"]
			print("Found mesh:", meshPath, "\n")
			bs.seek(getAlignedOffset(bs.tell(), 4)+4)
			mdfPath = ReadUnicodeString(bs)
			if mdfPath.find(".mdf2"):
				mdfPath = mdfPath.replace("/", "\\")
				mdfPath = current_pak_location + mdfPath + formats[sGameName]["mdfExt"].replace(".mdf2", "")
			output = [meshPath, mdfPath]
		return output

	def findGameObjects(bs):
		GameObjectAddresses = []
		GameObjects = []
		fileSize = bs.getSize()
		pos = 0
		bs.seek(0)
		tester = bs.readUInt()
		while tester != 5919570 and bs.tell() + 4 < fileSize: #find "RSZ" magic
			bs.seek(-3,1)
			tester = bs.readUInt()
		if tester == 5919570:
			bs.seek(getAlignedOffset(bs.tell(), 4))
			while bs.tell() + 4 < fileSize:
				while tester != 3212836864 and bs.tell() + 4 < fileSize: # 00 00 80 BF , timescale -1.0
					tester = bs.readUInt()
				if pos < fileSize - 16 and detectedBools(bs, bs.tell()-8) and detectedXform(bs):
					#print ("\nFound possible GameObject at ", bs.tell())
					GameObjectAddresses.append(bs.tell())
				tester = bs.readUInt()
			
			if len(GameObjectAddresses) > 0:
				GameObjectAddresses.append(fileSize)
				for i in range(len(GameObjectAddresses)-2):
					bs.seek(GameObjectAddresses[i])
					transform = readViaTransform(bs)
					bs.seek(GameObjectAddresses[i]-36)
					pos2 = bs.tell()
					while not detectedString(bs, bs.tell()) and pos2 - bs.tell() < 12:
						bs.seek(-2,1)
					if pos2 - bs.tell() == 12:
						bs.seek(pos2)
					if detectedString(bs, bs.tell()):
						redetectStringBehind(bs, False)
					gameobject = readViaGameObject(bs, GameObjectAddresses[i]-4)
					if abs(gameobject.DrawSelf) <= 1 and abs(gameobject.UpdateSelf) <= 1 and gameobject.TimeScale == -1:
						meshMDF = findMesh(bs, GameObjectAddresses[i+1])
						GameObjects.append([gameobject, transform, meshMDF[0], meshMDF[1]])
						#print(bs.tell(), GameObjects[len(GameObjects)-1])
						
		return GameObjects
	
	ss = NoeBitStream(data)
	gameObjs = findGameObjects(ss)
	ctx = rapi.rpgCreateContext()
	
	totalTexList = []
	totalMatList = []
	totalBoneList = []
	totalRemapTable = []
	ids = []
	parentIds = []
	gameObjsDict = {}
	
	ss.seek(64+16)
	for i in range(readUIntAt(ss, 4)):
		ids.append(ss.readUInt())
		parentIds.append(ss.readUInt())
		ss.seek(24,1)
	#st4_708_0 garage
	counter = 0
	usedNames = {}
	print(gameObjs)
	for i, tup in enumerate(gameObjs):
		try:
			gameObjsDict[ids[i]] = tup
		except: 
			pass
		if tup[2] != None and rapi.checkFileExists(tup[2]) and tup[0].Name.find("AIMap") == -1:
			mesh = meshFile(rapi.loadIntoByteArray(tup[2]), tup[2])
			mesh.meshFile = tup[2]
			mesh.mdfFile = tup[3]
			mesh.pos = tup[1].LocalPosition
			mesh.rot = tup[1].LocalRotation
			mesh.scl = tup[1].LocalScale
			if i < len(parentIds):
				parentPosition = gameObjsDict[parentIds[i]][1].LocalPosition if parentIds[i] in gameObjsDict else NoeVec3((0,0,0))
				parentRotation = gameObjsDict[parentIds[i]][1].LocalRotation if parentIds[i] in gameObjsDict else NoeQuat((0,0,0,1))
				mesh.pos *= parentRotation.transpose()
				mesh.pos += parentPosition
				mesh.rot = parentRotation * mesh.rot
			mesh.fullTexList = totalTexList
			mesh.fullMatList = totalMatList
			mesh.fullBoneList = totalBoneList
			mesh.fullRemapTable = totalRemapTable
			mesh.name = tup[0].Name
			nameCtr = 1
			while mesh.name in usedNames:
				mesh.name = tup[0].Name + "#" + str(nameCtr)
				nameCtr += 1
			usedNames[mesh.name] = True
			mesh.loadMeshFile()
			counter += 1
	try:
		mdl = rapi.rpgConstructModelAndSort()
		mdl.setModelMaterials(NoeModelMaterials(totalTexList, totalMatList))
	except:
		mdl = NoeModel()
		
	mdl.setBones(totalBoneList)
	collapseBones(mdl)
		
	mdlList.append(mdl)
	print("\nLoaded", counter, "MESH files comprised of", len(mdl.meshes), "submeshes")
	
	return 1
	
	
	
	
BoneHeader = namedtuple("BoneHeader", "name pos rot index parentIndex hash mat")

BoneClipHeader = namedtuple("BoneClipHeader", "boneIndex trackFlags boneHash trackHeaderOffset")

BoneTrack = namedtuple("BoneTrack", "flags keyCount frameRate maxFrame frameIndOffs frameDataOffs unpackDataOffs")

Unpacks = namedtuple("Unpacks", "max min")

UnpackVec = namedtuple("UnpackVec", "x y z w")

def readPackedBitsVec3(packedInt, numBits):
	limit = 2**numBits-1
	x = ((packedInt >> 0) 		    & limit) / limit
	y = ((packedInt >> (numBits*1)) & limit) / limit
	z = ((packedInt >> (numBits*2)) & limit) / limit
	return NoeVec3((x, y, z))
	
def convertBits(packedInt, numBits):
	return packedInt / (2**numBits-1)	

def skipToNextLine(bs):
	bs.seek(bs.tell() + 16 - (bs.tell() % 16))

def wRot(quat3):
	RotationW = 1.0 - (quat3[0] * quat3[0] + quat3[1] * quat3[1] + quat3[2] * quat3[2]);
	if RotationW > 0:
		return math.sqrt(RotationW)
	return 0

class motFile:
	
	def __init__(self, dataBytesArray, motlist=[], start=0):
		self.bs = NoeBitStream(dataBytesArray)
		bs = self.bs
		self.start = start
		self.anim = None
		self.frameCount = 0
		self.motlist = motlist
		self.bones = []
		self.version = bs.readUInt()
		bs.seek(12)
		self.motSize = bs.readUInt()
		self.offsToBoneHdrOffs = bs.readUInt64()
		self.boneHdrOffset = 0
		self.boneClipHdrOffset = bs.readUInt64()
		bs.seek(8,1)
		if self.version >= 456:
			bs.seek(8,1)
			clipFileOffset = bs.readUInt64()
			jmapOffset = bs.readUInt64()
			exDataOffset  = bs.readUInt64()
			bs.seek(16,1)
		else:
			self.jmapOffset = bs.readUInt64()
			self.clipFileOffset = bs.readUInt64()
			bs.seek(16,1)
			self.exDataOffset = bs.readUInt64()
		nameOffs = bs.readUInt64()
		self.name = readUnicodeStringAt(bs, nameOffs)
		self.frameCount = bs.readFloat()
		self.name += " (" + str(int(self.frameCount)) + " frames)"
		self.blending = bs.readFloat()
		self.uknFloat0 = bs.readFloat()
		self.uknFloat0 = bs.readFloat()
		self.boneCount = bs.readShort()
		self.boneClipCount = bs.readShort()
		self.clipCount = bs.readByte()
		self.uknCount = bs.readByte()
		self.frameRate = bs.readShort()
		self.uknCount2 = bs.readShort()
		self.ukn3 = bs.readShort()
		self.boneHeaders = []
		self.boneClipHeaders = []
		self.kfBones = []
		self.doSkip = False
		
	def checkIfSyncMot(self, other):
		return (self.frameCount == other.frameCount)
		'''if self.frameCount == other.frameCount:
			boneNames = [self.motlist.bones[kfBone.boneIndex].name.lower() for kfBone in self.kfBones]
			otherBoneNames = [other.motlist.bones[kfBone.boneIndex].name.lower() for kfBone in other.kfBones]
			counter = 0
			for boneName in boneNames:
				if boneName in otherBoneNames:
					counter += 1
			return (counter / len(boneNames) < 0.25)'''
				
	
	def readFrame(self, ftype, flags, unpacks):
		bs = self.bs
		compression = flags & 0xFF000
		if ftype=="pos" or ftype=="scl":
			defScaleVec = NoeVec3((fDefaultMeshScale, fDefaultMeshScale, fDefaultMeshScale))
			if compression == 0x00000:
				output = NoeVec3((bs.readFloat(), bs.readFloat(), bs.readFloat())) * defScaleVec
			elif compression == 0x20000:
				rawVec = readPackedBitsVec3(bs.readUShort(), 5)
				if self.version <= 65:
					output = NoeVec3((unpacks.max.x * rawVec[0] + unpacks.min.x, unpacks.max.y * rawVec[1] + unpacks.min.z, unpacks.max.y * rawVec[2] + unpacks.min.z)) * defScaleVec
				else:
					output = NoeVec3((unpacks.max.x * rawVec[0] + unpacks.max.w, unpacks.max.y * rawVec[1] + unpacks.min.x, unpacks.max.z * rawVec[2] + unpacks.min.y)) * defScaleVec
			elif compression == 0x24000:
				x = y = z = unpacks.max.x * convertBits(bs.readUShort(), 16) + unpacks.min.x
				output = NoeVec3((x, y, z)) * defScaleVec
			elif compression == 0x44000:
				x = y = z = unpacks.max.x * bs.readFloat() + unpacks.min.x
				output = NoeVec3((x, y, z)) * defScaleVec
			elif compression == 0x40000 or (compression == 0x30000 and self.version <= 65):
				rawVec = readPackedBitsVec3(bs.readUInt(), 10)
				if self.version <= 65:
					output = NoeVec3((unpacks.max.x * rawVec[0] + unpacks.min.x, unpacks.max.y * rawVec[1] + unpacks.min.y, unpacks.max.z * rawVec[2] + unpacks.min.z)) * defScaleVec
				else:
					output = NoeVec3((unpacks.max.x * rawVec[0] + unpacks.max.w, unpacks.max.y * rawVec[1] + unpacks.min.x, unpacks.max.z * rawVec[2] + unpacks.min.y)) * defScaleVec
			elif compression == 0x70000:
				rawVec = readPackedBitsVec3(bs.readUInt64(), 21)
				output = NoeVec3((unpacks.max.x * rawVec[0] + unpacks.min.x, unpacks.max.y * rawVec[1] + unpacks.min.y, unpacks.max.z * rawVec[2] + unpacks.min.z)) * defScaleVec
			elif compression == 0x80000:
				rawVec = readPackedBitsVec3(bs.readUInt64(), 21)
				output = NoeVec3((unpacks.max.x * rawVec[0] + unpacks.max.w, unpacks.max.y * rawVec[1] + unpacks.min.x, unpacks.max.z * rawVec[2] + unpacks.min.y)) * defScaleVec
			elif (compression == 0x31000 and self.version <= 65) or (compression == 0x41000 and self.version >= 78): #LoadVector3sXAxis
				output = NoeVec3((bs.readFloat(), unpacks.max.y, unpacks.max.z)) * defScaleVec
			elif (compression == 0x32000 and self.version <= 65) or (compression == 0x42000 and self.version >= 78): #LoadVector3sYAxis
				output = NoeVec3((unpacks.max.x, bs.readFloat(), unpacks.max.z)) * defScaleVec
			elif (compression == 0x33000 and self.version <= 65) or (compression == 0x43000 and self.version >= 78): #LoadVector3sZAxis
				output = NoeVec3((unpacks.max.x, unpacks.max.y, bs.readFloat())) * defScaleVec
			elif compression == 0x21000:
				output = NoeVec3((unpacks.max.x * convertBits(bs.readUShort(), 16) + unpacks.max.y, unpacks.max.z, unpacks.max.w)) * defScaleVec
			elif compression == 0x22000:
				output = NoeVec3((unpacks.max.y, unpacks.max.x * convertBits(bs.readUShort(), 16) + unpacks.max.z, unpacks.max.w)) * defScaleVec
			elif compression == 0x23000:
				output = NoeVec3((unpacks.max.y, unpacks.max.z, unpacks.max.x * convertBits(bs.readUShort(), 16) + unpacks.max.w)) * defScaleVec
			else:
				print("Unknown", "Translation" if ftype=="pos" else "Scale", "type:", "0x"+'{:02X}'.format(compression))
				output = NoeVec3((0,0,0)) if ftype=="pos" else NoeVec3((100,100,100))
		elif ftype=="rot":
			if compression == 0x00000: #LoadQuaternionsFull
				output = NoeQuat((bs.readFloat(), bs.readFloat(), bs.readFloat(), bs.readFloat())).transpose()
			elif compression == 0xB0000 or compression == 0xC0000: #LoadQuaternions3Component
				#rawVec = [bs.readFloat(), bs.readFloat(), bs.readFloat()]
				#output = NoeQuat((rawVec[0], rawVec[1], rawVec[2], wRot(rawVec))).transpose()
				output = NoeQuat3((bs.readFloat(), bs.readFloat(), bs.readFloat())).toQuat().transpose()
			elif compression == 0x20000: #//LoadQuaternions5Bit RE3
				rawVec = readPackedBitsVec3(bs.readUShort(), 5)
				output = NoeQuat3((unpacks.max.x * rawVec[0] + unpacks.min.x, unpacks.max.y * rawVec[1] + unpacks.min.y, unpacks.max.z * rawVec[2] + unpacks.min.z)).toQuat().transpose()
			elif compression == 0x21000:
				output = NoeQuat3((unpacks.max.x * convertBits(bs.readUShort(), 16) + unpacks.max.y, 0, 0)).toQuat().transpose()
			elif compression == 0x22000:
				output = NoeQuat3((0, unpacks.max.x * convertBits(bs.readUShort(), 16) + unpacks.max.y, 0)).toQuat().transpose()
			elif compression == 0x23000:
				output = NoeQuat3((0, 0, unpacks.max.x * convertBits(bs.readUShort(), 16) + unpacks.max.y)).toQuat().transpose()
			elif compression == 0x30000 and self.version >= 78: #LoadQuaternions8Bit RE3
				rawVec = [convertBits(bs.readUByte(), 8), convertBits(bs.readUByte(), 8), convertBits(bs.readUByte(), 8)]
				output = NoeQuat3((unpacks.max.x * rawVec[0] + unpacks.min.x, unpacks.max.y * rawVec[1] + unpacks.min.y, unpacks.max.z * rawVec[2] + unpacks.min.z)).toQuat().transpose()
			elif compression == 0x30000:
				rawVec = readPackedBitsVec3(bs.readUInt(), 10)
				output = NoeQuat3((unpacks.max.x * rawVec[0] + unpacks.min.x, unpacks.max.y * rawVec[1] + unpacks.min.y, unpacks.max.z * rawVec[2] + unpacks.min.z)).toQuat().transpose()
			elif compression == 0x31000 or compression == 0x41000:
				output = NoeQuat3((bs.readFloat(), 0, 0)).toQuat().transpose()
			elif compression == 0x32000 or compression == 0x42000:
				output = NoeQuat3((0, bs.readFloat(), 0)).toQuat().transpose()
			elif compression == 0x33000 or compression == 0x43000:
				output = NoeQuat3((0, 0, bs.readFloat())).toQuat().transpose()
			elif compression == 0x40000: #LoadQuaternions10Bit RE3
				rawVec = readPackedBitsVec3(bs.readUInt(), 10)
				output = NoeQuat3((unpacks.max.x * rawVec[0] + unpacks.min.x, unpacks.max.y * rawVec[1] + unpacks.min.y, unpacks.max.z * rawVec[2] + unpacks.min.z)).toQuat().transpose()
			elif compression == 0x50000 and self.version <= 65: #LoadQuaternions16Bit RE2
				rawVec = [convertBits(bs.readUShort(), 16), convertBits(bs.readUShort(), 16), convertBits(bs.readUShort(), 16)]
				output = NoeQuat3((unpacks.max.x * rawVec[0] + unpacks.min.x, unpacks.max.y * rawVec[1] + unpacks.min.y, unpacks.max.z * rawVec[2] + unpacks.min.z)).toQuat().transpose()
			elif compression == 0x50000: #LoadQuaternions13Bit RE3
				rawBytes = [bs.readUByte(), bs.readUByte(), bs.readUByte(), bs.readUByte(), bs.readUByte()]
				retrieved = (rawBytes[0] << 32) | (rawBytes[1] << 24) | (rawBytes[2] << 16) | (rawBytes[3] << 8) | (rawBytes[4] << 0)
				rawVec = readPackedBitsVec3(retrieved, 13)
				output = NoeQuat3((unpacks.max.x * rawVec[0] + unpacks.min.x, unpacks.max.y * rawVec[1] + unpacks.min.y, unpacks.max.z * rawVec[2] + unpacks.min.z)).toQuat().transpose()
			elif compression == 0x60000: #LoadQuaternions16Bit RE3
				#output = NoeQuat((0,0,0,1))
				rawVec = [convertBits(bs.readUShort(), 16), convertBits(bs.readUShort(), 16), convertBits(bs.readUShort(), 16)]
				output = NoeQuat3((unpacks.max.x * rawVec[0] + unpacks.min.x, unpacks.max.y * rawVec[1] + unpacks.min.y, unpacks.max.z * rawVec[2] + unpacks.min.z)).toQuat().transpose()
			elif (compression == 0x70000 and self.version <= 65) or (compression == 0x80000 and self.version >= 78): #LoadQuaternions21Bit RE2 and LoadQuaternions21Bit RE3
				rawVec = readPackedBitsVec3(bs.readUInt64(), 21)
				output = NoeQuat3((unpacks.max.x * rawVec[0] + unpacks.min.x, unpacks.max.y * rawVec[1] + unpacks.min.y, unpacks.max.z * rawVec[2] + unpacks.min.z)).toQuat().transpose()
			elif compression == 0x70000 and self.version >= 78: #LoadQuaternions18Bit RE3
				rawBytes = [bs.readUByte(), bs.readUByte(), bs.readUByte(), bs.readUByte(), bs.readUByte(), bs.readUByte(), bs.readUByte()]
				retrieved = (rawBytes[0] << 48) | (rawBytes[1] << 40) | (rawBytes[2] << 32) | (rawBytes[3] << 24) | (rawBytes[4] << 16) | (rawBytes[5] << 8) | (rawBytes[6] << 0)
				rawVec = readPackedBitsVec3(retrieved, 18)
				output = NoeQuat3((unpacks.max.x * rawVec[0] + unpacks.min.x, unpacks.max.y * rawVec[1] + unpacks.min.y, unpacks.max.z * rawVec[2] + unpacks.min.z)).toQuat().transpose()
			else:
				print("Unknown Rotation type:", "0x"+'{:02X}'.format(compression))
				output = NoeQuat((0,0,0,1))
		return output
			
	# Used a lot for merging+moving skeletons of animations and meshes together:
	def readBoneHeaders(self):
		bs = self.bs
		boneHdrOffs = 0
		if self.offsToBoneHdrOffs:
			bs.seek(self.offsToBoneHdrOffs)
			self.boneHdrOffset = bs.readUInt64()
			count = bs.readUInt64()
			if self.boneHdrOffset and count == self.boneCount:
				boneHdrOffs = self.boneHdrOffset
		if boneHdrOffs:
			bs.seek(boneHdrOffs)
			for i in range(count):
				bs.seek(self.boneHdrOffset+80*i)
				boneName = readUnicodeStringAt(bs, bs.readUInt64())
				#boneName = self.motlist.meshBones[i].name if i < len(self.motlist.meshBones) else boneName #SF6 facial anims test
				parentOffset = bs.readUInt64()
				parentIndex = int((parentOffset-self.boneHdrOffset)/80) if parentOffset else -1
				bs.seek(16,1)
				translation = NoeVec4((bs.readFloat(), bs.readFloat(), bs.readFloat(), bs.readFloat()))
				quat = NoeQuat((bs.readFloat(), bs.readFloat(), bs.readFloat(), bs.readFloat())).transpose()
				index = bs.readUInt()
				boneHash = bs.readUInt()
				mat = quat.toMat43()
				mat[3] = translation.toVec3() * fDefaultMeshScale
				self.boneHeaders.append(BoneHeader(name=boneName, pos=translation, rot=quat, index=index, parentIndex=parentIndex, hash=boneHash, mat=mat))
			self.motlist.boneHeaders = self.motlist.boneHeaders or self.boneHeaders
		elif self.motlist.boneHeaders:
			self.boneHeaders = self.motlist.boneHeaders
		elif not self.motlist.searchedForBoneHeaders:
			self.motlist.findBoneHeaders()
		else:
			print("Failed to find bone headers:", self.name)
			return 0
			
		self.bones = []
		if not dialogOptions.dialog or not dialogOptions.dialog.args.get("mesh"):
			motlistBoneNames = [bone.name.lower() for bone in self.motlist.bones]
			for i, boneHeader in enumerate(self.boneHeaders):
				bone = NoeBone(len(self.bones), boneHeader.name, boneHeader.mat, self.boneHeaders[boneHeader.parentIndex].name if boneHeader.parentIndex != -1 else None, boneHeader.parentIndex)
				self.bones.append(bone)
				
			
			selfBoneNames = [bone.name.lower() for bone in self.bones]
			addedBones = []
			for i, bone in enumerate(self.bones):
				if bone.parentName and bone.parentName.lower() in motlistBoneNames:
					bone.parentIndex = motlistBoneNames.index(bone.parentName.lower())
				if bone.name.lower() not in motlistBoneNames:
					bone.index = len(self.motlist.bones)
					self.motlist.bones.append(bone)
					motlistBoneNames.append(bone.name.lower())
					addedBones.append(bone)
			for b, bone in enumerate(self.bones):
				if bone.parentIndex != -1 and bone.parentName.lower() in motlistBoneNames:
					mat = self.boneHeaders[b].mat
					bone.setMatrix(mat * self.motlist.bones[motlistBoneNames.index(bone.parentName.lower())].getMatrix())
					'''if bone in addedBones:
						mat = NoeMat43() #remove posed rotation from anim skeleton, and relocate bone to merged parent bone
						mat[3] = self.boneHeaders[b].pos.toVec3()'''
					'''if bone in addedBones:
						childBones = getChildBones(bone, self.motlist.bones, True)
						childMats = []
						for childBone in childBones:
							#print("moving child", childBone.name)
							oldIndex = selfBoneNames.index(childBone.name.lower())
							childMats.append(self.boneHeaders[oldIndex].mat * self.bones[selfBoneNames.index(childBone.parentName.lower())].getMatrix())'''

					'''if bone in addedBones:
						for c, childBone in enumerate(childBones):
							#childBone.setMatrix(childMats[c] * self.motlist.bones[motlistBoneNames.index(childBone.parentName.lower())].getMatrix())
							print("moving child", childBone.name)
							childBone.setMatrix(NoeMat43())'''
				
	def read(self):
		bs = self.bs
		
		if not self.boneHeaders:
			self.readBoneHeaders()
		
		bnClipSz = 24 if self.version==65 else 16 if self.version==43 else 12
		for i in range(self.boneClipCount):
			bs.seek(self.boneClipHdrOffset+bnClipSz*i)
			#print(i, "bnCLipHdr at", bs.tell()+self.start)
			if self.version == 65:
				index = bs.readUShort()
				trackFlags = bs.readUShort()
				boneHash = bs.readUInt()
				bs.seek(8,1)
				trackHeaderOffset = bs.readUInt64()
			else:
				index = bs.readUShort()
				trackFlags = bs.readUShort()
				boneHash = bs.readUInt()
				if  self.version == 43:
					trackHeaderOffset = bs.readUInt64()
				else:
					trackHeaderOffset = bs.readUInt()
			self.boneClipHeaders.append(BoneClipHeader(boneIndex=index, trackFlags=trackFlags, boneHash=boneHash, trackHeaderOffset=trackHeaderOffset))
			
		skipToNextLine(bs)
		self.boneClips = []
		for i in range(self.boneClipCount):
			boneClipHdr = self.boneClipHeaders[i]
			#if (i == 0 and self.boneHeaders[boneClipHdr.boneIndex].name != self.motlist.bones[0].name):
			#	print(self.name, "Ignoring all keyframes for ", self.boneHeaders[boneClipHdr.boneIndex].name)
			#	continue
			tracks = {"pos": None, "rot": None, "scl": None }
			bs.seek(boneClipHdr.trackHeaderOffset)
			for t in range(3):
				if boneClipHdr.trackFlags & (1 << t):
					flags = bs.readUInt()
					keyCount = bs.readUInt()
					frameRate = maxFrame = 0
					if self.version >= 78:
						frameIndOffs = bs.readUInt()
						frameDataOffs = bs.readUInt()
						unpackDataOffs = bs.readUInt()
					else:
						frameRate = float(bs.readUInt())
						maxFrame = bs.readFloat()
						frameIndOffs = bs.readUInt64()
						frameDataOffs = bs.readUInt64()
						unpackDataOffs = bs.readUInt64()
					newTrack = BoneTrack(flags=flags, keyCount=keyCount, frameRate=frameRate, maxFrame=maxFrame, frameIndOffs=frameIndOffs, frameDataOffs=frameDataOffs, unpackDataOffs=unpackDataOffs)
					if (boneClipHdr.trackFlags & (1)) and not tracks.get("pos"): 
						tracks["pos"] = newTrack
					elif (boneClipHdr.trackFlags & (1 << 1)) and not tracks.get("rot"): 
						tracks["rot"] = newTrack
					elif (boneClipHdr.trackFlags & (1 << 2)) and not tracks.get("scl"): 
						tracks["scl"] = newTrack
			if i == 0 and dialogOptions.dialog and dialogOptions.dialog.pak and self.boneHeaders[boneClipHdr.boneIndex].name != dialogOptions.dialog.pak.bones[0].name:
			#if i == 0 and self.boneHeaders[boneClipHdr.boneIndex].name != "root":
				print(self.name, ": Ignoring all keyframes for ", self.boneHeaders[boneClipHdr.boneIndex].name)
				tracks["pos"] = tracks["rot"] = tracks["scl"] = None #remove local root bone translations/rotations for mounted animations like facials 
			elif dialogOptions.doForceCenter and (self.boneHeaders[boneClipHdr.boneIndex].parentIndex == 0 or i == 0):
				print(self.name, ": Ignoring position keyframes for ", self.boneHeaders[boneClipHdr.boneIndex].name)
				tracks["pos"] = None
			self.boneClips.append(tracks)
			
		for i, boneClip in enumerate(self.boneClips):
			motlistBoneIndex = self.motlist.boneHashes.get(self.boneClipHeaders[i].boneHash)
			if motlistBoneIndex != None:
				kfBone = NoeKeyFramedBone(motlistBoneIndex)
				for ftype in ["pos", "rot", "scl"]:
					fHeader = boneClip.get(ftype)
					if fHeader:
						keyCompression = fHeader.flags >> 20
						keyReadFunc = bs.readUInt if keyCompression==5 else bs.readUByte if keyCompression==2 else bs.readUShort
						bs.seek(fHeader.frameIndOffs)
						keyTimes = []
						for k in range(fHeader.keyCount):
							keyTimes.append(keyReadFunc() if fHeader.frameIndOffs else 0)
						if fHeader.unpackDataOffs:
							bs.seek(fHeader.unpackDataOffs)
							unpackMax = UnpackVec(x=bs.readFloat(), y=bs.readFloat(), z=bs.readFloat(), w=bs.readFloat())
							unpackMin = UnpackVec(x=bs.readFloat(), y=bs.readFloat(), z=bs.readFloat(), w=bs.readFloat())
						else:
							unpackMax = unpackMin = UnpackVec(x=0, y=0, z=0, w=0)
						unpackValues = Unpacks(max=unpackMax, min=unpackMin)
						frames = []
						bs.seek(fHeader.frameDataOffs)
						for f in range(fHeader.keyCount):
							frame = self.readFrame(ftype, fHeader.flags, unpackValues)
							if ftype == "scl":
								frame /= 100
							kfValue = NoeKeyFramedValue(keyTimes[f], frame)
							frames.append(kfValue)
						if ftype == "pos": # and self.motlist.bones[motlistBoneIndex].parentIndex != 0:#kfBoneNames:
							kfBone.setTranslation(frames, noesis.NOEKF_TRANSLATION_VECTOR_3)
						elif ftype == "rot":
							kfBone.setRotation(frames, noesis.NOEKF_ROTATION_QUATERNION_4)
						elif ftype == "scl":
							kfBone.setScale(frames, noesis.NOEKF_SCALE_VECTOR_3)
				self.kfBones.append(kfBone)
		motEnd = bs.tell()
		
		#bs.seek(0)
		#self.bs = NoeBitStream(bs.readBytes(motEnd))
		#self.anim = NoeKeyFramedAnim(self.name, self.motlist.bones, self.kfBones, 1)
		

class motlistFile:
	
	def __init__(self, data, path=""):
		self.bs = NoeBitStream(data)
		bs = self.bs
		self.path = path
		self.bones = []
		self.boneHashes = {}
		self.boneHeaders = []
		self.anims = []
		self.mots = []
		self.meshBones = []
		self.searchedForBoneHeaders = False
		self.totalFrames = 0
		self.version = bs.readInt()
		bs.seek(16)
		pointersOffset = bs.readUInt64()
		motionIDsOffset = bs.readUInt64()
		self.name = readUnicodeStringAt(bs, bs.readUInt64())
		bs.seek(8, 1)
		numOffsets = bs.readUInt()
		bs.seek(pointersOffset)
		self.motionIDs = []
		self.pointers = []
		for i in range(numOffsets):
			bs.seek(pointersOffset + i*8)
			motAddress = bs.readUInt64()
			if motAddress and motAddress not in self.pointers and readUIntAt(bs, motAddress+4) == 544501613: # 'mot'
				self.pointers.append(motAddress)
				bs.seek(motAddress)
				mot = motFile(bs.readBytes(bs.getSize()-bs.tell()), self, motAddress)
				self.mots.append(mot)
				
	def findBoneHeaders(self):
		self.searchedForBoneHeaders = True
		for mot in self.mots:
			mot.readBoneHeaders()
			if self.boneHeaders:
				print("Using bone headers from", mot.name)
				break
				
	def readBoneHeaders(self, motNamesToLoad=[]):
		self.boneHashes = {}
		for mot in self.mots:
			if not motNamesToLoad or mot.name in motNamesToLoad:
				mot.readBoneHeaders()
		for i, bone in enumerate(self.bones):
			hash = hash_wide(bone.name, True)
			self.boneHashes[hash] = i #bone.index
				
	def read(self, motNamesToLoad=[]):
		bs = self.bs
		self.readBoneHeaders(motNamesToLoad)
		for i, mot in enumerate(self.mots):
			if not motNamesToLoad or mot.name in motNamesToLoad and not mot.doSkip:
				mot.read()
				
	def makeAnims(self, motNamesToLoad=[]):
		bs = self.bs
		motsToLoad = []
		#check for sync mots:
		for i, mot in enumerate(self.mots):
			if not motNamesToLoad or mot.name in motNamesToLoad and not mot.doSkip:
				motsToLoad.append(mot)
		if (dialogOptions.doSync or dialogOptions.doForceMergeAnims) and dialogOptions.motDialog and len(dialogOptions.motDialog.loadItems) > 0:
			allLoadItems = copy.copy(dialogOptions.motDialog.loadItems)
			allLoadPaths = copy.copy(dialogOptions.motDialog.fullLoadItems)
			for j, otherMotName in enumerate(dialogOptions.motDialog.loadItems):
				if "[ALL]" in otherMotName:
					for mot in dialogOptions.motDialog.loadedMlists[dialogOptions.motDialog.fullLoadItems[j]].mots:
						if mot.name not in allLoadItems:
							allLoadItems.append(mot.name)
							allLoadPaths.append(dialogOptions.motDialog.fullLoadItems[j])
			for i, mot in enumerate(motsToLoad):
				mlistBoneNames = [bone.name.lower() for bone in self.bones]
				for otherPath, otherMlist in dialogOptions.motDialog.loadedMlists.items():
					if otherMlist == self:
						continue
					otherMotNames = [otherMot.name for otherMot in otherMlist.mots]
					for j, otherMotName in enumerate(allLoadItems):
						if mot.motlist.path != allLoadPaths[j] and "[ALL]" not in otherMotName and otherMotName in otherMotNames and not otherMlist.mots[otherMotNames.index(otherMotName)].doSkip and (dialogOptions.doForceMergeAnims or mot.checkIfSyncMot(otherMlist.mots[otherMotNames.index(otherMotName)])):
							syncMot = otherMlist.mots[otherMotNames.index(otherMotName)]
							existingKfBoneNames = [self.bones[kfBone.boneIndex].name for kfBone in mot.kfBones]
							for b, kfBone in enumerate(syncMot.kfBones):
								bone = syncMot.motlist.bones[kfBone.boneIndex]
								if bone.name.lower() not in mlistBoneNames:
									bone.index = len(self.bones)
									self.bones.append(bone)
									mlistBoneNames.append(bone.name.lower())
								if (kfBone.hasAnyKeys() and (bone.name not in existingKfBoneNames or not mot.kfBones[existingKfBoneNames.index(bone.name)].hasAnyKeys())):
									kfBone.boneIndex = mlistBoneNames.index(bone.name.lower())
									mot.kfBones.append(kfBone)
							print("Merged animation ", syncMot.name, "into", mot.name)
							syncMot.doSkip = True
		motsByName = []	
		for i, mot in enumerate(motsToLoad):
			if not mot.doSkip:
				mot.anim = NoeKeyFramedAnim(mot.name, self.bones, mot.kfBones, 1)
				self.anims.append(mot.anim)
				motsByName.append(mot.name)
		if len(self.anims) > 0:
			print("\nImported", len(self.anims), "animations from motlist '", self.name, "':")
			for anim in self.anims:
				print(" @ " + str(int(self.totalFrames)), "	'", anim.name, "'")
				self.totalFrames += self.mots[motsByName.index(anim.name)].frameCount

def motlistCheckType(data):
	bs = NoeBitStream(data)
	magic = readUIntAt(bs, 4)
	if magic == 1953721453:
		return 1
	else: 
		print("Fatal Error: Unknown file magic: " + str(hex(magic) + " expected 'mlst'!"))
		return 0

def motlistLoadModel(data, mdlList):
	ctx = rapi.rpgCreateContext()
	
	dialogOptions.motDialog = None
	motlist = motlistFile(data, rapi.getInputName())
	mlDialog = openOptionsDialogImportWindow(None, None, {"motlist":motlist, "isMotlist":True})
	mlDialog.createMotlistWindow()
	
	mdl= NoeModel()
	
	if not mlDialog.isCancelled:
		mdl.setBones(mlDialog.pak.bones)
		collapseBones(mdl, 100)
		bones = list(mdl.bones)
		mdlBoneNames = [bone.name.lower() for bone in bones]
		sortedMlists = []
		for mlist in [mlDialog.loadedMlists[path] for path in mlDialog.fullLoadItems]:
			if mlist not in sortedMlists:
				sortedMlists.append(mlist)
		for mlist in sortedMlists:
			mlist.readBoneHeaders(mlDialog.loadItems)
			for bone in mlist.bones:
				if bone.name.lower() not in mdlBoneNames:
					bone.index = len(bones)
					bones.append(bone)
		anims = []
		for mlist in sortedMlists:
			mlist.bones = bones
			mlist.readBoneHeaders(mlDialog.loadItems)
			mlist.read(mlDialog.loadItems)
		for mlist in sortedMlists:
			mlist.makeAnims(mlDialog.loadItems)
			anims.extend(mlist.anims)
			
		mdl.setBones(bones)
		mdl.setAnims(anims)
		rapi.setPreviewOption("setAnimSpeed", "60.0")
	
	mdlList.append(mdl)
	
	return 1
	

isSF6 = False
isExoPrimal = False
BBskipBytes = numNodesLocation = LOD1OffsetLocation = normalsRecalcOffsLocation = bsHdrOffLocation = bsIndicesOffLocation = \
vBuffHdrOffsLocation = bonesOffsLocation = nodesIndicesOffsLocation = namesOffsLocation = floatsHdrOffsLocation = 0

def setOffsets(ver):
	global BBskipBytes, numNodesLocation, LOD1OffsetLocation, normalsRecalcOffsLocation, bsHdrOffLocation, bsIndicesOffLocation, \
	vBuffHdrOffsLocation, bonesOffsLocation, nodesIndicesOffsLocation, namesOffsLocation, floatsHdrOffsLocation
	BBskipBytes = 				8 	if ver == 1 else 0
	numNodesLocation = 			18 	if ver < 3 else 20
	LOD1OffsetLocation = 		24 	if ver < 3 else 32
	normalsRecalcOffsLocation = 56 	if ver < 3 else 64
	bsHdrOffLocation = 			64 	if ver < 3 else 56
	bsIndicesOffLocation = 		112 if ver < 3 else 128
	vBuffHdrOffsLocation = 		80 	if ver < 3 else 72
	bonesOffsLocation = 		48 	if ver < 3 else 104
	nodesIndicesOffsLocation = 	96 	if ver < 3 else 112
	namesOffsLocation = 		120 if ver < 3 else 144
	floatsHdrOffsLocation = 	72 	if ver < 3 else 96
	if isExoPrimal:
		nodesIndicesOffsLocation = 104
		namesOffsLocation = 136 

class meshFile(object): 

	def __init__(self, data, path=""):
		self.path = path or rapi.getInputName()
		self.inFile = NoeBitStream(data)
		self.boneList = []
		self.matNames = []
		self.groupIDs = []
		self.matHashes = []
		self.matList = []
		self.texList = []
		self.texNames = []
		self.missingTexNames = []
		self.texColors = []
		self.fullBoneList = []
		self.fullTexList = []
		self.fullMatList = []
		self.fullRemapTable = []
		self.setGameName()
		self.gameName = sGameName
		self.ver = formats[sGameName]["meshVersion"]
		self.mdfVer = formats[sGameName]["mdfVersion"]
		self.name = "LOD" if bShorterNames else "LODGroup"
		self.meshFile = None
		self.mdfFile = None
		self.pos = NoeVec3((0,0,0))
		self.rot = NoeQuat((0,0,0,1))
		self.scl = NoeVec3((1,1,1))
		self.uvBias = {}
		setOffsets(self.ver)
		
	def setGameName(self):
		global sGameName, bSkinningEnabled, isSF6, isExoPrimal
		sGameName = "RE2"
		meshVersion = readUIntAt(self.inFile, 4)
		isSF6 = isExoPrimal = False
		if meshVersion == 220822879:
			isSF6 = 2
			sGameName = "RE4"
		elif meshVersion == 220705151:
			isSF6 = True
			sGameName = "SF6"
		elif meshVersion == 22011900:
			isExoPrimal = True
			sGameName = "ExoPrimal"
		elif meshVersion == 21041600: # or self.path.find(".2109108288") != -1: #RE2RT + RE3RT, and RE7RT
			sGameName = "RE7RT" if self.path.find(".220128762") != -1 else "RERT"
		elif self.path.find(".1808282334") != -1:
			sGameName = "DMC5"
		elif self.path.find(".1902042334") != -1:  #386270720
			sGameName = "RE3"
		elif self.path.find(".2102020001") != -1:
			sGameName = "ReVerse"
		elif meshVersion == 2020091500 or self.path.find(".2101050001") != -1:
			sGameName = "RE8"
		elif (meshVersion == 2007158797 or self.path.find(".2008058288") != -1): #Vanilla MHRise
			sGameName = "MHRise"
		elif (meshVersion == 21061800 or self.path.find(".2109148288") != -1):  #MHRise Sunbreak version
			sGameName = "MHRSunbreak"
		
	'''MDF IMPORT ========================================================================================================================================================================'''
	def createMaterials(self, matCount):
		global bColorize, bPrintMDF, sGameName, sExportExtension
		
		doColorize = bColorize
		doPrintMDF = bPrintMDF
		noMDFFound = 0
		skipPrompt = 0
		
		modelExt = formats[sGameName]["modelExt"]
		texExt = formats[sGameName]["texExt"]
		mmtrExt = formats[sGameName]["mmtrExt"]
		nDir = formats[sGameName]["nDir"]
		mdfExt = formats[sGameName]["mdfExt"]
		extractedNativesPath = LoadExtractedDir(sGameName)
		
		#Try to find & save extracted game dir for later if extracted game dir is unknown
		if extractedNativesPath == "":
			dirName = GetRootGameDir(self.path)
			if (dirName.endswith("chunk_000\\natives\\" + nDir + "\\")):
				print ("Saving extracted natives path...")
				if SaveExtractedDir(dirName, sGameName):
					extractedNativesPath = dirName
					
		if extractedNativesPath != "":
			print ("Using this extracted natives path:", extractedNativesPath + "\n")
			
		#Try to guess MDF filename
		inputName = self.path #rapi.getInputName()
		isSCN = (rapi.getInputName().lower().find(".scn") != -1)
		if inputName.find(".noesis") != -1:
			inputName = rapi.getLastCheckedName()
			skipPrompt = 2
			doPrintMDF = 0
		elif dialogOptions.doLoadTex or isSCN: # len(self.fullMatList) > 0 or len(self.fullBoneList) > 0:
			skipPrompt = 2
			doPrintMDF = 0
		
		pathPrefix = inputName
		while pathPrefix.find("out.") != -1: 
			pathPrefix = pathPrefix.replace("out.",".")
		pathPrefix = pathPrefix.replace(".mesh", "").replace(modelExt,"").replace(".NEW", "")
		
		if sGameName == "ReVerse" and os.path.isdir(os.path.dirname(inputName) + "\\Material"):
			pathPrefix = (os.path.dirname(inputName) + "\\Material\\" + rapi.getLocalFileName(inputName).replace("SK_", "M_")).replace(".NEW", "")
			while pathPrefix.find("out.") != -1: 
				pathPrefix = pathPrefix.replace("out.",".")
			pathPrefix = pathPrefix.replace(".mesh" + modelExt,"")
			if not rapi.checkFileExists(pathPrefix + mdfExt):
				pathPrefix = pathPrefix.replace("00_", "")
			if not rapi.checkFileExists(pathPrefix + mdfExt):
				for item in os.listdir(os.path.dirname(pathPrefix + mdfExt)):
					if mdfExt == (".mdf2" + os.path.splitext(os.path.join(os.path.dirname(pathPrefix), item))[1]):
						pathPrefix = os.path.join(os.path.dirname(pathPrefix), item) #.replace(mdfExt, "")
						break
			
		similarityCounter = 0
		ogFileName = rapi.getLocalFileName(inputName)
		if not rapi.checkFileExists(pathPrefix + mdfExt):
			for item in os.listdir(os.path.dirname(pathPrefix + mdfExt)):
				if mdfExt == (".mdf2" + os.path.splitext(item)[1]):
					test = rapi.getLocalFileName(os.path.join(os.path.dirname(pathPrefix), item)).replace(mdfExt, "")
					sameCharCntr = 0
					for c, char in enumerate(test):
						if c < len(ogFileName) and char == ogFileName[c]:
							sameCharCntr += 1
					if sameCharCntr > similarityCounter:
						pathPrefix = os.path.join(os.path.dirname(pathPrefix), item).replace(mdfExt, "")
						similarityCounter = sameCharCntr
		materialFileName = pathPrefix + mdfExt
		
		if not (rapi.checkFileExists(materialFileName)):
			print(materialFileName, "does not exist!") 
			materialFileName = (pathPrefix + "_mat" + mdfExt)
		if not (rapi.checkFileExists(materialFileName)):
			materialFileName = (pathPrefix + "_00" + mdfExt)
		if not (rapi.checkFileExists(materialFileName)):
			if self.mdfVer >= 2: #sGameName == "RERT" or sGameName == "RE3" or sGameName == "ReVerse" or sGameName == "RE8" or sGameName == "MHRise":
				pathPrefix = extractedNativesPath + re.sub(r'.*stm\\', '', inputName)
			else:
				pathPrefix = extractedNativesPath + re.sub(r'.*x64\\', '', inputName) 
			pathPrefix = pathPrefix.replace(modelExt,"").replace(".mesh","")
			materialFileName = (pathPrefix + mdfExt)
			print (materialFileName)
			if not (rapi.checkFileExists(materialFileName)):
				materialFileName = (pathPrefix + "_mat" + mdfExt)
			if not (rapi.checkFileExists(materialFileName)):
				materialFileName = (pathPrefix + "_00" + mdfExt)
				
		if not (rapi.checkFileExists(materialFileName)):
			materialFileName = noesis.userPrompt(noesis.NOEUSERVAL_FILEPATH, "MDF File Not Found", "Manually enter the name of the MDF file or cancel.", os.path.join(os.path.dirname(inputName), rapi.getLocalFileName(materialFileName)) , None)
			if (materialFileName is None):
				print("No material file.")
				return
			elif not (rapi.checkFileExists(materialFileName)):
				noMDFFound = 1
			skipPrompt = 1
			
		msgName = materialFileName
		
		#Prompt for MDF load
		if not skipPrompt or (skipPrompt == 2 and not rapi.checkFileExists(materialFileName)):
			msgName = noesis.userPrompt(noesis.NOEUSERVAL_FILEPATH, "MDF File Detected", "Load materials? This may take some time.", materialFileName, None)
			if msgName is None:
				print("No material file.")
				return False
				
			'''if msgName.endswith(" -c"):
				print (msgName)
				doColorize = 1
				doPrintMDF = 0												
				msgName = msgName.replace(" -c", "")'''											
			
			if ((rapi.checkFileExists(msgName)) and (msgName.endswith(mdfExt))):
				materialFileName = msgName
			else:
				noMDFFound = 1
		
		if (bPopupDebug == 1):
			noesis.logPopup()
		
		#Save a manually entered natives directory path name for later
		if (msgName.endswith("\\natives\\" + nDir + "\\")) and (os.path.isdir(msgName)):
			print ("Attempting to write: ")
			if SaveExtractedDir(msgName, sGameName):
				extractedNativesPath = msgName
				
		if (noMDFFound == 1) or not (rapi.checkFileExists(materialFileName)):
			print("Failed to open material file.")
			return False
	
		texBaseColour = []
		texRoughColour = []
		texSpecColour = []
		texAmbiColour = []
		texMetallicColour = []
		texFresnelColour = []
			
		bs = rapi.loadIntoByteArray(materialFileName)
		bs = NoeBitStream(bs)
		#Magic, Unknown, MaterialCount, Unknown, Unknown
		matHeader = [bs.readUInt(), bs.readUShort(), bs.readUShort(), bs.readUInt(), bs.readUInt()]
		matCountMDF = matHeader[2]
		
		if matCountMDF != matCount and len(self.fullMatList) == 0:
			print ("MDF Checkerboard Error: MDF does not have the same material count as the MESH file!\n	MESH materials:", matCount, "\n	MDF Materials:", matCountMDF)
			return 0
		
		usedMats = [mat.name for mat in self.fullMatList]
		usedTexs = [tex.name for tex in self.fullTexList]
		
		#Parse Materials
		for i in range(matCountMDF):
			
			if self.mdfVer > 3: #isSF6 or isExoPrimal:
				bs.seek(0x10 + (i * 100))
			elif self.mdfVer > 2:#sGameName == "RERT" or sGameName == "ReVerse" or sGameName == "RE8" or sGameName == "MHRise":
				bs.seek(0x10 + (i * 80))
			else:
				bs.seek(0x10 + (i * 64))
			
			materialNamesOffset = bs.readUInt64()
			materialHash = bs.readInt()
			sizeOfFloatStr = bs.readUInt()
			floatCount = bs.readUInt()
			texCount = bs.readUInt()
			
			if self.mdfVer >= 3:
				bs.seek(8,1)
				
			shaderType = bs.readUInt()
			if self.mdfVer >= 4:
				uknSF6int = bs.readUInt()
				
			alphaFlag = bs.readUInt()
			
			if self.mdfVer >= 4:
				uknSF6int2 = bs.readUInt()
				uknSF6int3 = bs.readUInt()
				
			floatHdrOffs = bs.readUInt64()
			texHdrOffs = bs.readUInt64()
			if self.mdfVer >= 3:
				firstMtrlNameOffs = bs.readUInt64()
			floatStartOffs = bs.readUInt64()
			mmtr_PathOffs = bs.readUInt64()
			
			if self.mdfVer >= 4: #isSF6 or isExoPrimal:
				uknSF6offset = bs.readUInt64()
				
			bs.seek(materialNamesOffset)
			materialName = ReadUnicodeString(bs)
			bs.seek(mmtr_PathOffs)
			mmtrName = ReadUnicodeString(bs)
			hasTransparency = not not (((alphaFlag & ( 1 << 1 )) >> 1) or ((alphaFlag & ( 1 << 4 )) >> 4))
			
			if bPrintFileList:
				self.texNames.append(("natives/" + nDir + "/" + mmtrName + mmtrExt).lower())
				if not rapi.checkFileExists(extractedNativesPath + (mmtrName + mmtrExt).lower()) and not rapi.checkFileExists(self.rootDir + (mmtrName + mmtrExt).lower()) and rapi.getInputName().find("natives".lower()) != -1:
					self.missingTexNames.append("DOES NOT EXIST " + ("natives/" + nDir + "/" + mmtrName + mmtrExt).lower())
			
			if doPrintMDF:
				print(materialName + "[" + str(i) + "]\n")
			
			self.matNames.append(materialName)
			self.matHashes.append(materialHash)
			materialFlags = 0
			materialFlags2 = 0
			material = NoeMaterial(materialName, "")
			material.setDefaultBlend(0)
			#material.setBlendMode("GL_ONE", "GL_ONE")
		
			#Parse Textures
			textureInfo = []
			paramInfo = []
			
			bFoundBM = False
			bFoundNM = False
			bFoundSSSM = False
				
			bFoundBaseColour = False
			bFoundRoughColour = False
			bFoundSpecColour = False
			bFoundAmbiColour = False
			bFoundMetallicColour = False
			bFoundFresnelColour = False
			
			if doPrintMDF:
				print ("Material Properties:")
				
			for j in range(floatCount): # floats
				bs.seek(floatHdrOffs + (j * 0x18))
				paramInfo.append([bs.readUInt64(), bs.readUInt64(), bs.readUInt(), bs.readUInt()]) #dscrptnOffs[0], type[1], strctOffs[2], numFloats[3] 
				bs.seek(paramInfo[j][0])
				paramType = ReadUnicodeString(bs)
				
				colours = []
				if self.mdfVer >= 2: #sGameName == "RERT" or sGameName == "RE3" or sGameName == "ReVerse" or sGameName == "RE8" or sGameName == "MHRise" or sGameName == "SF6":
					bs.seek(floatStartOffs + paramInfo[j][2])
					if paramInfo[j][3] == 4:
						colours.append(NoeVec4((bs.readFloat(), bs.readFloat(), bs.readFloat(), bs.readFloat())))
					elif paramInfo[j][3] == 1:
						colours.append(bs.readFloat())
				else:
					bs.seek(floatStartOffs + paramInfo[j][3])
					if paramInfo[j][2] == 4:
						colours.append(NoeVec4((bs.readFloat(), bs.readFloat(), bs.readFloat(), bs.readFloat())))
					elif paramInfo[j][2] == 1:
						colours.append(bs.readFloat())
					
				if doPrintMDF:
					print(paramType + ":", colours)
				
				if paramType == "BaseColor" and not bFoundBaseColour:
					bFoundBaseColour = True
					texBaseColour.append(colours)
				if paramType == "Roughness" and not bFoundRoughColour:
					bFoundRoughColour = True
					texRoughColour.append(colours)
				if paramType == "PrimalySpecularColor" and not bFoundSpecColour:
					bFoundSpecColour = True
					texSpecColour.append(colours)
				if paramType == "AmbientColor" and not bFoundAmbiColour:
					bFoundAmbiColour = True
					texAmbiColour.append(colours)
				if paramType == "Metallic" and not bFoundMetallicColour:
					bFoundMetallicColour = True
					texMetallicColour.append(colours)
				if paramType == "Fresnel_DiffuseIntensity" and not bFoundFresnelColour:
					bFoundFresnelColour = True
					texFresnelColour.append(colours)
			
			#Append defaults
			if not bFoundBaseColour:
				texBaseColour.append(NoeVec4((1.0, 1.0, 1.0, 1.0)))
			if not bFoundRoughColour:
				texRoughColour.append(1.0)
			if not bFoundSpecColour:
				texSpecColour.append(NoeVec4((0.5, 0.5, 0.5, 0.5)))
			if not bFoundAmbiColour:
				texAmbiColour.append(NoeVec4((1.0, 1.0, 1.0, 1.0)))
			if not bFoundMetallicColour:
				texMetallicColour.append(1.0)
			if not bFoundFresnelColour:
				texFresnelColour.append(0.8)
			
			if doPrintMDF:
				print ("\nTextures for " + materialName + "[" + str(i) + "]" + ":")
			
			alreadyLoadedTexs = [tex.name for tex in self.fullTexList]
			alreadyLoadedMats = [mat.name for mat in self.fullMatList]
			secondaryDiffuse = ""
			
			for j in range(texCount): # texture headers
				
				if self.mdfVer >= 2: #sGameName == "RERT" or sGameName == "RE3" or sGameName == "ReVerse" or sGameName == "RE8" or sGameName == "MHRise" or sGameName == "SF6":
					bs.seek(texHdrOffs + (j * 0x20))
					textureInfo.append([bs.readUInt64(), bs.readUInt64(), bs.readUInt64(), bs.readUInt64()]) #TextureTypeOffset[0], uknBytes[1], TexturePathOffset[2], padding[3]
					if self.mdfVer >= 4: #isSF6 or isExoPrimal:
						bs.seek(8,1)
				else:
					bs.seek(texHdrOffs + (j * 0x18))
					textureInfo.append([bs.readUInt64(), bs.readUInt64(), bs.readUInt64()])
				bs.seek(textureInfo[j][0])
				textureType = ReadUnicodeString(bs)
				bs.seek(textureInfo[j][2])
				textureName = ReadUnicodeString(bs).replace("@", "")
				
				textureFilePath = ""
				texName = ""
				isNotMainTexture = False
				opacityName = ""
				extraParam = ""
				
				
				if bFoundSpecColour:
					material.setSpecularColor(texSpecColour[i])
				if bFoundAmbiColour:
					material.setAmbientColor(texAmbiColour[i])
				if bFoundMetallicColour:
					material.setMetal(texMetallicColour[i], 0.25)
				if bFoundRoughColour:
					material.setRoughness(texRoughColour[i], 0.25)
				if bFoundFresnelColour:
					material.setEnvColor(NoeVec4((1.0, 1.0, 1.0, texFresnelColour[i])))
				
				tmpExt = texExt
				for k in range(2):
					if not rapi.checkFileExists(textureFilePath):
						if (rapi.checkFileExists(self.rootDir + "streaming/" + textureName + tmpExt)):
							textureFilePath = self.rootDir + "streaming/" + textureName + tmpExt						
							texName = rapi.getLocalFileName(self.rootDir + "streaming/" + textureName).rsplit('.', 1)[0] + texOutputExt
									
						elif (rapi.checkFileExists(self.rootDir + textureName + tmpExt)):
							textureFilePath = self.rootDir + textureName + tmpExt
							texName = rapi.getLocalFileName(self.rootDir + textureName).rsplit('.', 1)[0] + texOutputExt
							if bPrintFileList and not (rapi.checkFileExists(self.rootDir + textureName + tmpExt)):
								self.missingTexNames.append("DOES NOT EXIST: " + (('natives/' + (re.sub(r'.*natives\\', '', textureFilePath)).lower()).replace("\\","/")).replace(extractedNativesPath,''))
							
						elif (rapi.checkFileExists(extractedNativesPath + "streaming/" + textureName + tmpExt)):
							textureFilePath = extractedNativesPath + "streaming/" + textureName + tmpExt
							texName = rapi.getLocalFileName(extractedNativesPath + "streaming/" + textureName).rsplit('.', 1)[0] + texOutputExt
									
						elif (rapi.checkFileExists(extractedNativesPath + textureName + tmpExt)):
							textureFilePath = extractedNativesPath + textureName + tmpExt
							texName = rapi.getLocalFileName(extractedNativesPath + textureName).rsplit('.', 1)[0] + texOutputExt
							if bPrintFileList and not (rapi.checkFileExists(extractedNativesPath + textureName + tmpExt)):
								self.missingTexNames.append("DOES NOT EXIST: " + ('natives/' + (re.sub(r'.*natives\\', '', textureFilePath)).lower()).replace("\\","/").replace(extractedNativesPath,''))
							
						else:
							textureFilePath = self.rootDir + textureName + tmpExt
							texName = rapi.getLocalFileName(self.rootDir + textureName).rsplit('.', 1)[0] + texOutputExt
							if bPrintFileList and not (textureFilePath.endswith("rtex" + tmpExt)) and (k==1 or sGameName.find("MHR") == -1):
								self.missingTexNames.append("DOES NOT EXIST: " + ('natives/' + (re.sub(r'.*natives\\', '', textureFilePath)).lower()).replace("\\","/").replace("streaming/",""))
						if "MHR" not in sGameName:
							break
						tmpExt += ".stm"
				
				bAlreadyLoadedTexture = (texName in alreadyLoadedTexs)
				bAlreadyLoadedMat = (materialName in alreadyLoadedMats)
						
				if bPrintFileList: #and rapi.getInputName().find("natives".lower()) != -1:
					if not (textureName.endswith("rtex")):
						newTexPath = ((('natives/' + (re.sub(r'.*natives\\', '', textureFilePath))).replace("\\","/")).replace(extractedNativesPath,'')).lower()
						self.texNames.append(newTexPath)
						if newTexPath.find('streaming') != -1:
							testPath = newTexPath.replace('natives/' + nDir + '/streaming/', '')
							if rapi.checkFileExists(self.rootDir + testPath) or rapi.checkFileExists(extractedNativesPath + testPath):
								self.texNames.append(newTexPath.replace('streaming/',''))
				
				#if (("BaseMetal" in textureType or "BaseDielectric" in textureType or "BaseAlpha" in textureType or "BaseShift" in textureType)) and not bFoundBM: #
				if "_alb" in texName.lower() and not bFoundBM: #goddamn RE8
					bFoundBM = True
					material.setTexture(texName)
					material.setDiffuseColor(texBaseColour[i])
					material.setSpecularColor([.25, .25, .25, 1])
					if "AlphaMap" in textureType:
						extraParam = "isALBA"
					if "Metal" in textureType:
						extraParam = "isALBM"
					if "Dielectric" in textureType:
						extraParam = "isALBD"
					self.uvBias[material.name] = [0.5, 0.5] if sGameName == "RE7RT" and "atlas" in texName.lower() else 1.0
				#elif (("Normal" in textureType or "NR" in textureType) or "_nr" in texName.lower()) and not bFoundNM:
				elif "_nr" in texName.lower() and not bFoundNM:
					bFoundNM = True
					material.setNormalTexture(texName)
					extraParam = "isNRM"
					if textureType == "NormalRoughnessMap":
						materialFlags |= noesis.NMATFLAG_PBR_ROUGHNESS_NRMALPHA
					if "NRR" in textureType or textureType == "NormalRoughnessTranslucentMap" or textureType == "NormalRoughnessCavityMap":
						extraParam = "isNRR"
				elif "AlphaTranslucent" in textureType and not bFoundSSSM:
					bFoundSSSM = True
					material.setOcclTexture(texName.replace(texOutputExt,  "_NoesisAO" + texOutputExt))
					extraParam = "isATOS_Alpha" if hasTransparency else "isATOS"
					material.setOcclTexture(texName.replace(texOutputExt,  "_NoesisAO" + texOutputExt))
				elif textureType == "AlphaMap":
					opacityName = texName
				#elif "_lymo" in texName.lower():
				#	extraParam = "isLYMO"
				elif re.search("^Base.*Map$", textureType) and not secondaryDiffuse:
				#elif ("_alb" in texName.lower()) and not secondaryDiffuse:
					secondaryDiffuse = texName
				elif not dialogOptions.loadAllTextures:
					isNotMainTexture = True
					
				if not bAlreadyLoadedTexture and not isNotMainTexture:
					if (textureName.endswith("rtex")):
						pass
					elif not (rapi.checkFileExists(textureFilePath)):
						if textureFilePath != "": 
							print("Error: Texture at path: " + str(textureFilePath) + " does not exist!")
					else:
						textureData = rapi.loadIntoByteArray(textureFilePath)
						numTex = len(self.texList)
						noetex = texLoadDDS(textureData, self.texList, texName)
						if noetex:
							if dialogOptions.doConvertTex:
								if "isALBM"  == extraParam or "isALBD" == extraParam:
									if "isALBD" == extraParam:
										noetex.pixelData = invertRawRGBAChannel(noetex.pixelData, 3)
									materialFlags |= noesis.NMATFLAG_PBR_METAL
									if dialogOptions.doConvertMatsForBlender:
										metalTexData = rapi.imageEncodeRaw(noetex.pixelData, noetex.width, noetex.height, "a8a8a8")
										metalTexData = rapi.imageDecodeRaw(metalTexData, noetex.width, noetex.height, "r8g8b8")
										noetex.pixelData = rapi.imageEncodeRaw(noetex.pixelData, noetex.width, noetex.height, "r8g8b8")
										noetex.pixelData = rapi.imageDecodeRaw(noetex.pixelData, noetex.width, noetex.height, "r8g8b8")
										if not isImageBlank(metalTexData, noetex.width, noetex.height, 4):
											metalTexName = texName.replace(texOutputExt,  "_NoesisMET" + texOutputExt)
											material.setSpecularTexture(metalTexName)
											self.texList.append(NoeTexture(metalTexName, noetex.width, noetex.height, metalTexData, noesis.NOESISTEX_RGBA32))
									else:
										material.setSpecularTexture(texName)
										material.setSpecularSwizzle( NoeMat44([[1, 0, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0]])) #move alpha channel to green channel
								if dialogOptions.doConvertMatsForBlender and ("isNRM" == extraParam or "isNRR" in extraParam):
									roughnessTexData = rapi.imageEncodeRaw(noetex.pixelData, noetex.width, noetex.height, "a8a8a8" if "isNRM" == extraParam else "r8r8r8")
									roughnessTexData = rapi.imageDecodeRaw(roughnessTexData, noetex.width, noetex.height, "r8g8b8")
									if not isImageBlank(roughnessTexData, noetex.width, noetex.height, 4):
										roughnessTexName = texName.replace(texOutputExt,  "_NoesisRGH" + texOutputExt)
										self.texList.append(NoeTexture(roughnessTexName, noetex.width, noetex.height, roughnessTexData, noesis.NOESISTEX_RGBA32))
										material.setBumpTexture(roughnessTexName)
								if "isNRR" in extraParam:
									noetex.pixelData = rapi.imageSwapChannelRGBA32(noetex.pixelData, 3, 0)
									#noetex.pixelData = rapi.imageNormalSwizzle(noetex.pixelData, noetex.width, noetex.height, 1, 0, 0)
									#noetex.pixelData = moveChannelsRGBA(noetex.pixelData, 3, noetex.width, noetex.height, noetex.pixelData, [0], noetex.width, noetex.height)
									noetex.pixelData = moveChannelsRGBA(noetex.pixelData, -2, noetex.width, noetex.height, noetex.pixelData, [2,3], noetex.width, noetex.height)
									#noetex.pixelData = invertRawRGBAChannel(noetex.pixelData, 1)
								if "isALBA" == extraParam:
									opacityTexData = rapi.imageEncodeRaw(noetex.pixelData, noetex.width, noetex.height, "a8a8a8")
									opacityTexData = rapi.imageDecodeRaw(opacityTexData, noetex.width, noetex.height, "r8g8b8")
									opacityName = texName.replace(texOutputExt,  "_NoesisAlpha" + texOutputExt)
									self.texList.append(NoeTexture(opacityName, noetex.width, noetex.height, opacityTexData, noesis.NOESISTEX_RGBA32))
								if "isLYMO" == extraParam:
									#r=metal? g= b=roughness? a=ao?
									materialFlags |= noesis.NMATFLAG_PBR_METAL
									metalTexName = texName.replace(texOutputExt,  "_NoesisMET" + texOutputExt)
									metalTexData = rapi.imageEncodeRaw(noetex.pixelData, noetex.width, noetex.height, "r8r8r8")
									metalTexData = rapi.imageDecodeRaw(metalTexData, noetex.width, noetex.height, "r8g8b8")
									material.setSpecularTexture(metalTexName)
									self.texList.append(NoeTexture(metalTexName, noetex.width, noetex.height, metalTexData, noesis.NOESISTEX_RGBA32))
									if dialogOptions.doConvertMatsForBlender:
										roughnessTexName = texName.replace(texOutputExt,  "_NoesisRGH" + texOutputExt)
										roughnessTexData = rapi.imageEncodeRaw(noetex.pixelData, noetex.width, noetex.height, "b8b8b8")
										roughnessTexData = rapi.imageDecodeRaw(roughnessTexData, noetex.width, noetex.height, "r8g8b8")
										self.texList.append(NoeTexture(roughnessTexName, noetex.width, noetex.height, roughnessTexData, noesis.NOESISTEX_RGBA32))
										material.setBumpTexture(roughnessTexName)
									noetex.pixelData = rapi.imageEncodeRaw(noetex.pixelData, noetex.width, noetex.height, "a8a8a8")
									noetex.pixelData = rapi.imageDecodeRaw(noetex.pixelData, noetex.width, noetex.height, "r8g8b8")
									material.setOcclTexture(noetex.name)
									
								if "isATOS" in extraParam:
									imgData = copy.copy(noetex.pixelData)
									aoTexData = rapi.imageEncodeRaw(noetex.pixelData, noetex.width, noetex.height, "b8b8b8")
									aoTexData = rapi.imageDecodeRaw(aoTexData, noetex.width, noetex.height, "r8g8b8")
									if not isImageBlank(aoTexData, noetex.width, noetex.height):
										noetex.name = texName.replace(texOutputExt,  "_NoesisAO" + texOutputExt)
										self.texList[len(self.texList)-1].pixelData = aoTexData
									else:           
										self.texList.remove(noetex)
										material.setOcclTexture("")
									if extraParam == "isATOS_Alpha" and not opacityName:
										opacityTexData = rapi.imageEncodeRaw(imgData, noetex.width, noetex.height, "r8r8r8")
										opacityTexData = rapi.imageDecodeRaw(opacityTexData, noetex.width, noetex.height, "r8g8b8")
										if not isImageBlank(opacityTexData, noetex.width, noetex.height):
											opacityName = texName.replace(texOutputExt,  "_NoesisAlpha" + texOutputExt)
											materialFlags |= noesis.NMATFLAG_TWOSIDED
											self.texList.append(NoeTexture(opacityName, noetex.width, noetex.height, opacityTexData, noesis.NOESISTEX_RGBA32))
							alreadyLoadedTexs.append(texName)
						else:
							print ("Failed to load", texName)
				
				if opacityName and hasTransparency:
					material.setAlphaTest(0.05)
					material.setOpacityTexture(opacityName)
					if dialogOptions.doConvertMatsForBlender:
						material.setEnvTexture(opacityName)
						
				
				if doPrintMDF:
					print(textureType + ":\n    " + textureName)
			
			if secondaryDiffuse and not bFoundBM:
				material.setTexture(secondaryDiffuse)
				material.setSpecularColor([.25, .25, .25, 1])
			
			if texCount:
				if not bFoundBM:
					dummyTexName = textureName.replace(texOutputExt, "_NoesisColor" + texOutputExt)
					material.setTexture(dummyTexName)
					if dummyTexName not in alreadyLoadedTexs:
						try:
							byteColor = [int((1 if color > 1.0 else 0 if color < 0.0 else color) * 255) for color in texBaseColour[i]]
						except:
							byteColor = [127, 127, 127, 255]
						self.texList.append(generateDummyTexture4px(byteColor, dummyTexName))
						alreadyLoadedTexs.append(dummyTexName)
				if not bFoundNM:
					material.setNormalTexture("NoesisNRM" + texOutputExt)
					if "NoesisNRM" + texOutputExt not in alreadyLoadedTexs:
						self.texList.append(generateDummyTexture4px((127, 127, 255, 255), "NoesisNRM" + texOutputExt))
						alreadyLoadedTexs.append("NoesisNRM" + texOutputExt)
					
			material.setFlags(materialFlags)
			material.setFlags2(materialFlags2)
			self.matList.append(material)
			
			lowername = material.name.lower()
			if ("eye" in lowername and not material.texName) or "tearline" in lowername or "lens" in lowername or "destroy" in lowername: #"ao" in lowername or "out" in lowername or 
				material.setSkipRender(True)
			
			if doPrintMDF:
				print("--------------------------------------------------------------------------------------------\n")
					
		if bPrintFileList:
			if len(self.texNames) > 0:
				print ("\nReferenced Files:")
				textureList = sorted(list(set(self.texNames)))
				for x in range (len(textureList)):
					print (textureList[x])
				print ("")
			
			if len(self.missingTexNames) > 0:
				print ("Missing Files:")
				missingTextureList = sorted(list(set(self.missingTexNames)))
				for x in range (len(missingTextureList)):
					print (missingTextureList[x])
				print ("")

		if doColorize:
			colorList = sorted(list(set(self.texColors)))
			print ("Color-coded Materials:")
			for g in range (len(colorList)):
				print (colorList[g])
			print ("")
		
		for mat in self.matList:
			if mat.name not in usedMats:
				usedMats.append(mat.name)
				self.fullMatList.append(mat)
		for tex in self.texList:
			if tex.name not in usedTexs:
				usedTexs.append(tex.name)
				self.fullTexList.append(tex)
		
		return True
		
	'''MESH IMPORT ========================================================================================================================================================================'''
	def loadMeshFile(self): #, mdlList):
		
		global sGameName, bSkinningEnabled, isSF6, isExoPrimal
		bs = self.inFile
		magic = bs.readUInt()
		meshVersion = bs.readUInt()
		fileSize = bs.readUInt()
		deferredWarning = ""
		bDoSkin = True
		
		bs.seek(numNodesLocation)
		numNodes = bs.readUInt()
		bs.seek(LOD1OffsetLocation)
		LOD1Offs = bs.readUInt64()
		LOD2Offs = bs.readUInt64()
		occluderMeshOffs = bs.readUInt64()
		bs.seek(vBuffHdrOffsLocation)  
		vBuffHdrOffs = bs.readUInt64() 
		bs.seek(bonesOffsLocation)   
		bonesOffs = bs.readUInt64()  
		bs.seek(nodesIndicesOffsLocation)  
		nodesIndicesOffs = bs.readUInt64()  
		boneIndicesOffs = bs.readUInt64()  
		bs.seek(namesOffsLocation)
		namesOffs = bs.readUInt64()
		
		if LOD1Offs:
			bs.seek(LOD1Offs)
			countArray = bs.read("16B") #[0] = LODGroupCount, [1] = MaterialCount, [2] = UVChannelCount
			matCount = countArray[1]
			self.rootDir = GetRootGameDir(self.path)
			bLoadedMats = False
			if not (noesis.optWasInvoked("-noprompt")) and not bRenameMeshesToFilenames and not rapi.noesisIsExporting() and not (dialogOptions.dialog != None and dialogOptions.doLoadTex == False):
				bLoadedMats = self.createMaterials(matCount)
			if bDebugMESH:
				print("Count Array")
				print(countArray)
		
		bs.seek(vBuffHdrOffs)
		vertElemHdrOffs = bs.readUInt64()
		vertBuffOffs = bs.readUInt64()
		
		if self.ver >= 3: #isSF6 or isExoPrimal:
			uknVB = bs.readUInt64()
			vertBuffSize = bs.readUInt()
			face_buffOffsSF6 = bs.readUInt()
			faceBuffOffs = face_buffOffsSF6 + vertBuffOffs;
		else:
			faceBuffOffs = bs.readUInt64()
			if sGameName == "RERT" or sGameName == "RE7RT" or sGameName == "MHRSunbreak":
				uknInt64 = bs.readUInt64()
			vertBuffSize = bs.readUInt()
			faceBuffSize = bs.readUInt()
		
		vertElemCountA = bs.readUShort()
		vertElemCountB = bs.readUShort()
		faceBufferSize2nd = bs.readUInt64()
		blendshapesOffset = bs.readUInt()
		
		bs.seek(vertElemHdrOffs)
		vertElemHeaders = []
		positionIndex = -1
		normalIndex = -1
		colorIndex = -1
		uvIndex = -1
		uv2Index = -1
		weightIndex = -1
		
		for i in range (vertElemCountB):
			vertElemHeaders.append([bs.readUShort(), bs.readUShort(), bs.readUInt()])
			if vertElemHeaders[i][0] == 0 and positionIndex == -1:
				positionIndex = i
			elif vertElemHeaders[i][0] == 1 and normalIndex == -1:
				normalIndex = i
			elif vertElemHeaders[i][0] == 2 and uvIndex == -1:
				uvIndex = i
			elif vertElemHeaders[i][0] == 3 and uv2Index == -1:
				uv2Index = i
			elif vertElemHeaders[i][0] == 4 and weightIndex == -1:
				weightIndex = i
			elif vertElemHeaders[i][0] == 5 and colorIndex == -1:
				colorIndex = i
		bs.seek(vertBuffOffs)
		
		vertexStartIndex = bs.tell()
		#print (vertElemHdrOffs, vertBuffOffs, uknVB, vertBuffSize, faceBuffOffs, vertElemCountA, vertElemCountB)
		vertexBuffer = bs.readBytes(vertBuffSize)
		submeshDataArr = []
		
		if LOD1Offs:	
			
			bs.seek(LOD1Offs + 48 + 16) #unknown floats and bounding box
			
			if self.ver <= 1:  #sGameName != "RERT" and sGameName != "ReVerse" and sGameName != "RE8" and sGameName != "MHRise": 
				bs.seek(bs.readUInt64())
			
			offsetInfo = []
			for i in range(countArray[0]):
				offsetInfo.append(bs.readUInt64())
				
			if bDebugMESH:
				print("Vertex Info Offsets")
				print(offsetInfo)
			
			nameOffsets = []
			names = []
			nameRemapTable = []
			
			bs.seek(nodesIndicesOffs)
			for i in range(numNodes):
				nameRemapTable.append(bs.readUShort())
				
			bs.seek(namesOffs)
			for i in range(numNodes):
				nameOffsets.append(bs.readUInt64())
				
			for i in range(numNodes):
				bs.seek(nameOffsets[i])
				names.append(bs.readString())
				
			if bDebugMESH:
				print("Names:")
				print(names)
				
			bs.seek(nodesIndicesOffs) #material indices
			matIndices =[]
			for i in range(matCount):
				matIndices.append(bs.readUShort())
			
			isSCN = (rapi.getInputName().lower().find(".scn") != -1)
			fullBonesOffs = len(self.fullBoneList)
			fullRemapOffs = len(self.fullRemapTable)
			fullBoneNames = [cleanBoneName(bone.name).lower() for bone in self.fullBoneList]
			boneRemapTable = []
			
			#Skeleton
			if bonesOffs:
				bs.seek(bonesOffs)
				boneCount = bs.readUInt()
				boneMapCount = bs.readUInt()	
				bAddNumbers = False
				if rapi.getInputName().find(".noesis") == -1 and (not dialogOptions.dialog or len(dialogOptions.dialog.loadItems) == 1) and (not dialogOptions.motDialog or not dialogOptions.motDialog.loadItems) :
					maxBones = 1024 if isSF6 == True else 256
					if bAddBoneNumbers == 1 or noesis.optWasInvoked("-bonenumbers"):
						bAddNumbers = True
					elif bAddBoneNumbers == 2 and boneCount > maxBones and rapi.getInputName().lower().find(".scn") == -1:
						bAddNumbers = True
						print ("Model has more than", maxBones, "bones, auto-enabling bone numbers...")
				
				bs.seek(bonesOffs + 16)
				
				if boneCount:
					hierarchyOffs = bs.readUInt64()
					localOffs = bs.readUInt64()
					globalOffs = bs.readUInt64()
					inverseGlobalOffs = bs.readUInt64()
					
					if boneMapCount:
						for i in range(boneMapCount):
							boneRemapTable.append(bs.readShort() + fullBonesOffs)
					else:
						deferredWarning = "WARNING: Mesh has weights but no bone map"
						print(deferredWarning)
						boneRemapTable.append(0)
						
					if bDebugMESH:
						print("boneRemapTable:", boneRemapTable)

					boneParentInfo = []
					bs.seek(hierarchyOffs)
					for i in range(boneCount):
						boneParentInfo.append([bs.readShort(), bs.readShort(), bs.readShort(), bs.readShort(), bs.readShort(), bs.readShort(), bs.readShort(), bs.readShort()])
					
					bs.seek(localOffs)
					for i in range(boneCount):
						mat = NoeMat44.fromBytes(bs.readBytes(0x40)).toMat43()
						mat[3] *= fDefaultMeshScale
						boneName = names[countArray[1] + i]
						lowerBoneName = boneName.lower()
						#if i==0 and "root" in boneName.lower():
						#	mat[3][1] = 0 #neutralize Y offset for root bone
						
						if bAddNumbers: 
							for j in range(len(boneRemapTable)):
								if boneParentInfo[i][0] == boneRemapTable[j]:
									boneName = "b" + "{:03d}".format(j+1) + ":" + boneName
									break
						parentIdx = boneParentInfo[i][1]
						if not isSCN and lowerBoneName in fullBoneNames:
							if i == 0: #relocate this mesh's root bone onto base skeleton version
							#if lowerBoneName == "cog" or lowerBoneName == "hip" or lowerBoneName == "c_hip":
								print("Relocating bone", boneName)
								newMat = self.fullBoneList[fullBoneNames.index(lowerBoneName)].getMatrix()
								self.pos =  (newMat[3] - mat[3]) / fDefaultMeshScale
								mat = newMat
							ctr = 1
							newBoneName = boneName + "." + rapi.getLocalFileName(self.path).split(".")[0]
							while newBoneName.lower() in fullBoneNames:
								newBoneName = boneName + "." + rapi.getLocalFileName(self.path).split(".")[0] + "-" + str(ctr)
								ctr += 1
							boneName = newBoneName
							
						#if (parentIdx == -1 or parentIdx == i) and (i > 0 or self.fullBoneList):
						#	print("changed parent", boneName)
						#	parentIndex = 0
						
						self.boneList.append(NoeBone(boneParentInfo[i][0], boneName, mat, None, parentIdx))
						
					self.boneList = rapi.multiplyBones(self.boneList)
					
					if bRotateBonesUpright:
						rot_mat = NoeMat43(((1, 0, 0), (0, 0, 1), (0, -1, 0), (0, 0, 0)))
						for bone in self.boneList: 
							bone.setMatrix( (bone.getMatrix().inverse() * rot_mat).inverse()) 	#rotate upright in-place
					for bone in self.boneList: 
						bone.index += fullBonesOffs
						if bone.parentIndex != -1:
							bone.parentIndex += fullBonesOffs
						if bone.parentIndex == -1 and fullBonesOffs > 0:
							bone.parentIndex = 0
				else:
					bDoSkin = False
					
			
			self.fullBoneList.extend(self.boneList)
			self.fullRemapTable.extend(boneRemapTable)
			
			#print(offsetInfo)
			for i in range(countArray[0]): # LODGroups
				
				meshVertexInfo = []
				#ctx = rapi.rpgCreateContext()
				bs.seek(offsetInfo[i])
				numOffsets = bs.readUByte()
				bs.seek(3,1)
				uknFloat = bs.readUInt()
				offsetSubOffsets = bs.readUInt64()
				bs.seek(offsetSubOffsets)
				
				meshOffsetInfo = []
				
				for j in range(numOffsets):
					meshOffsetInfo.append(bs.readUInt64())
				
				numVertsLOD = 0
				
				for j in range(numOffsets): # MainMeshes
					bs.seek(meshOffsetInfo[j])
					meshVertexInfo.append([bs.readUByte(), bs.readUByte(), bs.readUShort(), bs.readUInt(), bs.readUInt(), bs.readUInt()]) #GroupID, NumMesh, unused, unused, numVerts, numFaces
					self.groupIDs.append(meshVertexInfo[len(meshVertexInfo)-1][0])
					submeshData = []
					for k in range(meshVertexInfo[j][1]):
						if self.ver >= 2: #sGameName == "RERT" or sGameName == "ReVerse" or sGameName == "MHRise" or sGameName == "RE8" or sGameName == "SF6":
							submeshData.append([bs.readUShort(), bs.readUShort(), bs.readUInt(), bs.readUInt(), bs.readUInt(), bs.readUInt64(), self.groupIDs[len(self.groupIDs)-1]]) 
						else:
							submeshData.append([bs.readUShort(), bs.readUShort(), bs.readUInt(), bs.readUInt(), bs.readUInt(), self.groupIDs[len(self.groupIDs)-1]]) #0 MaterialID, 1 faceCount, 2 indexBufferStartIndex, 3 vertexStartIndex
					
					submeshDataArr.append(submeshData)
					
					for k in range(meshVertexInfo[j][1]): # Submeshes
						
						mainMeshNo = self.groupIDs[len(self.groupIDs)-1] if bReadGroupIds else j+1
						mainMeshStr = "_Group_" if bReadGroupIds else "_MainMesh_" if not bShorterNames else "_Main_"
						
						materialID = submeshData[k][0]
						uknSubmeshID = submeshData[k][1]
						numFaces	 = submeshData[k][2]
						facesBefore  = submeshData[k][3]
						vertsBefore  = submeshData[k][4]
						uknSubmeshInt1 = submeshData[k][5]
						
						numVerts = submeshData[k+1][4] - vertsBefore if k+1 < len(submeshData) else meshVertexInfo[j][4] - (submeshData[k][4] - numVertsLOD)
						
						mainMeshNo = self.groupIDs[len(self.groupIDs)-1] if bReadGroupIds else j+1
						mainMeshStr = "_Group_" if bReadGroupIds else "_MainMesh_" if not bShorterNames else "_Main_"
						
						if bUseOldNamingScheme:
							meshName = "LODGroup_" + str(i+1) + mainMeshStr + str(mainMeshNo) + "_SubMesh_" + str(materialID+1)
						else:
							if bRenameMeshesToFilenames:
								meshName = os.path.splitext(rapi.getLocalFileName(sInputName))[0].replace(".mesh", "") + "_" + str(mainMeshNo) + "_" + str(k+1)
							elif bShorterNames:
								meshName = "LOD_" + str(i+1) + mainMeshStr + str(mainMeshNo) + "_Sub_" + str(k+1)
							else:
								meshName = "LODGroup_" + str(i+1) + mainMeshStr + str(mainMeshNo) + "_SubMesh_" + str(k+1)
						
						if (dialogOptions.dialog and len(dialogOptions.dialog.loadItems) > 1) or isSCN:
							meshName = rapi.getLocalFileName(self.path).split(".")[0].replace("_", "") + "_" + meshName.split("_", 1)[1]
							
						rapi.rpgSetName(meshName)
						if bRenameMeshesToFilenames: 
							rapi.rpgSetMaterial(meshName)
						matName = ""; matHash = 0
						
						#Search for material
						if bLoadedMats:
							matHash = hash_wide(names[matIndices[materialID]])
							if i == 0:
								for m in range(len(self.matHashes)):
									if self.matHashes[m] == matHash:
										if self.matNames[m] != names[nameRemapTable[materialID]]:
											print ("WARNING: " + meshName + "\'s material name \"" + self.matNames[m] + "\" in MDF does not match its material hash! \n	True material name: \"" + names[nameRemapTable[materialID]] + "\"")
										matName = self.matNames[m]
										#rapi.rpgSetLightmap(matArray[k].replace(".dds".lower(), ""))
										break
						if matName == "":
							if matHash == 0: 
								matHash = hash_wide(names[matIndices[materialID]])
							if bLoadedMats:
								print ("WARNING: " + meshName + "\'s material \"" + names[nameRemapTable[materialID]] + "\" hash " + str(matHash) + " not found in MDF!")
							self.matNames.append(names[nameRemapTable[materialID]])
							
							matName = self.matNames[len(self.matNames)-1]
						
						rapi.rpgSetMaterial(matName)
						rapi.rpgSetPosScaleBias((fDefaultMeshScale, fDefaultMeshScale, fDefaultMeshScale), (0, 0, 0))
						if bImportMaterialNames:
							#rapi.rpgSetName(meshName + "__" + matName + "__" + str(submeshData[k][len(submeshData[k])-1]))
							rapi.rpgSetName(meshName + '__' + matName)
						
						if positionIndex != -1:
							if self.pos: #position offset
								posList = []
								for v in range(vertsBefore, vertsBefore+numVerts):
									idx = 12 * v
									transVec = NoeVec3(((struct.unpack_from('f', vertexBuffer, idx))[0], (struct.unpack_from('f', vertexBuffer, idx + 4))[0], (struct.unpack_from('f', vertexBuffer, idx + 8))[0])) * self.rot.transpose()
									posList.append(transVec[0] + self.pos[0]) 
									posList.append(transVec[1] + self.pos[1])
									posList.append(transVec[2] + self.pos[2])
								posBuff = struct.pack("<" + 'f'*len(posList), *posList)
								rapi.rpgBindPositionBufferOfs(posBuff, noesis.RPGEODATA_FLOAT, 12, 0)
							else:
								rapi.rpgBindPositionBufferOfs(vertexBuffer, noesis.RPGEODATA_FLOAT, vertElemHeaders[positionIndex][1], (vertElemHeaders[positionIndex][1] * vertsBefore))
						
						if normalIndex != -1 and bNORMsEnabled:
							if bDebugNormals and not bColorsEnabled:
								rapi.rpgBindColorBufferOfs(vertexBuffer, noesis.RPGEODATA_BYTE, vertElemHeaders[normalIndex][1], vertElemHeaders[normalIndex][2] + (vertElemHeaders[normalIndex][1] * vertsBefore), 4)
							else:
								rapi.rpgBindNormalBufferOfs(vertexBuffer, noesis.RPGEODATA_BYTE, vertElemHeaders[normalIndex][1], vertElemHeaders[normalIndex][2] + (vertElemHeaders[normalIndex][1] * vertsBefore))
								if bTANGsEnabled:
									rapi.rpgBindTangentBufferOfs(vertexBuffer, noesis.RPGEODATA_BYTE, vertElemHeaders[normalIndex][1], 4 + vertElemHeaders[normalIndex][2] + (vertElemHeaders[normalIndex][1] * vertsBefore))
						try:
							rapi.rpgSetUVScaleBias(NoeVec3((self.uvBias[names[nameRemapTable[materialID]]][0], 1, 1)), NoeVec3((self.uvBias[names[nameRemapTable[materialID]]][1], 0, 0)))
						except:
							rapi.rpgSetUVScaleBias(NoeVec3((1,1,1)), NoeVec3((0,0,0)))
						if uvIndex != -1 and bUVsEnabled:
							rapi.rpgBindUV1BufferOfs(vertexBuffer, noesis.RPGEODATA_HALFFLOAT, vertElemHeaders[uvIndex][1], vertElemHeaders[uvIndex][2] + (vertElemHeaders[uvIndex][1] * vertsBefore))
						if uv2Index != -1 and bUVsEnabled:
							rapi.rpgBindUV2BufferOfs(vertexBuffer, noesis.RPGEODATA_HALFFLOAT, vertElemHeaders[uv2Index][1], vertElemHeaders[uv2Index][2] + (vertElemHeaders[uv2Index][1] * vertsBefore))
						
						if weightIndex != -1 and bSkinningEnabled and bDoSkin:
							#rapi.rpgSetBoneMap(boneRemapTable)
							rapi.rpgSetBoneMap(self.fullRemapTable)
							idxList = []
							start = vertexStartIndex + vertElemHeaders[weightIndex][2] + (vertElemHeaders[weightIndex][1] * vertsBefore)
							if isSF6 == True:
								for v in range(numVerts):
									bs.seek(start + vertElemHeaders[weightIndex][1] * v)
									for bID in range(3):
										idxList.append(bs.readBits(10)+fullRemapOffs)
									bs.readBits(2)
									for bID in range(3):
										idxList.append(bs.readBits(10)+fullRemapOffs)
									idxList.extend([0,0])
								idxBuff = struct.pack("<" + 'H'*len(idxList), *idxList)
								rapi.rpgBindBoneIndexBufferOfs(idxBuff, noesis.RPGEODATA_USHORT, 16, 0, 8)
							elif fullBonesOffs:
								for v in range(numVerts):
									bs.seek(start + vertElemHeaders[weightIndex][1] * v)
									for w in range(8):
										idxList.append(bs.readUByte()+fullRemapOffs)
								idxBuff = struct.pack("<" + 'H'*len(idxList), *idxList)
								rapi.rpgBindBoneIndexBufferOfs(idxBuff, noesis.RPGEODATA_USHORT, 16, 0, 8)
							else:
								rapi.rpgBindBoneIndexBufferOfs(vertexBuffer, noesis.RPGEODATA_UBYTE, vertElemHeaders[weightIndex][1], vertElemHeaders[weightIndex][2] + (vertElemHeaders[weightIndex][1] * vertsBefore), 8)
							rapi.rpgBindBoneWeightBufferOfs(vertexBuffer, noesis.RPGEODATA_UBYTE, vertElemHeaders[weightIndex][1], vertElemHeaders[weightIndex][2] + (vertElemHeaders[weightIndex][1] * vertsBefore) + 8, 8)
							
						if colorIndex != -1 and bColorsEnabled:
							offs = vertElemHeaders[colorIndex][2] + (vertElemHeaders[colorIndex][1] * vertsBefore)
							if offs + numVerts*4 < len(vertexBuffer):
								rapi.rpgBindColorBufferOfs(vertexBuffer, noesis.RPGEODATA_UBYTE, vertElemHeaders[colorIndex][1], offs, 4)
							else:
								print("WARNING:", meshName, "Color buffer would have been read out of bounds by provided indices", "\n	Buffer Size:", len(vertexBuffer), "\n	Required Size:", offs + numVerts*4)
							
						if numFaces > 0:
							bs.seek(faceBuffOffs + (facesBefore * 2))
							indexBuffer = bs.readBytes(numFaces * 2)
							if bRenderAsPoints:
								rapi.rpgCommitTriangles(None, noesis.RPGEODATA_USHORT, (meshVertexInfo[j][4] - (vertsBefore)), noesis.RPGEO_POINTS, 0x1)
							else:
								rapi.rpgSetStripEnder(0x10000)
								rapi.rpgCommitTriangles(indexBuffer, noesis.RPGEODATA_USHORT, numFaces, noesis.RPGEO_TRIANGLE, 0x1)
								rapi.rpgClearBufferBinds()
					
					numVertsLOD += meshVertexInfo[j][4]
					
				'''try:
					mdl = rapi.rpgConstructModelAndSort()
					if mdl.meshes[0].name.find("_") == 4:
						print ("\nWARNING: Noesis split detected!\n   Export this mesh to FBX with the advanced option '-fbxmeshmerge'\n")
						rapi.rpgOptimize()
				except:
					mdl = NoeModel()
				mdl.setBones(self.boneList)
				mdl.setModelMaterials(NoeModelMaterials(self.texList, self.matList))
				mdlList.append(mdl)'''
				
				if not bImportAllLODs:
					break
				
			print ("\nMESH Material Count:", matCount)
			if bLoadedMats:
				print ("MDF Material Count:", len(self.matList))
			
		if occluderMeshOffs:
			#ctx = rapi.rpgCreateContext()
			#rapi.rpgSetOption(noesis.RPGOPT_TRIWINDBACKWARD, 1)
			bs.seek(occluderMeshOffs)
			occluderMeshCount = bs.readUInt()
			uknFloat = bs.readFloat()
			occluderMeshesOffset = bs.readUInt64()
			bs.seek(occluderMeshesOffset)
			occluderMeshes = []
			lastVertPos = vertBuffOffs
			lastFacesPos = faceBuffOffs
			for i in range(occluderMeshCount):
				dataOffset = bs.readUInt64()
				bs.seek(dataOffset)
				uknBytes = [bs.readByte(), bs.readByte(), bs.readByte(), bs.readByte(), bs.readByte(), bs.readByte(), bs.readByte(), bs.readByte()]
				vertexCount = bs.readUInt()
				indexCount = bs.readUInt()
				ukn = bs.readUInt()
				indexCount2 = bs.readUInt()
				occluderMeshes.append([uknBytes, vertexCount, indexCount])
				bs.seek(lastVertPos)
				vertexBuffer = bs.readBytes(12 * vertexCount)
				lastVertPos = bs.tell()
				bs.seek(lastFacesPos)
				indexBuffer = bs.readBytes(indexCount * 2)
				lastFacesPos = bs.tell()
				rapi.rpgSetName("OccluderMesh_" + str(i))
				rapi.rpgBindPositionBuffer(vertexBuffer, noesis.RPGEODATA_FLOAT, 12)
				rapi.rpgSetStripEnder(0x10000)
				try:
					rapi.rpgCommitTriangles(indexBuffer, noesis.RPGEODATA_USHORT, indexCount, noesis.RPGEO_TRIANGLE, 0x1)
					rapi.rpgClearBufferBinds()
					'''try:
						mdl = rapi.rpgConstructModelAndSort()
						if mdl.meshes[0].name.find("_") == 4:
							print ("\nWARNING: Noesis split detected!\n   Export this mesh to FBX with the advanced option '-fbxmeshmerge'\n")
							rapi.rpgOptimize()
					except:
						mdl = NoeModel()
					mdlList.append(mdl)'''
				except:
					print("Failed to read Occluder Mesh")
					
		print (deferredWarning)
		
		return 1 #mdlList


def meshLoadModel(data, mdlList):
	
	noesis.logPopup()
	print("\n\n	RE Engine MESH model import", Version, "by alphaZomega\n")
	
	ctx = rapi.rpgCreateContext()
	mesh = meshFile(data)
	mesh.setGameName()
	dialogOptions.motDialog = None
	dialogOptions.dialog = None
	dialogOptions.currentDir = ""
	dialog = openOptionsDialogImportWindow(None, None, {"mesh":mesh})
	dialog.path = rapi.getInputName()
	dialog.createPakWindow()
	
	while dialogOptions.motDialog and dialogOptions.motDialog.isOpen:
		dialogOptions.motDialog.createMotlistWindow()
		dialogOptions.motDialog.isOpen = False
		if dialog.isOpen:
			dialogOptions.currentDir = dialog.currentDir
			dialog.createPakWindow()
	
	if not dialog.isCancelled:
		for fullMeshPath in dialog.fullLoadItems:
			meshToLoad = meshFile(rapi.loadIntoByteArray(fullMeshPath), fullMeshPath)
			meshToLoad.fullBoneList = dialog.pak.fullBoneList
			meshToLoad.fullRemapTable = dialog.pak.fullRemapTable
			meshToLoad.fullTexList = dialog.pak.fullTexList
			meshToLoad.fullMatList = dialog.pak.fullMatList
			meshToLoad.loadMeshFile()
		try:
			mdl = rapi.rpgConstructModelAndSort()
			if mdl.meshes[0].name.find("_") == 4:
				print ("\nWARNING: Noesis split detected!\n   Export this mesh to FBX with the advanced option '-fbxmeshmerge'\n")
		except:
			print("Failed to construct model from rpgeo context")
			mdl = NoeModel()
	else:
		mdl = NoeModel()
	
	doLoadAnims = (dialogOptions.motDialog and dialogOptions.motDialog.loadItems and not dialogOptions.motDialog.isCancelled)
	if doLoadAnims:
		mlDialog = dialogOptions.motDialog
		sortedMlists = []
		for mlist in [mlDialog.loadedMlists[path] for path in mlDialog.fullLoadItems]:
			if mlist not in sortedMlists:
				sortedMlists.append(mlist)
		motlist = mlDialog.pak
		mdl.setBones(dialog.pak.fullBoneList)
		collapseBones(mdl, 100)
		bones = list(mdl.bones)
		mdlBoneNames = [bone.name.lower() for bone in bones]
		for mlist in sortedMlists:
			mlist.meshBones = bones
			mlist.readBoneHeaders(mlDialog.loadItems)
			for bone in mlist.bones:
				if bone.name.lower() not in mdlBoneNames:
					bone.index = len(bones)
					bones.append(bone)
		anims = []
		startFrame = 0
		for mlist in sortedMlists:
			mlist.bones = bones
			mlist.readBoneHeaders(mlDialog.loadItems)
			mlist.totalFrames = startFrame
			mlist.read(mlDialog.loadItems)
			startFrame = mlist.totalFrames
		for mlist in sortedMlists:
			mlist.makeAnims(mlDialog.loadItems)
			anims.extend(mlist.anims)
		mdl.setBones(bones)
		mdl.setAnims(anims)
		rapi.setPreviewOption("setAnimSpeed", "60.0")
	else:
		mdl.setBones(dialog.pak.fullBoneList)
		
	mdl.setModelMaterials(NoeModelMaterials(dialog.pak.fullTexList, dialog.pak.fullMatList))
	
	if len(dialog.loadItems) > 1:
		if dialogOptions.reparentHelpers and not doLoadAnims:
			collapseBones(mdl, 1)
		if noesis.optWasInvoked("-bonenumbers"):
			generateBoneMap(mdl)
	mdlList.append(mdl)
	
	'''boneNames = {}
	for i, bone in enumerate(mdl.bones):
		if bone.name.lower() in boneNames:
			print("Duplicate Bone Name:", bone.name)
			collapseBones(mdl, 1)
			break
		boneNames[bone.name.lower()] = True'''
	
	return 1


def getSameExtFilesInDir(filename=None, ext=None):
	ext = ext or os.path.splitext(rapi.getOutputName())[-1]
	filename = filename or rapi.getOutputName()
	sourceList = []
	for item in os.listdir(os.path.dirname(rapi.getOutputName())):
		if os.path.splitext(item)[1] == ext:
			sourceList.append(os.path.join(os.path.dirname(filename), item))
	return sourceList

def getExportName(fileName, exportType=".mesh"):
	global w1, w2, bWriteBones, bReWrite, bRigToCoreBones, bDoVFX, openOptionsDialog #, doLOD
	bReWrite = False; bWriteBones = False; w1 = 127; w2 = -128
	sourceList = []
	if fileName == None:
		meshExt = os.path.splitext(rapi.getOutputName())[-1]
		newMeshName = rapi.getExtensionlessName(rapi.getOutputName().replace("out.", ".")).replace(".mesh", "").replace(meshExt, "") + ".mesh" + meshExt
		ogFileName = rapi.getLocalFileName(newMeshName)
		similarityCounter = 0
		for item in os.listdir(os.path.dirname(rapi.getOutputName())):
			if os.path.splitext(item)[1] == meshExt:
				sourceList.append(os.path.join(os.path.dirname(newMeshName), item))
				sameCharCntr = 0
				for c, char in enumerate(rapi.getExtensionlessName(item)): 
					if c < len(ogFileName) and char == ogFileName[c]:
						sameCharCntr += 1
				if sameCharCntr > similarityCounter:
					similarityCounter = sameCharCntr
					newMeshName = os.path.join(os.path.dirname(newMeshName), item)
	else:
		newMeshName = fileName
	
	if bNewExportMenu:
		openOptionsDialog = openOptionsDialogExportWindow(1000, 195, {"filepath":newMeshName, "exportType":exportType}) #int(len(newMeshName)*7.5)
		openOptionsDialog.createMeshWindow()
		newMeshName = openOptionsDialog.filepath or newMeshName
		if openOptionsDialog.doCancel:
			newMeshName = None
		else: 
			if openOptionsDialog.doRewrite:
				newMeshName = newMeshName + " -rewrite"
			if openOptionsDialog.doWriteBones:
				newMeshName = newMeshName + " -bones"
			if openOptionsDialog.doVFX:
				newMeshName = newMeshName + " -vfx"
	else:
		newMeshName = noesis.userPrompt(noesis.NOEUSERVAL_FILEPATH, "Export over " + exportType.upper(), "Choose a " + exportType.upper() + " file to export over", newMeshName, None)

	if newMeshName == None:
		print("Aborting...")
		return
		
	if noesis.optWasInvoked("-flip") or newMeshName.find(" -flip") != -1:
		newMeshName = newMeshName.replace(" -flip", "")
		print ("Exporting with OpenGL handedness")
		w1 = -128; w2 = 127
		
	if noesis.optWasInvoked("-vfx") or newMeshName.find(" -vfx") != -1:
		newMeshName = newMeshName.replace(" -vfx", "")
		bDoVFX = True
		print ("Exporting VFX mesh")
	
	if noesis.optWasInvoked("-bones") or newMeshName.find(" -bones") != -1:
		newMeshName = newMeshName.replace(" -bones", "")
		print ("Exporting with new skeleton...")
		bWriteBones = True
		
	if newMeshName.find(" -rewrite") != -1:
		newMeshName = newMeshName.replace(" -rewrite", "")
		print ("Exporting with new skeleton, Group and Submesh order...")
		bReWrite = True
		bWriteBones = True
		
	if newMeshName.find(" -match") != -1:
		newMeshName = newMeshName.replace(" -match", "")
		print ("Unmatched bones will be rigged to the hips and spine")
		bRigToCoreBones = True
		
	return newMeshName
	
#===========================================================================================================================================
#MESH EXPORT
	
def meshWriteModel(mdl, bs):

	global sExportExtension, w1, w2, bWriteBones, bReWrite, bRigToCoreBones, bAddBoneNumbers, sGameName, bNewExportMenu, bDoVFX, isSF6 #doLOD
	
	bWriteBones = noesis.optWasInvoked("-bones")
	bReWrite = noesis.optWasInvoked("-rewrite")
	bNewExportMenu = noesis.optWasInvoked("-adv") or bNewExportMenu
	
	w1 = 127; w2 = -128
	if noesis.optWasInvoked("-flip"): 
		w1 = -128; w2 = 127
		
	if bAlwaysRewrite or noesis.optWasInvoked("-b"):
		bReWrite = True
	if bAlwaysWriteBones:
		bWriteBones = True
	
	meshesToExport = mdl.meshes
	bDoUV2 = False
	bDoSkin = False
	bDoColors = False
	bAddNumbers = False
	f = None
	newMeshName = ""
	bDoVFX = noesis.optWasInvoked("-vfx") or (openOptionsDialog and openOptionsDialog.doVFX)
	numLODs = 1
	diff = 0	
	meshVertexInfo = []
	vertElemCountB = 5	
	newScale = (1 / fDefaultMeshScale)
	submeshes = []
	
	
	def padToNextLine(bitstream):
		while bitstream.tell() % 16 != 0:
			bitstream.writeByte(0)
			
	def dot(v1, v2):
		return sum(x*y for x,y in zip(v1,v2))	
			
	def cross(a, b):
		c = [a[1]*b[2] - a[2]*b[1],
			 a[2]*b[0] - a[0]*b[2],
			 a[0]*b[1] - a[1]*b[0]]
		return c
		
	def checkReWriteMeshes():
		global bReWrite
		nonlocal submeshes, meshesToExport, bDoSkin
		for i in objToExport:
			obj = meshesToExport[i]
			sName = obj.name.lower().split('_')
			if len(sName) < 8:
				print("WARNING! Cannot rewrite mesh, an object is missing its material name\nObject Name:", obj.name, "\nMeshes for ReWrite should have 7 underscores in their names.\nExporting with new skeleton...")
				bReWrite = False
				submeshes = []
				break
			else:
				submeshes.append(copy.copy(obj))
		if bReWrite and not bDoSkin: #if still true
			submeshBoneCount = 0
			for bone in mdl.bones:
				for mesh in submeshes:
					if bone.name == mesh.name: #fbx is stupid and adds submeshes as bones to boneless meshes
						submeshBoneCount = submeshBoneCount + 1
						break
			if len(mdl.bones) > 0 and submeshBoneCount != len(submeshes):
				bDoSkin = True
					
	#Prompt for source mesh to export over / export options:
	def showOptionsDialog():
		global bReWrite
		nonlocal bDoSkin, submeshes, f, newMeshName
		fileName = None
		if noesis.optWasInvoked("-meshfile"):
			newMeshName = noesis.optGetArg("-meshfile")
			if noesis.optWasInvoked("-adv"):
				newMeshName = getExportName(newMeshName)
			if newMeshName:
				newMesh = rapi.loadIntoByteArray(newMeshName)
				f = NoeBitStream(newMesh)
				return newMeshName
		else:
			newMeshName = getExportName(fileName)
		if newMeshName == None:
			return 0
		while not bReWrite and not rapi.checkFileExists(newMeshName):
			print ("File not found!")
			newMeshName = getExportName(fileName)	
			fileName = newMeshName
			if newMeshName == None:
				return 0
		if not bReWrite:		
			newMesh = rapi.loadIntoByteArray(newMeshName)
			f = NoeBitStream(newMesh)
		else:
			checkReWriteMeshes()
			if not bReWrite:
				showOptionsDialog()
		
	print ("		----" + Version + " by alphaZomega----\nOpen fmt_RE_MESH.py in your Noesis plugins folder to change global exporter options.\nExport Options:\n Input these options in the `Advanced Options` field to use them, or use in CLI mode\n -flip  =  OpenGL / flipped handedness (fixes seams and inverted lighting on some models)\n -bones = save new skeleton from Noesis to the MESH file\n -bonenumbers = Export with bone numbers, to save a new bone map\n -meshfile [filename]= Input the location of a [filename] to export over that file\n -noprompt = Do not show any prompts\n -rewrite = save new MainMesh and SubMesh order (also saves bones)\n -vfx = Export as a VFX mesh\n -b = Batch conversion mode\n -adv = Show Advanced Options dialog window\n") #\n -lod = export with additional LODGroups") # 
	
	ext = os.path.splitext(rapi.getOutputName())[1]
	RERTBytes = 0
	
	sGameName = "RE2" 
	if ext.find(".1808282334") != -1:
		sGameName = "DMC5"
	elif ext.find(".1902042334") != -1:
		sGameName = "RE3"
	elif ext.find(".2102020001") != -1:
		sGameName = "ReVerse"
	elif ext.find(".2101050001") != -1:
		sGameName = "RE8"
	elif (ext.find(".2109108288") != -1) or (ext.find(".220128762") != -1): #RE2/RE3RT, and RE7RT
		sGameName = "RERT"
		RERTBytes = 8
	elif ext.find(".2109148288") != -1: #MHRise Sunbreak
		realGameName = "MHRise Sunbreak"
		sGameName = "RERT"
		RERTBytes = 8
	elif ext.find(".2008058288") != -1: #Vanilla MHRise
		sGameName = "MHRise"
	elif ext.find(".220721329") != -1:
		sGameName = "SF6"
		isSF6 = True
	elif ext.find(".221108797") != -1:
		sGameName = "RE4"
		isSF6 = 2
		
	setOffsets(formats[sGameName]["meshVersion"])
	
	print ("\n				  ", realGameName if 'realGameName' in locals() else sGameName, "\n")
	
	#merge Noesis-split meshes back together:
	if meshesToExport[0].name.find("_") == 4 and meshesToExport[0].name != meshesToExport[0].sourceName:
		meshesToExport = recombineNoesisMeshes(mdl)
	
	#Remove Blender numbers from all names
	for mesh in mdl.meshes:
		if mesh.name.find('.') != -1:
			print ("Renaming Mesh " + str(mesh.name) + " to " + str(mesh.name.split('.')[0]))
			mesh.name = mesh.name.split('.')[0]
		if len(mesh.lmUVs) == 0: #make sure UV2 exists
			mesh.lmUVs = mesh.uvs
	
	#sort by name (if FBX reorganized):
	meshesToExport = sort_human(meshesToExport) 
	
	#Validate meshes are named correctly
	objToExport = []
	for i, mesh in enumerate(meshesToExport):
		ss = mesh.name.lower().split('_')			
		if len(ss) >= 6:
			if ss[1].isnumeric() and ss[3].isnumeric() and ss[5].isnumeric():
				objToExport.append(i)
				
	if bReWrite:
		if noesis.optWasInvoked("-adv"): # and noesis.optWasInvoked("-noprompt"):
			newMeshName = getExportName(rapi.getOutputName() or None)
		checkReWriteMeshes()
	else:
		showOptionsDialog()

	if f:
		magic = f.readUInt()
		if magic != 1213416781:
			noesis.messagePrompt("Not a MESH file.\nAborting...")
			return 0		
		bonesOffs = readUIntAt(f, bonesOffsLocation)
		if bonesOffs > 0:
			bDoSkin = True
	
	if not bReWrite:
		if newMeshName != None:
			print("Source Mesh:\n", newMeshName)
		else:
			return 0
	
	if bDoSkin:
		print ("  Rigged mesh detected, exporting with skin weights...")
	else:
		print("  No rigging detected")
		
	extension = os.path.splitext(rapi.getInputName())[1]
	vertElemCount = 3 


	#check if exporting bones and create skin bone map if so:
	if bDoSkin:
		vertElemCount += 1
		bonesList = []
		newSkinBoneMap = []
		maxBones = 1024 if isSF6 else 256
		
		if (bReWrite or bWriteBones) and dialogOptions.doCreateBoneMap:
			generateBoneMap(mdl)
		
		if bAddBoneNumbers == 1 or noesis.optWasInvoked("-bonenumbers"):
			bAddNumbers = True
		elif bAddBoneNumbers == 2:
			if len(mdl.bones) > maxBones:
				print ("Model has more than", maxBones, "bones, auto-enabling bone numbers...")
				bAddNumbers = True
			else:
				for bone in mdl.bones:
					if bone.name.find(':') != -1:
						bAddNumbers = True
						print (bone.name, "has a \':\' (colon) in its name, auto-enabling bone numbers...")
						break
		
		if (bReWrite or bWriteBones) and bForceRootBoneToBone0 and mdl.bones[0] != None and mdl.bones[0].name.lower() != "root" and mdl.bones[len(mdl.bones)-1].name.lower() == "root":
			print("WARNING: root is not bone[0], reorganizing heirarchy...")
			sortedBones = list(mdl.bones)
			rootIdx = len(sortedBones)-1
			sortedBones.remove(sortedBones[rootIdx])
			sortedBones.insert(0, mdl.bones[rootIdx])
			for i, bone in enumerate(sortedBones):
				bone.index = i
				if bone.parentIndex == rootIdx:
					bone.parentIndex = 0
				elif bone.parentIndex != -1:
					bone.parentIndex = bone.parentIndex + 1
			mdl.bones = tuple(sortedBones)
			for mesh in mdl.meshes:
				for weightsList in mesh.weights:
					indicesList = list(weightsList.indices)
					for i, idx in enumerate(indicesList):
						if idx == rootIdx:
							idx = 0
						else:
							indicesList[i] = idx + 1
					weightsList.indices = tuple(indicesList)
		
		for i, bone in enumerate(mdl.bones):
			if bone.name.find('_') == 8 and bone.name.startswith("bone"):
				print ("Renaming Bone " + str(bone.name) + " to " + bone.name[9:len(bone.name)] )
				bone.name = bone.name[9:len(bone.name)] #remove Noesis duplicate numbers
			if bone.name.find('.') != -1:
				print ("Renaming Bone " + str(bone.name) + " to " + str(bone.name.split('.')[0]))
				bone.name = bone.name.split('.')[0] #remove blender numbers
			
			if bone.name.find(':') != -1:
				bonesList.append(bone.name.split(':')[1]) #remove bone numbers
				if len(newSkinBoneMap) < maxBones:
					newSkinBoneMap.append(i)
			else:
				bonesList.append(bone.name)
				if not bAddNumbers and len(newSkinBoneMap) < maxBones:
					newSkinBoneMap.append(i)
					
		if bAddNumbers and len(newSkinBoneMap) == 0: #in case bone numbers is on but the skeleton has no bone numbers:
			print ("WARNING: No bone numbers detected, only the first", maxBones, "bones will be rigged")
			bAddNumbers = False
			for i, bone in enumerate(mdl.bones):
				if len(newSkinBoneMap) < maxBones:
					newSkinBoneMap.append(i)
	
	newBBOffs = 0

	#OLD WAY (reading source file, no rewrite):
	#====================================================================
	if not bReWrite:
		
		#header
		f.seek(numNodesLocation)
		numNodes = f.readUInt()
		f.seek(LOD1OffsetLocation)
		LOD1Offs = f.readUInt64()
		f.seek(vBuffHdrOffsLocation)  
		vBuffHdrOffs = f.readUInt64() 
		f.seek(bonesOffsLocation)   
		bonesOffs = f.readUInt64()  
		f.seek(nodesIndicesOffsLocation)  
		nodesIndicesOffs = f.readUInt64()  
		boneIndicesOffs = f.readUInt64()  
		f.seek(namesOffsLocation)
		namesOffs = f.readUInt64() 
		f.seek(floatsHdrOffsLocation)
		floatsHdrOffs = f.readUInt64() 
		
		newBBOffs = floatsHdrOffs
		f.seek(LOD1Offs)
		countArray = f.read("16B")
		numMats = countArray[1]
			
		#vertex buffer header
		f.seek(vBuffHdrOffs)
		vertElemHdrOffs = f.readUInt64()
		vertBuffOffs = f.readUInt64()
		print(f.tell(), vBuffHdrOffsLocation, vBuffHdrOffs, vertElemHdrOffs, vertBuffOffs)
		
		if isSF6:
			f.seek(8,1)
			print("vBuffSz at", f.tell())
			vertBuffSize = f.readUInt()
			face_buffOffsSF6 = f.readUInt()
			faceBuffOffs = face_buffOffsSF6 + vertBuffOffs
			print(faceBuffOffs)
			vertElemCountA = f.readUShort()
			vertElemCountB = f.readUShort()
		else:
			faceBuffOffs = f.readUInt64()
			if sGameName == "RERT":
				uknIntA = f.readUInt()
				uknIntB = f.readUInt()
			vertBuffSize = f.readUInt()
			faceBuffSize = f.readUInt()
			vertElemCountA = f.readUShort()
			vertElemCountB = f.readUShort()
			faceBufferSize2nd = f.readUInt64()
			blendshapesOffset = f.readUInt()
		
		f.seek(vertElemHdrOffs)
		vertElemHeaders = []
		for i in range(vertElemCountB):
			vertElemHeaders.append([f.readUShort(), f.readUShort(), f.readUInt()])
		
		for i in range(len(vertElemHeaders)):
			if vertElemHeaders[i][0] == 3:
				bDoUV2 = 1
			if vertElemHeaders[i][0] == 4:
				bDoSkin = 1
			if vertElemHeaders[i][0] == 5:
				bDoColors = True
		
		nameOffsets = []	
		f.seek(namesOffs)
		for i in range(numNodes):
			nameOffsets.append(f.readUInt64())
		
		names = []
		for i in range(numNodes):
			f.seek(nameOffsets[i])
			names.append(f.readString())
		
		boneNameAddressList = []
		matNameAddressList = []
		
		if bDoSkin:		
			boneRemapTable = []
			boneInds = []
			
			#Skeleton
			f.seek(bonesOffs+4)
			boneMapCount = f.readUInt()
			
			f.seek(bonesOffs)			
			boneCount = f.readUInt()
			f.seek(12,1)
			hierarchyOffs = f.readUInt64()
			localOffs = f.readUInt64()
			globalOffs = f.readUInt64()
			inverseGlobalOffs = f.readUInt64()
				
			for b in range(boneMapCount):
				boneRemapTable.append(f.readUShort())
			
			f.seek(boneIndicesOffs)
			for i in range(boneCount):
				boneInds.append(f.readUShort())
				boneMapIndex = -1
				for b in range(len(boneRemapTable)):
					if boneRemapTable[b] == i:
						boneMapIndex = b
			
			f.seek(namesOffs)
			for i in range(countArray[1]): 
				matNameAddressList.append(f.readUInt64())
				
			for i in range(boneCount):
				boneNameAddressList.append(f.readUInt64())
		
		if isSF6:
			f.seek(232)
		elif sGameName == "RERT" or sGameName == "ReVerse" or sGameName == "MHRise" or sGameName == "RE8":
			f.seek(192)
		else:
			f.seek(200)
			f.seek(f.readUInt64())
			
		offsetInfo = []
		for i in range(numLODs): #LODGroup Offsets
			offsetInfo.append(f.readUInt64())
		
		#prepare array of submeshes for export:
		mainmeshCount = 0
		for ldc in range(numLODs): 
			f.seek(offsetInfo[ldc])
			mainmeshCount = f.readUByte()
			f.seek(3,1)
			uknFloat = f.readFloat()
			offsetSubOffsets = f.readUInt64()
			f.seek(offsetSubOffsets)
			meshOffsets = []
			for i in range(mainmeshCount):
				meshOffsets.append(f.readUInt64())
			for mmc in range(mainmeshCount):
				f.seek(meshOffsets[mmc])
				meshVertexInfo.append([f.readUByte(), f.readUByte(), f.readUShort(), f.readUInt(), f.readUInt(), f.readUInt()])
				for smc in range(meshVertexInfo[mmc][1]):
					matID = f.readUInt() + 1
					bFind = 0
					sourceGroupID = meshVertexInfo[len(meshVertexInfo)-1][0] if bReadGroupIds else (mmc+1)
					for s in range(len(objToExport)):
						#print (meshesToExport[objToExport[s]].name)
						sName = meshesToExport[objToExport[s]].name.split('_')
						thisGroupID = sName[3]
						if int(sName[1]) == (ldc+1) and int(thisGroupID) == (sourceGroupID) and ((not bUseOldNamingScheme and int(sName[5]) == (smc+1)) or (bUseOldNamingScheme and int(sName[5]) == (matID))):
							submeshes.append(copy.copy(meshesToExport[objToExport[s]]))
							bFind = 1							
							break
					if not bFind:  #create invisible placeholder submesh
						blankMeshName = "LODGroup_" + str(ldc+1) + "_MainMesh_" + str(sourceGroupID) + "_SubMesh_" + str(smc+1)
						blankTangent = NoeMat43((NoeVec3((0,0,0)), NoeVec3((0,0,0)), NoeVec3((0,0,0)), NoeVec3((0,0,0)))) 
						blankWeight = NoeVertWeight([0,0,0,0,0,0,0,0], [1,0,0,0,0,0,0,0])
						blankMesh = NoeMesh([0, 1, 2], [NoeVec3((0.00000000001,0,0)), NoeVec3((0,0.00000000001,0)), NoeVec3((0,0,0.00000000001))], blankMeshName, blankMeshName, -1, -1) #positions and faces
						blankMesh.setUVs([NoeVec3((0,0,0)), NoeVec3((0,0,0)), NoeVec3((0,0,0))]) #UV1
						blankMesh.setUVs([NoeVec3((0,0,0)), NoeVec3((0,0,0)), NoeVec3((0,0,0))], 1) #UV2
						blankMesh.setTangents([blankTangent, blankTangent, blankTangent]) #Normals + Tangents
						if bDoColors:
							blankMesh.setColors((NoeVec4((1,1,1,1)), NoeVec4((1,1,1,1)), NoeVec4((1,1,1,1)))) #vertex colors
						if bonesOffs > 0:
							blankMesh.setWeights([blankWeight,blankWeight,blankWeight]) #Weights + Indices
						submeshes.append(blankMesh)
						print (blankMeshName, "not found in FBX")
					f.seek(12, 1)	
		f.seek(0)
		
	if (len(submeshes) == 0):
		return 0
	
	#will be bounding box:
	min = NoeVec4((10000.0, 10000.0, 10000.0, fDefaultMeshScale))
	max = NoeVec4((-10000.1, -10000.1, -10000.1, fDefaultMeshScale))	
	
	bColorsExist = False
	for mesh in submeshes:
		for col in mesh.colors:
			if not bColorsExist and len(col) > 1:
				bColorsExist = True
				print ("  Vertex colors detected")
				break
		if bReWrite and bColorsExist:
			bDoColors = True
			break
			
	if bRotateBonesUpright:
		rot_mat = NoeMat43(((1, 0, 0), (0, -1, 0), (0, 0, 1), (0, 0, 0)))
		for bone in mdl.bones:
			bone.setMatrix( (bone.getMatrix().inverse() * rot_mat).inverse()) 	#rotate back to normal
			
			
	#NEW WAY (rewrite)
	#====================================================================
	if bReWrite: #save new mesh order	
		bDoUV2 = True
		#prepare new submesh order:
		newMainMeshes = []; newSubMeshes = []; newMaterialNames = []; 
		indicesBefore = 0; vertsBefore = 0; mmIndCount = 0; mmVertCount = 0
		lastMainMesh = submeshes[0].name.split('_')[3]
		meshOffsets= []
		
		for i, mesh in enumerate(submeshes):
			mat = mesh.name.split('__', 1)[1]
			if mat not in newMaterialNames:
				newMaterialNames.append(mat)
				
		numMats = len(newMaterialNames)
		print ("\nMESH Material Count:", numMats)
		
		for i, mesh in enumerate(submeshes):
			splitName = mesh.name.split('_')
			splitMatNames = mesh.name.split('__', 1)
			key = len(newMainMeshes)
			newGroupID = splitName[3]
			#try:
			if len(splitName) <= 6:
				bReWrite = False
				break
			else:
				newMaterialID = newMaterialNames.index(splitMatNames[1])
				if newGroupID != lastMainMesh:
					newMainMesh = (newSubMeshes, mmVertCount, mmIndCount, int(lastMainMesh))
					newMainMeshes.append(newMainMesh)
					newSubMeshes = []; mmIndCount = 0; mmVertCount = 0
					lastMainMesh = newGroupID
					
				newSubMeshes.append((newMaterialID, len(mesh.indices) , vertsBefore, indicesBefore))
				vertsBefore += len(mesh.positions)
				mmVertCount += len(mesh.positions)
				indicesBefore += len(mesh.indices)
				mmIndCount += len(mesh.indices)
				if i == len(submeshes)-1:
					newMainMesh = (newSubMeshes, mmVertCount, mmIndCount,  int(lastMainMesh))
					newMainMeshes.append(newMainMesh)
			#except:
			#	print("Failed to parse mesh name", mesh.name)
		
		#print(newMainMeshes)
		
		LOD1Offs = 168 if isSF6 else 128 if (sGameName == "RERT" or sGameName == "RE8" or sGameName == "MHRise") else 136
		
		#header:
		bs.writeUInt(1213416781) #MESH
		if sGameName == "RE2" or sGameName == "RE3" or sGameName == "DMC5":
			bs.writeUInt(386270720) #version no
		elif sGameName == "RE8":
			bs.writeUInt(2020091500)
		elif sGameName == "MHRise":
			bs.writeUInt(2007158797)
		elif sGameName == "RERT":
			bs.writeUInt(21041600)
		elif isSF6 == 2: 
			bs.writeUInt(220822879) #RE4R
		elif isSF6 == True or True:
			bs.writeUInt(220705151) #SF6 and all others
			
		bs.writeUInt(0) #Filesize
		bs.writeUInt(0) #LODGroupHash
		
		if isSF6:
			bs.writeUByte(3) #flag
			bs.writeUByte(2) #solvedOffset
			bs.writeUShort(0) #uknSF6
			bs.writeUInt(len(mdl.bones) * bDoSkin + numMats) #Node Count
			bs.writeUInt64(0) #ukn
			bs.writeUInt64(LOD1Offs) #LODOffs
			bs.writeUInt64(0) #ShadowLODOffs
			bs.writeUInt64(0) #OccluderMeshOffs
			bs.writeUInt64(0) #bsHeaderOffs
			bs.writeUInt64(0) #ukn2
			bs.writeUInt64(0) #vert_buffOffs
			bs.writeUInt64(0) #normalsRecalcOffs
			bs.writeUInt64(0) #groupPivotOffs      
			bs.writeUInt64(0) #BBHeaderOffs
			bs.writeUInt64(0) #bonesOffs
			bs.writeUInt64(0) #matIndicesOffs
			bs.writeUInt64(0) #boneIndicesOffs
			bs.writeUInt64(0) #bsIndicesOffs
			bs.writeUInt64(0) #ukn3
			bs.writeUInt64(0) #namesOffs
			bs.writeUInt64(0) #verticesOffset
			bs.writeUInt64(0) #ukn4/padding
		else:
			bs.writeUShort(3) #flag
			bs.writeUShort(len(mdl.bones) * bDoSkin + numMats) #Node Count
			bs.writeUInt(0) #LODGroupHash
			bs.writeUInt64(LOD1Offs) #LODs address
			bs.writeUInt64(0) #Shadow LODs address
			bs.writeUInt64(0) #occluderMeshOffs
			bs.writeUInt64(0) #Bones Address
			bs.writeUInt64(0) #Normal Recalculation Address
			bs.writeUInt64(0) #Blendshapes Header Address
			bs.writeUInt64(0) #Floats Header Address
			bs.writeUInt64(0) #Vertex Buffer Headers Address
			bs.writeUInt64(0)
			bs.writeUInt64(0) #Material Indices Table Address
			bs.writeUInt64(0) #Bones Indices Table Address
			bs.writeUInt64(0) #Blendshapes Indices Table Address
			bs.writeUInt64(0) #Names Address
			if sGameName == "RE2" or sGameName == "RE3" or sGameName == "DMC5":
				bs.writeUInt64(0)
		
		#LODs:
		bs.writeByte(1) #set to one LODGroup
		bs.writeByte(len(newMaterialNames)) #mat count
		bs.writeByte(2) #set to 2 UV channels
		bs.writeByte(1) #unknown
		bs.writeUInt(len(submeshes)) #total mesh count
		
		if BBskipBytes==8:
			bs.writeUInt64(0)
		
		for i in range(6):
			bs.writeUInt64(0) #main bounding sphere+box placeholder
		
		bs.writeUInt64(bs.tell()+8) #offset to LODOffsets
		
		if (bs.tell()+8) % 16 != 0:
			bs.writeUInt64(bs.tell()+16) #first (and only) LODOffset
		else:
			bs.writeUInt64(bs.tell()+8)
		padToNextLine(bs)
			
		#Write LODGroup:
		bs.writeUInt(len(newMainMeshes))
		LODDist = openOptionsDialog.LODDist if openOptionsDialog else 0.02667995
		bs.writeFloat(LODDist) #unknown, maybe LOD distance change
		bs.writeUInt64(bs.tell()+8) #Mainmeshes offset
		
		newMainMeshesOffset = bs.tell()
		for i in range(len(newMainMeshes)):
			bs.writeUInt64(0)
		
		while(bs.tell() % 16 != 0):
			bs.writeByte(0)

		#write new MainMeshes:
		for i, mm in enumerate(newMainMeshes):
			
			newMMOffset = bs.tell()
			bs.writeByte(mm[len(mm)-1]) #Group ID
			bs.writeByte(len(mm[0])) #Submesh count
			bs.writeShort(0)
			bs.writeInt(0)
			bs.writeUInt(mm[1]) #MainMesh index count
			bs.writeUInt(mm[2]) #MainMesh vertex count
			meshVertexInfo.append([i, len(mm[0]), 0, 0, mm[1], mm[2]])
			
			for j, submesh in enumerate(mm[0]):
				#print ("New mainmesh GroupID", mm[len(mm)-1], "submesh", j)
				bs.writeUInt(submesh[0])
				bs.writeUInt(submesh[1])
				bs.writeUInt(submesh[2])
				bs.writeUInt(submesh[3])
				if sGameName != "RE7" and sGameName != "RE2" and sGameName != "RE3" and sGameName != "DMC5":
					bs.writeUInt64(0)
			pos = bs.tell()
			bs.seek(newMainMeshesOffset + i * 8)
			bs.writeUInt64(newMMOffset)
			meshOffsets.append(newMMOffset)
			bs.seek(pos)
		
		bonesOffs = bs.tell()
		
		if bDoSkin:
			bs.seek(bonesOffsLocation)
		else:
			bs.seek(nodesIndicesOffsLocation) #to material indices offset instead
			
		bs.writeUInt64(bonesOffs)
		bs.seek(bonesOffs)
		mainmeshCount = len(newMainMeshes)
		
	if bDoUV2:
		vertElemCount += 1
	if bDoColors:
		vertElemCount += 1

	if (bReWrite or bWriteBones): 
		if bDoSkin:
			boneRemapTable = []
			
			maxBoneMapLength = 256 if not isSF6 else 1024
			
			if bAddNumbers and len(newSkinBoneMap) > 0:
				boneMapLength = len(newSkinBoneMap)
			else:
				boneMapLength = maxBoneMapLength if len(mdl.bones) > maxBoneMapLength else len(mdl.bones)

			if not bReWrite:
				bs.writeBytes(f.readBytes(bonesOffs)) #to bone name start
		
			#write new skeleton header
			bs.writeUInt(len(mdl.bones)) #bone count
			bs.writeUInt(boneMapLength)  #bone map count

			for b in range(5): 
				bs.writeUInt64(0)
			
			#write skin bone map:
			if bAddNumbers and len(newSkinBoneMap) > 0:
				for i in range(len(newSkinBoneMap)):
					bs.writeUShort(newSkinBoneMap[i])
				boneRemapTable = newSkinBoneMap
			else:
				for i in range(boneMapLength): 
					bs.writeUShort(i)
					boneRemapTable.append(i)
			padToNextLine(bs)
			
			if (len(boneRemapTable) > maxBoneMapLength):
				print ("WARNING! Bone map is greater than", maxBoneMapLength, "bones!")
			
			#write hierarchy
			newHierarchyOffs = bs.tell()
			for i, bone in enumerate(mdl.bones):
				bs.writeUShort(i) # bone index
				bs.writeUShort(bone.parentIndex)
				nextSiblingIdx = -1
				for j, bn in enumerate(mdl.bones):
					if i < j and bone != bn and bone.parentIndex == bn.parentIndex:
						nextSiblingIdx = j
						break
				bs.writeUShort(nextSiblingIdx)
				nextChildIdx = -1
				for j, bn in enumerate(mdl.bones):
					if bn.parentIndex == i:
						nextChildIdx = j
						break
				bs.writeUShort(nextChildIdx)
				cousinIdx = -1
				cousinBoneName = ""
				bnName = bonesList[i].lower()
				if bnName.startswith('r_'): 
					cousinBoneName = bnName.replace('r_','l_')
				elif bnName.startswith('l_'):
					cousinBoneName = bnName.replace('l_','r_')
				elif isSF6 or bnName.startswith("root") or bnName.startswith("cog") or bnName.startswith("hip") \
				or bnName.startswith("waist") or bnName.startswith("spine") or bnName.startswith("chest") \
				or bnName.startswith("stomach") or bnName.startswith("neck") or bnName.startswith("head") \
				or bnName.startswith("null_"):
					cousinIdx = i
				if cousinBoneName != "":
					for j in range(len(mdl.bones)):
						if bonesList[j].lower() == cousinBoneName:
							cousinIdx = j
							break
				bs.writeUShort(cousinIdx)
				padToNextLine(bs)
		
			#prepare transform data:
			localTransforms = []
			globalTransforms = []
			for bone in mdl.bones:
				boneGlobalMat = bone.getMatrix().toMat44()
				boneGlobalMat[3] = boneGlobalMat[3] * 0.01
				boneGlobalMat[3][3] = 1.0
				globalTransforms.append(boneGlobalMat)
				if bone.parentIndex != -1:
					pMat = mdl.bones[bone.parentIndex].getMatrix().toMat44()
					boneLocalMat = (bone.getMatrix().toMat44() * pMat.inverse())
					boneLocalMat[3] = boneLocalMat[3] * 0.01
					boneLocalMat[3][3] = 1.0
					localTransforms.append(boneLocalMat)
				else:
					localTransforms.append(boneGlobalMat)
			
			#write local bone transforms:
			newLocalOffs = bs.tell()
			for i in range(len(localTransforms)):
				bs.writeBytes(localTransforms[i].toBytes())
			
			#write global bone transforms:
			newGlobalOffs = bs.tell()
			for i in range(len(globalTransforms)):
				bs.writeBytes(globalTransforms[i].toBytes())
			
			#write inverse global bone transforms:
			newInvGlobOffs = bs.tell()
			for i in range(len(globalTransforms)):
				bs.writeBytes(globalTransforms[i].inverse().toBytes())
		
		#collect material names:
		materialNames = []
		if bReWrite:
			materialNames = newMaterialNames
		else:
			for i in range(numMats): 
				f.seek(matNameAddressList[i])
				materialNames.append(f.readString())
		
		#write material indices:
		newMatIndicesOffs = bs.tell()
		for i in range(numMats): 
			if bReWrite:
				bs.writeUShort(i)
			else:
				f.seek(nodesIndicesOffs + i * 2)
				bs.writeUShort(f.readUShort())
		padToNextLine(bs)
		
		if bDoSkin:
			boneInds = []
			#write bone map indices:
			newBoneMapIndicesOffs = bs.tell()
			for i in range(len(mdl.bones)): 
				bs.writeUShort(numMats + i)
				boneInds.append(numMats + i)
			padToNextLine(bs)
		
		#write names offsets:
		newNamesOffs = bs.tell()
		nameStringsOffs = newNamesOffs + (numMats + len(mdl.bones) * bDoSkin) * 8
		while nameStringsOffs % 16 != 0:
			nameStringsOffs += 1
		
		for i in range(numMats): 
			bs.writeUInt64(nameStringsOffs)
			nameStringsOffs += len(materialNames[i]) + 1
		if bDoSkin:
			for i in range(len(mdl.bones)): 
				bs.writeUInt64(nameStringsOffs)
				nameStringsOffs += len(bonesList[i]) + 1
		padToNextLine(bs)
		
		names = []
		#write name strings
		for i in range(len(materialNames)):
			bs.writeString(materialNames[i])
			names.append(materialNames[i])
		if bDoSkin:
			for i in range(len(bonesList)): 
				bs.writeString(bonesList[i])
				names.append(bonesList[i])
		padToNextLine(bs)
		
		if bDoSkin:
			#write bounding boxes
			newBBOffs = bs.tell()
			bs.writeUInt64(len(newSkinBoneMap))
			bs.writeUInt64(bs.tell() + 8)
			for i in range(len(newSkinBoneMap)):
				for j in range(3): bs.writeFloat(-BoundingBoxSize)
				bs.writeFloat(1)
				for j in range(3): bs.writeFloat(BoundingBoxSize)
				bs.writeFloat(1)
			newVertBuffHdrOffs = bs.tell()
			
			#fix bones header
			bs.seek(bonesOffs + 16)
			bs.writeUInt64(newHierarchyOffs)
			bs.writeUInt64(newLocalOffs)
			bs.writeUInt64(newGlobalOffs)
			bs.writeUInt64(newInvGlobOffs)
		else:
			newVertBuffHdrOffs = bs.tell()
		
		#fix main header
		bs.seek(numNodesLocation)
		bs.writeUShort(numMats + len(mdl.bones) * bDoSkin) #numNodes
			
		if bDoSkin:
			bs.seek(floatsHdrOffsLocation)
			bs.writeUInt64(newBBOffs)
			bs.seek(vBuffHdrOffsLocation)
			bs.writeUInt64(newVertBuffHdrOffs)
			bs.seek(nodesIndicesOffsLocation)
			bs.writeUInt64(newMatIndicesOffs)
			bs.writeUInt64(newBoneMapIndicesOffs)
		else:
			bs.seek(vBuffHdrOffsLocation)
			bs.writeUInt64(newVertBuffHdrOffs)
		bs.seek(namesOffsLocation)
		bs.writeUInt64(newNamesOffs)
		
		#fix vertexBufferHeader
		bs.seek(newVertBuffHdrOffs)
		
		SF6SkipBytes = 0 if not isSF6 else 32
		newVertBuffOffs = newVertBuffHdrOffs + 72 + SF6SkipBytes + 8*bDoSkin + 8*bDoUV2 + 8*bDoColors + 2*RERTBytes
		
		bs.writeUInt64(bs.tell() + 48 + SF6SkipBytes + 2*RERTBytes)
		bs.writeUInt64(newVertBuffOffs)
		
		if sGameName == "RERT":
			bs.writeUInt64(0)
		bs.writeUInt64(0)
		bs.writeUInt64(0)
		bs.writeShort(vertElemCount)
		bs.writeShort(vertElemCount)
		bs.writeUInt64(0)
		bs.writeInt(-newVertBuffOffs)
		
		if isSF6:
			for i in range(4):
				bs.writeUInt64(0)
		if sGameName == "RERT": # and (bs.tell() % 8) != 0:
			bs.writeUInt64(0)
		
		bs.writeUInt64(786432) #positions VertElemHeader
		bs.writeUInt64(524289) #normal VertElemHeader
		bs.writeUInt64(262146) #UV0 VertElemHeader
		if bDoUV2:
			bs.writeUInt64(262147) #UV2 VertElemHeader
		if bDoSkin:
			bs.writeUInt64(1048580) #Skin VertElemHeader
		if bDoColors:
			bs.writeUInt64(262149) #Colors VertElemHeader
			
	elif not bReWrite:
		bs.writeBytes(f.readBytes(vertBuffOffs)) #copy to vertex buffer header
		newVertBuffHdrOffs = bs.tell()

	
	vertexStrideStart = 0
	submeshVertexCount = []
	submeshVertexStride = []
	submeshFaceCount = []
	submeshFaceStride = []
	submeshFaceSize = []
	boneWeightBBs = {}

	#Write vertex data
	vertexPosStart = bs.tell()
	for mesh in submeshes:
		submeshVertexStride.append(vertexStrideStart)
		for vcmp in mesh.positions:
			bs.writeBytes((vcmp * newScale).toBytes())
			if vcmp[0] > max[0]: max[0] = vcmp[0] 	#calculate main bounding box
			if vcmp[0] < min[0]: min[0] = vcmp[0]
			if vcmp[1] > max[1]: max[1] = vcmp[1]
			if vcmp[1] < min[1]: min[1] = vcmp[1]
			if vcmp[2] > max[2]: max[2] = vcmp[2]
			if vcmp[2] < min[2]: min[2] = vcmp[2]
		submeshVertexCount.append(len(mesh.positions))
		vertexStrideStart += len(mesh.positions)
		
	normalTangentStart = bs.tell()	
	for m, mesh in enumerate(submeshes):
		for v, vcmp in enumerate(mesh.tangents):
			bs.writeByte(int(vcmp[0][0] * 127 + 0.5000000001)) #normal
			bs.writeByte(int(vcmp[0][1] * 127 + 0.5000000001))
			bs.writeByte(int(vcmp[0][2] * 127 + 0.5000000001))
			bs.writeByte(0)
			bs.writeByte(int(vcmp[2][0] * 127 + 0.5000000001)) #bitangent
			bs.writeByte(int(vcmp[2][1] * 127 + 0.5000000001))
			bs.writeByte(int(vcmp[2][2] * 127 + 0.5000000001))
			TNW = dot(cross(vcmp[0], vcmp[1]), vcmp[2])
			if (TNW < 0.0): #default way
				bs.writeByte(w1)
			else:
				bs.writeByte(w2)
				
	UV0start = bs.tell()
	for mesh in submeshes:
		for vcmp in mesh.uvs:
			bs.writeHalfFloat(vcmp[0])
			bs.writeHalfFloat(vcmp[1])
				
	UV1start = bs.tell()
	if bDoUV2:
		for mesh in submeshes:
			if len(mesh.lmUVs) != len(mesh.positions):
				mesh.lmUVs = mesh.uvs
			for vcmp in mesh.lmUVs:
				bs.writeHalfFloat(vcmp[0])
				bs.writeHalfFloat(vcmp[1])

	def writeBoneID(bID, i):
		if isSF6 == True:
			if i==3:
				bs.writeBits(0, 2)
			bs.writeBits(bID, 10)
		else:
			bs.writeUByte(bID)
	
	boneIdMax = 8 if not isSF6 else 6
	bnWeightStart = bs.tell()
	
	if bDoSkin:
		for m, mesh in enumerate(submeshes):
			pos = bs.tell()
			for vcmp in mesh.weights: #write 0's
				for i in range(4):
					bs.writeFloat(0)
			bs.seek(pos)
			
			for i, vcmp in enumerate(mesh.weights): #write bone indices & weights over 0's
				total = 0
				tupleList = []
				weightList = []
				vertPos = mesh.positions[i]
				for idx in range(len(vcmp.weights)):
					weightList.append(round(vcmp.weights[idx] * 255.0))
					total += weightList[idx]
				if bNormalizeWeights and total != 255:
					weightList[0] += 255 - total
					print ("Normalizing vertex weight", mesh.name, "vertex", i,",", total)
					
				for idx in range(len(vcmp.weights)):
					if idx > boneIdMax:
						if not isSF6: 
							print ("Warning: ", mesh.name, "vertex", i,"exceeds the vertex weight limit of ", boneIdMax, "!", )
						break
					elif vcmp.weights[idx] != 0:				
						byteWeight = weightList[idx]
						tupleList.append((byteWeight, vcmp.indices[idx]))
					if bCalculateBoundingBoxes:
						thisBoneBB = boneWeightBBs[ vcmp.indices[idx] ] if vcmp.indices[idx] in boneWeightBBs else [999999.0, 999999.0, 999999.0, -999999.0, -999999.0, -999999.0]
						if vertPos[0] < thisBoneBB[0]: thisBoneBB[0] = vertPos[0]
						if vertPos[1] < thisBoneBB[1]: thisBoneBB[1] = vertPos[1]
						if vertPos[2] < thisBoneBB[2]: thisBoneBB[2] = vertPos[2]
						if vertPos[0] > thisBoneBB[3]: thisBoneBB[3] = vertPos[0]
						if vertPos[1] > thisBoneBB[4]: thisBoneBB[4] = vertPos[1]
						if vertPos[2] > thisBoneBB[5]: thisBoneBB[5] = vertPos[2]
						boneWeightBBs[ vcmp.indices[idx] ] = thisBoneBB
						
				tupleList = sorted(tupleList, reverse=True) #sort in ascending order
				pos = bs.tell()
				lastBone = 0
				for idx in range(len(tupleList)):
					bFind = False
					for b in range(len(boneRemapTable)):
						if names[boneInds[boneRemapTable[b]]] == bonesList[tupleList[idx][1]]:
							writeBoneID(b, idx)
							lastBone = b
							bFind = True
							break	
					if bFind == False: #assign unmatched bones
						if not bRigToCoreBones:
							writeBoneID(lastBone, idx)
						else:
							for b in range(lastBone, 0, -1):
								if names[boneInds[boneRemapTable[b]]].find("spine") != -1 or names[boneInds[boneRemapTable[b]]].find("hips") != -1:
									writeBoneID(b, idx)
									break
									
				for x in range(len(tupleList), 8):
					writeBoneID(lastBone, x)
				
				bs.seek(pos+8)
				for wval in range(len(tupleList)):
					bs.writeUByte(tupleList[wval][0])
				bs.seek(pos+16)
							
	colorsStart = bs.tell()
	if bDoColors:
		for m, mesh in enumerate(submeshes):
			if bColorsExist:
				for p, pos in enumerate(mesh.positions):
					RGBA = mesh.colors[p] if p < len(mesh.colors) else NoeVec4((1.0, 1.0, 1.0, 1.0))
					for c in range(4): 
						color = RGBA[c] if c < len(RGBA) else 1.0
						bs.writeUByte(int(color * 255 + 0.5))
			else:
				for p, pos in enumerate(mesh.positions):
					bs.writeInt(-1)
	
	vertexDataEnd = bs.tell()
	
	for mesh in submeshes:
		faceStart = bs.tell()
		submeshFaceStride.append(faceStart - vertexDataEnd)
		submeshFaceCount.append(len(mesh.indices))
		submeshFaceSize.append(len(mesh.indices))
		for idx in mesh.indices:
			bs.writeUShort(idx)
		if ((bs.tell() - faceStart) / 6) % 2 != 0: #padding
			bs.writeUShort(0)
	faceDataEnd = bs.tell()
	
	#update mainmesh and submesh headers
	loopSubmeshCount = 0
	for ldc in range(numLODs): 
		for mmc in range(mainmeshCount):
			mainmeshVertexCount = 0
			mainmeshFaceCount = 0
			bs.seek(meshOffsets[mmc] + 16)
			
			for smc in range(meshVertexInfo[mmc][1]):
				bs.seek(4, 1)
				bs.writeUInt(submeshFaceCount[loopSubmeshCount])
				bs.writeUInt(int(submeshFaceStride[loopSubmeshCount] / 2))
				bs.writeUInt(submeshVertexStride[loopSubmeshCount])
				if sGameName == "RERT" or sGameName == "ReVerse" or sGameName == "MHRise" or sGameName == "RE8" or sGameName == "SF6" or sGameName == "RE4":
					bs.seek(8, 1)
				mainmeshVertexCount += submeshVertexCount[loopSubmeshCount]
				mainmeshFaceCount += submeshFaceSize[loopSubmeshCount]
				loopSubmeshCount += 1
			bs.seek(meshOffsets[mmc]+8)
			bs.writeUInt(mainmeshVertexCount)
			bs.writeUInt(mainmeshFaceCount)
		
	#Fix vertex buffer header:
	skipAmt = 16 if not isSF6 else 24
	fcBuffSize = faceDataEnd - vertexDataEnd
	if bReWrite or bWriteBones:
		bs.seek(newVertBuffHdrOffs+skipAmt) 
	else: 
		bs.seek(vBuffHdrOffs+skipAmt)
	
	if isSF6:
		facesDiff = (80 + 8*vertElemCountB if bWriteBones else 0) if not bReWrite else (80 + 8*vertElemCount)
		bs.writeUInt(faceDataEnd - vertexPosStart) #total buffer size
		#print("faces offset", bs.tell(), vertexDataEnd, newVertBuffHdrOffs, facesDiff, vertexDataEnd - newVertBuffHdrOffs - facesDiff)
		bs.writeUInt(vertexDataEnd - newVertBuffHdrOffs - facesDiff) #face buffer offset
		bs.seek(4,1) #element counts
		bs.writeUInt(faceDataEnd - vertexPosStart) #total buffer size2
		bs.writeUInt(faceDataEnd - vertexPosStart) #total buffer size3
		bs.writeInt(-(vertexPosStart))
		bs.seek(32, 1)
	else:
		bs.writeUInt64(vertexDataEnd) #face buffer offset
		bs.seek(RERTBytes, 1)
		bs.writeUInt(vertexDataEnd - vertexPosStart) #vertex buffer size
		bs.writeUInt(fcBuffSize) #face buffer size
		bs.seek(4,1) #element counts
		bs.writeUInt64(fcBuffSize)
		bs.writeInt(-(vertexPosStart))
	
	if bReWrite:
		bs.seek(newVertBuffHdrOffs + 48 + SF6SkipBytes + (RERTBytes * 2))
	else:
		bs.seek(RERTBytes, 1)
	
	vertElemHdrStart = bs.tell()
	
	for i in range (vertElemCount):
		elementType = bs.readUShort()
		elementSize = bs.readUShort()
		if elementType == 0:
			bs.writeUInt(vertexPosStart - vertexPosStart)
		elif elementType == 1:
			bs.writeUInt(normalTangentStart - vertexPosStart)
		elif elementType == 2:
			bs.writeUInt(UV0start - vertexPosStart)
		elif elementType == 3:
			bs.writeUInt(UV1start - vertexPosStart)
		elif elementType == 4:
			bs.writeUInt(bnWeightStart - vertexPosStart)
		elif elementType == 5:
			bs.writeUInt(colorsStart - vertexPosStart) 
	
	if isSF6: 
		bs.seek(136)
		bs.writeUInt64(vertElemHdrStart-16) #fix ukn3
		bs.seek(152)
		bs.writeUInt64(vertexPosStart) #fix Vertices offset
	
	#fix main bounding box:
	bs.seek(LOD1Offs+8+BBskipBytes)
	
	#Calculate Bounding Sphere:
	BBcenter = NoeVec3((min[0]+(max[0]-min[0])/2, min[1]+(max[1]-min[1])/2, min[2]+(max[2]-min[2])/2))
	sphereRadius = 0
	for mesh in mdl.meshes:
		for position in mesh.positions:
			distToCenter = (position - BBcenter).length()
			if distToCenter > sphereRadius: 
				sphereRadius = distToCenter
				
	bs.writeBytes((BBcenter * newScale).toBytes()) #Bounding Sphere
	bs.writeFloat(sphereRadius * newScale) #Bounding Sphere radius
	bs.writeBytes((min * newScale).toBytes()) #BBox min
	bs.writeBytes((max * newScale).toBytes()) #BBox max
	if isSF6:
		bs.seek(-20,1); bs.writeUInt(1)
		bs.seek(12,1); bs.writeUInt(1)
	
	#fix skeleton bounding boxes:
	if bDoSkin and bCalculateBoundingBoxes:
		for idx, box in boneWeightBBs.items():
			try:
				if bReWrite or bWriteBones:
					remappedBoneIdx = newSkinBoneMap.index(idx)
				else:
					remappedBoneIdx = boneRemapTable.index(idx)
				pos = mdl.bones[newSkinBoneMap[remappedBoneIdx]].getMatrix()[3]
			except:
				continue
			bs.seek(newBBOffs+16+remappedBoneIdx*32)
			boneWeightBBs[idx] = [(box[0]-pos[0])*newScale, (box[1]-pos[1])*newScale, (box[2]-pos[2])*newScale, 1.0, (box[3]-pos[0])*newScale, (box[4]-pos[1])*newScale, (box[5]-pos[2])*newScale, 1.0]
			box = boneWeightBBs[idx]
			for coord in box:
				bs.writeFloat(coord)
	
	#set to only one LODGroup
	bs.seek(LOD1Offs)
	bs.writeByte(1)
	
	#disable shadow LODs
	bs.seek(LOD1OffsetLocation+8)
	bs.writeUInt(0)
	
	#disable normals recalculation data
	bs.seek(normalsRecalcOffsLocation)
	bs.writeUInt(0)
	
	#disable group pivots data
	bs.seek(88)
	bs.writeUInt(0)
	
	#set numModels flag
	doSetFlag = bSetNumModels or bDoVFX or (openOptionsDialog and openOptionsDialog.flag != -1)
	if doSetFlag or bReWrite:
		bs.seek(16)
		if openOptionsDialog and openOptionsDialog.flag != -1:
			bitFlag = openOptionsDialog.flag
		else:
			bitFlag = 0x00
			if bDoVFX or rapi.getOutputName().find("2109148288") != -1 or isSF6: 
				bitFlag = bitFlag + 0x80
			if bDoSkin: 
				bitFlag = bitFlag + 0x03
		print("Flag: ", bitFlag)
		bs.writeUByte(bitFlag)
	
	#remove blendshapes offsets
	bs.seek(bsHdrOffLocation)
	bs.writeUInt(0)
	bs.seek(bsIndicesOffLocation)
	bs.writeUInt(0)
	
	#fileSize
	bs.seek(8)
	bs.writeUInt(faceDataEnd) 
	
	return 1