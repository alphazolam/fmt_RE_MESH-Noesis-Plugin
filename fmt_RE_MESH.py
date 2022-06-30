#RE Engine [PC] - ".mesh" plugin for Rich Whitehouse's Noesis
#v2.9993 (June 30 2022)
#Authors: alphaZomega, originally by Gh0stblade 
#Special thanks: Chrrox 

#Options: These are global options that change or enable/disable certain features

#Var												Effect
#Export Extensions
bRayTracingExport			= True					#Enable or disable the export of RE2R, RE3R and RE7 RayTracing meshes and textures
bRE2Export 					= True					#Enable or disable export of mesh.1808312334 and tex.10 from the export list			
bRE3Export 					= True					#Enable or disable export of mesh.1902042334 and tex.190820018 from the export list
bDMCExport 					= True					#Enable or disable export of mesh.1808282334 and tex.11 from the export list
bRE7Export 					= True					#Enable or disable export of mesh.32 and tex.8 from the export list
bREVExport 					= False					#Enable or disable export of mesh.2010231143 from the export list (and tex.30)
bRE8Export 					= True					#Enable or disable export of mesh.2101050001 from the export list (and tex.30)
bMHRiseExport 				= False					#Enable or disable export of mesh.2008058288 from the export list (and tex.28) 
bMHRiseSunbreakExport 		= True					#Enable or disable export of mesh.2109148288 from the export list (and tex.28)

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
bShorterNames				= False					#Imports meshes named like "LOD_1_Main_1_Sub_1" instead of "LODGroup_1_MainMesh_1_SubMesh_1"
bImportMips 				= False					#Imports texture mip maps as separate images

#Export Options
bNewExportMenu				= False					#Show a custom Noesis window on mesh export
bAlwaysRewrite				= False					#Always try to rewrite the meshfile on export
bAlwaysWriteBones			= False					#Always write new skeleton to mesh
bNormalizeWeights 			= False					#Makes sure that the weights of every vertex add up to 1.0, giving the remainder to the bone with the least influence
bCalculateBoundingBoxes		= True					#Calculates the bounding box for each bone
BoundingBoxSize				= 0.01					#With bCalculateBoundingBoxes False, change the size of the bounding boxes created for each rigged bone when exporting with -bones or -rewrite
bRigToCoreBones				= False					#Assign non-matching bones to the hips and spine, when exporting a mesh without -bones or -rewrite

#Import/Export:
bAddBoneNumbers 			= 2						#Adds bone numbers and colons before bone names to indicate if they are active. 0 = Off, 1 = On, 2 = Auto
bRotateBonesUpright			= False					#Rotates bones to be upright for editing and then back to normal for exporting

from inc_noesis import *
import math
import os
import re
import copy
import noewin
from noewin import user32, gdi32, kernel32


#Default global variables for internal use:
sGameName = "RE2"
sExportExtension = ".1808312334"
bWriteBones = False
bReWrite = False
w1 = 127
w2 = -128

formats = {
	"RE2":			{ "modelExt": ".1808312334", "texExt": ".10",		 "mmtrExt": ".1808160001", "nDir": "x64", "mdfExt": ".mdf2.10" },
	"RE3": 			{ "modelExt": ".1902042334", "texExt": ".190820018", "mmtrExt": ".1905100741", "nDir": "stm", "mdfExt": ".mdf2.13" },
	"RE7":			{ "modelExt": ".32", 		 "texExt": ".8", 		 "mmtrExt": ".69", 		   "nDir": "x64", "mdfExt": ".mdf2.6"  },
	"RE8": 			{ "modelExt": ".2101050001", "texExt": ".30", 		 "mmtrExt": ".2102188797", "nDir": "stm", "mdfExt": ".mdf2.19" },
	"DMC5":			{ "modelExt": ".1808282334", "texExt": ".11", 		 "mmtrExt": ".1808168797", "nDir": "x64", "mdfExt": ".mdf2.10" },
	"MHRise":		{ "modelExt": ".2008058288", "texExt": ".28", 		 "mmtrExt": ".2109301553", "nDir": "stm", "mdfExt": ".mdf2.19" },
	"MHRSunbreak":	{ "modelExt": ".2109148288", "texExt": ".28", 		 "mmtrExt": ".220427553",  "nDir": "stm", "mdfExt": ".mdf2.23" },
	"REVerse":		{ "modelExt": ".2010231143", "texExt": ".30", 		 "mmtrExt": ".2011178797", "nDir": "stm", "mdfExt": ".mdf2.19" },
	"RERT": 		{ "modelExt": ".2109108288", "texExt": ".34", 		 "mmtrExt": ".2109101635", "nDir": "stm", "mdfExt": ".mdf2.21" },
	"RE7RT": 		{ "modelExt": ".220128762",  "texExt": ".35", 		 "mmtrExt": ".2109101635", "nDir": "stm", "mdfExt": ".mdf2.21" },
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

class openOptionsDialogWindow:
	
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
		self.indices = []
		
	def setWidthAndHeight(self, width=None, height=None):
		self.width = width or self.width
		self.height = height or self.height
		
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
	
	def inputMeshFileEditBox(self, noeWnd, controlId, wParam, lParam):
		self.meshEditText = self.meshFile.getText()
		self.meshFile.setText(self.meshEditText)
		if rapi.checkFileExists(self.meshEditText):
			self.filepath = self.meshEditText
			self.clearComboBoxList()
			self.sourceList = getSameExtFilesInDir(self.filepath)
			self.setComboBoxList(self.meshFileList, self.filepath)
	
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
		
	#660, 120
	def createMeshWindow(self, width=None, height=None):
		width = width or self.width
		height = height or self.height
		if self.create(width, height):
			self.noeWnd.createStatic("Export Over Mesh", 5, 5, 140, 20)
			#index = self.noeWnd.createEditBox(5, 25, width-20, 20, self.filepath, self.inputMeshFileEditBox)
			#self.meshFile = self.noeWnd.getControlByIndex(index)
			index = self.noeWnd.createComboBox(5, 50, width-20, 20, self.selectSourceListItem, noewin.CBS_DROPDOWNLIST)
			self.meshFileList = self.noeWnd.getControlByIndex(index)
			self.setComboBoxList(self.meshFileList, self.filepath)
			
			self.noeWnd.createButton("Browse", 5, 85, 80, 30, self.openBrowseMenu)
			if rapi.checkFileExists(self.filepath):
				self.noeWnd.createButton("Export", width-416, 85, 80, 30, self.openOptionsButtonExport)
				self.noeWnd.createButton("Export New Bones", width-326, 85, 130, 30, self.openOptionsButtonExportBones)
			self.noeWnd.createButton("Rewrite", width-186, 85, 80, 30, self.openOptionsButtonRewrite)
			self.noeWnd.createButton("Cancel", width-96, 85, 80, 30, self.openOptionsButtonCancel)
			self.noeWnd.doModal()
		else:
			print("Failed to create Noesis Window")
			self.failed = True
			
	#286, 120
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

def registerNoesisTypes():

	def addOptions(handle):
		noesis.setTypeExportOptions(handle, "-noanims -notex")
		noesis.addOption(handle, "-bones", "Write new skeleton on export", 0)
		noesis.addOption(handle, "-rewrite", "Rewrite submeshes and materials structure", 0)
		noesis.addOption(handle, "-flip", "Reverse handedness from DirectX to OpenGL", 0)
		noesis.addOption(handle, "-bonenumbers", "Add bone numbers to imported bones", 0)
		noesis.addOption(handle, "-meshfile", "Reverse handedness from DirectX to OpenGL", noesis.OPTFLAG_WANTARG)
		noesis.addOption(handle, "-b", "Run as a batch process", 0)
		return handle

	handle = noesis.register("RE Engine MESH [PC]", ".1902042334;.1808312334;.1808282334;.2008058288;.2010231143;.2101050001;.2109108288;.2109148288;.220128762;.32;.NewMesh")
	noesis.setHandlerTypeCheck(handle, meshCheckType)
	noesis.setHandlerLoadModel(handle, meshLoadModel)
	noesis.addOption(handle, "-noprompt", "Do not prompt for MDF file", 0)
	noesis.setTypeSharedModelFlags(handle, (noesis.NMSHAREDFL_WANTGLOBALARRAY))
	
	handle = noesis.register("RE Engine Texture [PC]", ".10;.190820018;.11;.8;.28;.stm;.30;.34;.35")
	noesis.setHandlerTypeCheck(handle, texCheckType)
	noesis.setHandlerLoadRGBA(handle, texLoadDDS)

	handle = noesis.register("RE Engine UVS [PC]", ".5;.7")
	noesis.setHandlerTypeCheck(handle, UVSCheckType)
	noesis.setHandlerLoadModel(handle, UVSLoadModel)

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
		handle = noesis.register("ReVerse MESH", (".2010231143"))
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
		'''handle = noesis.register("RE7 MESH", (".32"))
		noesis.setHandlerTypeCheck(handle, meshCheckType)
		noesis.setHandlerWriteModel(handle, meshWriteModel)
		addOptions(handle)'''
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
		
	noesis.logPopup()
	return 1

def meshCheckType(data):
	bs = NoeBitStream(data)
	magic = bs.readUInt()
	
	stream = os.popen('echo Returned output')
	output = stream.read()
	print(output)
	
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
	
def readTextureData(texData, mipWidth, mipHeight, format):
	
	if format == 29 or  format == 28:
		fmtName = ("r32g32b32a32")
		texData = rapi.imageDecodeRaw(texData, mipWidth, mipHeight, "r32g32b32a32", 1)
	elif format == 61:
		fmtName = ("r8")
		texData = rapi.imageDecodeRaw(texData, mipWidth, mipHeight, "r8")
	elif format == 10:
		fmtName = ("r16g16b16a16")
		texData = rapi.imageDecodeRaw(texData, mipWidth, mipHeight, "r16g16b16a16")
	elif format == 2:
		fmtName = ("r32g32b32a32")
		texData = rapi.imageDecodeRaw(texData, mipWidth, mipHeight, "r32g32b32a32", 1)
	#elif format == 28:
	#	print ("FOURCC_ATI1")
	#	texData = rapi.imageDecodeDXT(texData, mipWidth, mipHeight, noesis.FOURCC_ATI1)
	elif format == 71 or format == 72: #ATOS
		fmtName = ("FOURCC_DXT1")
		texData = rapi.imageDecodeDXT(texData, mipWidth, mipHeight, noesis.FOURCC_DXT1)
	elif format == 77: #BC3
		fmtName = ("FOURCC_BC3")
		texData = rapi.imageDecodeDXT(texData, mipWidth, mipHeight, noesis.FOURCC_BC3)
	elif format == 80: #BC4 wetmasks
		fmtName = ("FOURCC_BC4")
		texData = rapi.imageDecodeDXT(texData, mipWidth, mipHeight, noesis.FOURCC_BC4)
	elif format == 83: #BC5
		fmtName = ("FOURCC_BC5")
		texData = rapi.imageDecodeDXT(texData, mipWidth, mipHeight, noesis.FOURCC_BC5)
		texData = rapi.imageEncodeRaw(texData, mipWidth, mipHeight, "r16g16")
		texData = rapi.imageDecodeRaw(texData, mipWidth, mipHeight, "r16g16")
	elif format == 95 or format == 96:
		fmtName = ("FOURCC_BC6H")
		texData = rapi.imageDecodeDXT(texData, mipWidth, mipHeight, noesis.FOURCC_BC6H)
	elif format == 98 or format == 99:
		texData = rapi.imageDecodeDXT(texData, mipWidth, mipHeight, noesis.FOURCC_BC7)
		fmtName = ("FOURCC_BC7")
	else:
		print("Fatal Error: Unsupported texture type: " + str(format))
		return 0
	return texData, fmtName
	
def texLoadDDS(data, texList):
	bs = NoeBitStream(data)
	magic = bs.readUInt()
	version = bs.readUInt()
	width = bs.readUShort()
	height = bs.readUShort()
	unk00 = bs.readUShort()
	if version > 27 and version < 1000:
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
	
	if version > 27 and version < 1000:
		bs.seek(8,1)
	
	mipData = []
	for i in range(numImages):
		mipDataImg = []
		for j in range(mipCount):
			mipDataImg.append([bs.readUInt64(), bs.readUInt(), bs.readUInt()]) #[0]offset, [1]pitch, [2]size
		mipData.append(mipDataImg)
		#bs.seek((mipCount-1)*16, 1) #skip small mipmaps
		
	texFormat = noesis.NOESISTEX_RGBA32
	#print("numImages:", numImages)
	
	for i in range(numImages):
		mipWidth = width
		mipHeight = height
		for j in range(mipCount):
			try:
				bs.seek(mipData[i][j][0])
				#print(bs.tell())
				texData = bs.readBytes(mipData[i][j][2])
			except:
				if i > 0:
					numImages = i - 1
					print ("Multi-image load stopped early")
					break
				else:
					return 0
			#if bPrintMDF:
			#	print ("Image", i, ":  Reading", mipData[i][j][2], "bytes starting from", mipData[i][j][0])
			
			try:
				texData, fmtName = readTextureData(texData, mipWidth, mipHeight, format)
			except:
				print("Failed", mipWidth, mipHeight, format, texData)
				texData, fmtName = readTextureData(texData, mipWidth, mipHeight, format)
			if texData == 0:
				return 0
				
			#if isATOS:
			#	texData = rapi.imageEncodeRaw(texData, mipWidth, mipHeight, "r8r8r8r8")
			#	texData = rapi.imageDecodeRaw(texData, mipWidth, mipHeight, "r8g8b8a8")
			
			texList.append(NoeTexture(rapi.getInputName(), int(mipWidth), int(mipHeight), texData, texFormat))
			
			if not bImportMips:
				break
			if mipWidth > 4: 
				mipWidth = int(mipWidth / 2)
			if mipHeight > 4: 
				mipHeight = int(mipHeight / 2)
		
		#if bPrintMDF:
		#print(fmtName, "(", format, ")")
	return 1

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

class texFile:
	
	def __init__(self, data, width, height, inFile=None, outFile=None):
		self.data = data
		self.width = width
		self.height = height
		self.slices = 1
		self.ddsFmt = noesis.NOE_ENCODEDXT_BC7
		self.inFile = inFile
		self.outFile = outFile
		
		if inFile and not outFile:
			self.version = int(os.path.splitext(inFile)[1][1:])
			byteArray = rapi.loadIntoByteArray(inFile)
			if byteArray:
				self.bs = self.readTexFile(NoeBitStream(byteArray))
		else:
			outFile = outFile or rapi.getOutputName()
			if inFile:
				#print(inFile)
				byteArray = rapi.loadIntoByteArray(inFile)
				if byteArray:
					self.source_tex = self.readTexFile(NoeBitStream(byteArray))
			self.numImages = 1
			self.version = int(os.path.splitext(outFile)[1][1:])
			filepath = outFile
			filename = rapi.getExtensionlessName(filepath)
			self.abbreviation = filename.split('_')[-1]
			self.abbreviation = self.abbreviation.split('.')[0]
			self.dictData = extToFormat[str(self.version)][self.abbreviation] if str(self.version) in extToFormat and self.abbreviation in extToFormat[str(self.version)] else []
			
			#print (filename.split('.'), filename.split('.')[-1])
			#print(self.dictData)
			if not self.dictData and not self.inFile:
				self.error = True
				return
			elif self.dictData:
				self.format = self.dictData[0]
				self.unkByte = self.dictData[1]
				self.ddsFmt = getNoesisDDSType(self.format)
				self.outputFileName = filepath.replace(filename, filename + "." + str(self.format))
		self.newFmtBytes = ((self.version > 27 and self.version < 1000) and 8) or 0
		
	def readTexFile(self, bs):
		#print("reading infile")
		bs.seek(0)
		self.magic = bs.readUInt()
		self.version = bs.readUInt()
		self.width = bs.readUShort()
		self.height = bs.readUShort()
		self.unk00 = bs.readUShort()
		if self.version > 27 and self.version < 1000:
			self.numImages = bs.readUByte()
			self.oneImgMipHdrSize = bs.readUByte()
			self.mipCount = int(self.oneImgMipHdrSize / 16)
		else:
			self.mipCount = bs.readUByte()
			self.numImages = bs.readUByte()
		self.format = bs.readUInt()
		#print("format is", self.format)
		self.ddsFmt = getNoesisDDSType(self.format)
		self.unk02 = bs.readUInt()
		self.unk03 = bs.readUInt()
		self.streamingTexture = bs.readByte()
		self.unkByte = bs.readByte()
		self.unkByte1 = bs.readByte()
		self.unkByte2 = bs.readByte()
		self.newFmtBytes = ((self.version > 27 and self.version < 1000) and 8) or 0
		if self.newFmtBytes > 0:
			bs.readUInt64()
		self.dictData = [self.format, self.unkByte]
		imgDataOffset = readUIntAt(bs, bs.tell())
		pitch = readUIntAt(bs, bs.tell()+8)
		size = readUIntAt(bs, bs.tell()+12)
		self.mipData = []
		for i in range(self.mipCount):
			self.mipData.append(bs.readUInt64())
			self.mipData.append(bs.readUInt64())
		
		bs.seek(imgDataOffset)
		
		if not self.outFile: #import only, load into preview scene
			self.imageData = bs.readBytes(size)
			self.imageData, self.fmtName = readTextureData(self.imageData, self.width, self.height, self.format)
		else:
			self.imageData = bs.readBytes(bs.getSize() - bs.tell())
		
		return bs
		
	def writeTexHeader(self, bs):
		
		#print("New format: ", extToFormat[str(self.version)][self.abbreviation])
		bs = bs or NoeBitStream() #self.bs
		bs.seek(0)
		bs.writeUInt(5784916) #TEX
		bs.writeUInt(self.version)
		bs.writeUShort(self.width)
		bs.writeUShort(self.height)
		bs.writeUByte(self.slices) #slices
		bs.writeUByte(0) #unknown0
		mipHeaderSz = 0
		if self.mipData:
			mipHeaderSz = int(len(self.mipData) * 8)
		#print("mipHeaderSz", mipHeaderSz)
		if self.newFmtBytes > 0:
			bs.writeUByte(self.numImages) #numImages
			bs.writeUByte(mipHeaderSz) #mipHeaderSz
		else:
			bs.writeUByte(len(self.mipData)) #old-version mipCount
			bs.writeUByte(self.numImages) #numImages
			
		bs.writeUInt(int(self.format)) #tex format
		bs.writeUInt(-1) #unknown
		bs.writeUInt(0)  #unknown
		bs.writeUByte(128) #streamingtexture
		bs.writeUByte(self.unkByte or 0) #unknown
		bs.writeUByte(0) #unknown
		bs.writeUByte(0) #unknown
		if self.newFmtBytes > 0:
			bs.writeUInt64(0)
		#print(self.mipData)
		if self.imageData:
			for i, mipData in enumerate(self.mipData):
				#print(bs.tell(), mipData)
				if i % 2 == 0:
					bs.writeUInt64(mipData + self.newFmtBytes)
				else:
					bs.writeUInt64(mipData)
		return bs
			
	def readTexImageData(self):
		return 1
		
	def writeTexImageData(self, bs, exportCycles):
		
		exportCycles = exportCycles or self.numImages
		mipWidth = self.width
		mipHeight = self.height
		numMips = 0
		output_mips = 0
		dataSize = 0
		totalData = 0
		sizeArray = []
		fileData = []
		
		bs.seek(32 + self.newFmtBytes)
		
		
		if self.imageData: 
			#write image data from source file:
			bs.seek(bs.getSize())
			#print(bs.tell(), self.newFmtBytes)
			bs.writeBytes(self.imageData)	
		else:
			#write mipmap headers & encode image
			while mipWidth > 4 or mipHeight > 4:
				
				if self.ddsFmt == "r8" and numMips > 1:
					break
					
				numMips += 1
				output_mips += 1
				
				mipData = rapi.imageResample(self.data, self.width, self.height, mipWidth, mipHeight)
				try:
					dxtData = rapi.imageEncodeDXT(mipData, 4, mipWidth, mipHeight, self.ddsFmt)
				except:
					dxtData = rapi.imageEncodeRaw(mipData, mipWidth, mipHeight, self.ddsFmt)
					
				mipSize = len(dxtData)
				fileData.append(dxtData)
					
				sizeArray.append(dataSize)
				dataSize += mipSize
				
				pitch = mipWidth
				if self.ddsFmt == noesis.NOE_ENCODEDXT_BC1:
					pitch *= 2
				elif self.ddsFmt != "r8":
					pitch *= 4
					
				bs.writeUInt64(0)
				bs.writeUInt(pitch)
				bs.writeUInt(mipSize)
				
				print ("Mip", numMips, ": ", mipWidth, "x", mipHeight, "\n            ", pitch, "\n            ", mipSize)
				if mipWidth > 4: mipWidth = int(mipWidth / 2)
				if mipHeight > 4: mipHeight = int(mipHeight / 2)
					
			for d in range(len(fileData)): #write image data
				bs.writeBytes(fileData[d])
			
			#adjust header
			bs.seek(28)
			if self.newFmtBytes > 0:
				bs.writeUByte(128) #ReVerse streaming
			else: 
				bs.writeUByte(0) #streaming texture
				
			bs.seek(8)
			bs.writeUShort(self.width)
			bs.writeUShort(self.height)
			if self.newFmtBytes > 0:
				bs.seek(15)
				bs.writeUByte(numMips * 16)
			else:
				bs.seek(14)
				bs.writeUByte(numMips)
			
			bsHeaderSize = output_mips * 16 + 32 + self.newFmtBytes
			bs.seek(32 + self.newFmtBytes)
			
			for mip in range(numMips):
				bs.writeUInt64(sizeArray[mip] + bsHeaderSize)
				bs.seek(8, 1)
		return 1

def findSourceTexFile(version_no, outputName=None):
	newTexName = outputName or rapi.getOutputName().lower()
	while newTexName.find("out.") != -1: 
		newTexName = newTexName.replace("out.",".")
	newTexName =  newTexName.replace(".dds","").replace(".tex","").replace(".10","").replace(".190820018","").replace(".11","").replace(".8","").replace(".28","").replace(".34","").replace(".35","").replace(".30","").replace(".jpg","").replace(".png","").replace(".tga","").replace(".gif","")
	ext = ".tex." + str(version_no)
	if not rapi.checkFileExists(newTexName + ext):
		for other_ext, subDict in extToFormat.items():
			if rapi.checkFileExists(newTexName + ".tex." + other_ext):
				ext = ".tex." + other_ext
	return newTexName + ext, ext

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
	
	f.seek(14)
	if version  > 27 and version < 1000:
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
		ogVersion = og.readUInt()
		if ((ogVersion > 27 and ogVersion < 1000) and int(os.path.splitext(rapi.getOutputName())[1][1:]) < 27) or ((ogVersion < 27 and int(os.path.splitext(rapi.getOutputName())[1][1:]) > 27) and int(os.path.splitext(rapi.getOutputName())[1][1:])  < 1000):
			print("\nWARNING: Source tex version does not match your output tex version\n	Selected Output:      tex" + str(os.path.splitext(rapi.getOutputName())[1]), "\n	Source Tex version: tex." + str(ogVersion) + "\n")
		og.seek(8)
		ogWidth = og.readUShort()
		ogHeight = og.readUShort()
		if ogWidth != width or ogHeight != height: 
			print ("Input TEX file uses a different resolution from Source TEX file.\nEncoding image...")
			bDoEncode = True
		og.seek(14)
		
		ogHeaderSize = og.readUByte() * 16 + 32
		if ogVersion  > 27 and ogVersion < 1000: 
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
			if version  > 27 and version < 1000:
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
		
def GetRootGameDir():
	path = rapi.getDirForFilePath(rapi.getInputName())
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

#murmur3 hash algorithm
#Credit to Darkness for adapting this
def hash(key, seed=0xffffffff):
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
    if unsigned_val & 0x80000000 == 0:
        return unsigned_val
    else:
        return -((unsigned_val ^ 0xFFFFFFFF) + 1)

def hash_wide(key, seed=0xffffffff):
    key_temp = ''
    for char in key:
        key_temp += char + '\x00'
    return hash(key_temp, seed)
	
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
			sGameName = "REVerse"
			ext = ".30"

		texFile = LoadExtractedDir() + FileName + ext
		#print ("texFile:", texFile)
		if rapi.checkFileExists(texFile):
			return texFile, ext
			
	return 0, 0
	
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
				
				if texLoadDDS(textureData, uvsTexList) == 1:
					aspectRatios[len(aspectRatios)-1] = (uvsTexList[len(uvsTexList)-1].width / uvsTexList[len(uvsTexList)-1].height, 1)
					#print ("found", texFile)
					matName = rapi.getExtensionlessName(rapi.getExtensionlessName(rapi.getLocalFileName(texFile)))
					uvsTexList[len(uvsTexList)-1].name = matName
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
	
class meshFile(object): 

	def __init__(self, data):
		self.inFile = NoeBitStream(data)
		self.boneList = []
		self.matNames = []
		self.matHashes = []
		self.matList = []
		self.texList = []
		self.texNames = []
		self.missingTexNames = []
		self.texColors = []
		
	'''MDF IMPORT ========================================================================================================================================================================'''
	def createMaterials(self, matCount):
		global bColorize, bPrintMDF, sGameName, sExportExtension
		doColorize = bColorize
		doPrintMDF = bPrintMDF
		noMDFFound = 0
		skipPrompt = 0
		
		tempGameName = "RE7RT" 		 if sGameName == "RERT" and rapi.getOutputName().find("220128762") else sGameName
		tempGameName = "MHRSunbreak" if sGameName == "RERT" and rapi.getOutputName().find("2109148288") else sGameName
		
		#tempGameName = sGameName
		modelExt = formats[tempGameName]["modelExt"]
		texExt = formats[tempGameName]["texExt"]
		mmtrExt = formats[tempGameName]["mmtrExt"]
		nDir = formats[tempGameName]["nDir"]
		mdfExt = formats[tempGameName]["mdfExt"]
		
		print ("\n							", tempGameName, "\n")
		sExportExtension = modelExt
		
		extractedNativesPath = LoadExtractedDir(tempGameName)
		
		#Try to find & save extracted game dir for later if extracted game dir is unknown
		if extractedNativesPath == "":
			dirName = GetRootGameDir()
			if (dirName.endswith("chunk_000\\natives\\" + nDir + "\\")):
				print ("Saving extracted natives path...")
				if SaveExtractedDir(dirName, tempGameName):
					extractedNativesPath = dirName
					
		if extractedNativesPath != "":
			print ("Using this extracted natives path:", extractedNativesPath + "\n")
			
		#Try to guess MDF filename
		inputName = rapi.getInputName()
		if inputName.find(".noesis") != -1:
			inputName = rapi.getLastCheckedName()
			skipPrompt = 2
			doPrintMDF = 0
			
		pathPrefix = inputName
		while pathPrefix.find("out.") != -1: pathPrefix = pathPrefix.replace("out.",".")
		pathPrefix = pathPrefix.replace(".mesh", "").replace(modelExt,"").replace(".NEW", "")
		
		if sGameName == "REVerse" and os.path.isdir(os.path.dirname(inputName) + "\\Material"):
			pathPrefix = (os.path.dirname(inputName) + "\\Material\\" + rapi.getLocalFileName(inputName).replace("SK_", "M_")).replace(".NEW", "")
			while pathPrefix.find("out.") != -1: pathPrefix = pathPrefix.replace("out.",".")
			pathPrefix = pathPrefix.replace(".mesh" + modelExt,"")
			if not rapi.checkFileExists(pathPrefix + mdfExt):
				pathPrefix = pathPrefix.replace("00_", "")
			if not rapi.checkFileExists(pathPrefix + mdfExt):
				for item in os.listdir(os.path.dirname(pathPrefix + mdfExt)):
					if mdfExt == (".mdf2" + os.path.splitext(os.path.join(os.path.dirname(pathPrefix), item))[1]):
						pathPrefix = os.path.join(os.path.dirname(pathPrefix), item).replace(mdfExt, "")
						break
			print (pathPrefix + mdfExt) 
			
		similarityCounter = 0
		ogFileName = rapi.getLocalFileName(inputName)
		if not rapi.checkFileExists(pathPrefix + mdfExt):
			for item in os.listdir(os.path.dirname(pathPrefix + mdfExt)):
				if mdfExt == (".mdf2" + os.path.splitext(os.path.join(os.path.dirname(pathPrefix), item))[1]):
					test = rapi.getLocalFileName(os.path.join(os.path.dirname(pathPrefix), item).replace(mdfExt, ""))
					sameCharCntr = 0
					for c, char in enumerate(test):
						if c < len(ogFileName) and char == ogFileName[c]:
							sameCharCntr += 1
					if sameCharCntr > similarityCounter:
						pathPrefix = os.path.join(os.path.dirname(pathPrefix), item).replace(mdfExt, "")
						similarityCounter = sameCharCntr
		
		materialFileName = (pathPrefix + mdfExt)
		
		if not (rapi.checkFileExists(materialFileName)):
			materialFileName = (pathPrefix + "_mat" + mdfExt)
		if not (rapi.checkFileExists(materialFileName)):
			materialFileName = (pathPrefix + "_00" + mdfExt)
		if not (rapi.checkFileExists(materialFileName)):
			if sGameName == "RERT" or sGameName == "RE3" or sGameName == "REVerse" or sGameName == "RE8" or sGameName == "MHRise":
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
				
			if msgName.endswith(" -c"):
				print (msgName)
				doColorize = 1
				doPrintMDF = 0												
				msgName = msgName.replace(" -c", "")												
			
			if ((rapi.checkFileExists(msgName)) and (msgName.endswith(mdfExt))):
				materialFileName = msgName
			else:
				noMDFFound = 1
		
		if (bPopupDebug == 1):
			noesis.logPopup()
		
		#Save a manually entered natives directory path name for later
		if (msgName.endswith("\\natives\\" + nDir + "\\")) and (os.path.isdir(msgName)):
			print ("Attempting to write: ")
			if SaveExtractedDir(msgName, tempGameName):
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
		
		if matCountMDF != matCount:
			print ("MDF Checkerboard Error: MDF does not have the same material count as the MESH file!\n	MESH materials:", matCount, "\n	MDF Materials:", matCountMDF)
			return 0
		
		#Parse Materials
		for i in range(matCountMDF):
			
			if sGameName == "RE7":
				bs.seek(0x10 + (i * 72))
			elif sGameName == "RERT" or sGameName == "REVerse" or sGameName == "RE8" or sGameName == "MHRise":
				bs.seek(0x10 + (i * 80))
			else:
				bs.seek(0x10 + (i * 64))

			materialNamesOffset = bs.readUInt64()
			materialHash = bs.readInt()
			if sGameName == "RE7":
				bs.seek(8,1)
			sizeOfFloatStr = bs.readUInt()
			floatCount = bs.readUInt()
			texCount = bs.readUInt()
			bs.seek(8,1)
			if sGameName == "REVerse" or sGameName == "RERT" or sGameName == "RE8" or sGameName == "MHRise":
				bs.seek(8,1)
			floatHdrOffs = bs.readUInt64()
			texHdrOffs = bs.readUInt64()
			if sGameName == "REVerse" or sGameName == "RERT" or sGameName == "RE8" or sGameName == "MHRise":
				firstMtrlNameOffs = bs.readUInt64()
			floatStartOffs = bs.readUInt64()
			mmtr_PathOffs = bs.readUInt64()
			bs.seek(materialNamesOffset)
			materialName = ReadUnicodeString(bs)
			bs.seek(mmtr_PathOffs)
			mmtrName = ReadUnicodeString(bs)
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
			material.setAlphaTest(0)
		
			#Parse Textures
			textureInfo = []
			paramInfo = []
			
			bFoundBM = False
			bFoundNM = False
			bFoundHM = False
			bFoundBT = False
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
				if sGameName == "RERT" or sGameName == "RE3" or sGameName == "REVerse" or sGameName == "RE8" or sGameName == "MHRise" :
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
				texSpecColour.append(NoeVec4((1.0, 1.0, 1.0, 0.8)))
			if not bFoundAmbiColour:
				texAmbiColour.append(NoeVec4((1.0, 1.0, 1.0, 1.0)))
			if not bFoundMetallicColour:
				texMetallicColour.append(1.0)
			if not bFoundFresnelColour:
				texFresnelColour.append(0.8)
			
			if doPrintMDF:
				print ("\nTextures for " + materialName + "[" + str(i) + "]" + ":")
			
			for j in range(texCount): # texture headers
				
				if sGameName == "RERT" or sGameName == "RE3" or sGameName == "REVerse" or sGameName == "RE8" or sGameName == "MHRise" :
					bs.seek(texHdrOffs + (j * 0x20))
					textureInfo.append([bs.readUInt64(), bs.readUInt64(), bs.readUInt64(), bs.readUInt64()]) #TextureTypeOffset[0], uknBytes[1], TexturePathOffset[2], padding[3]
				else:
					bs.seek(texHdrOffs + (j * 0x18))
					textureInfo.append([bs.readUInt64(), bs.readUInt64(), bs.readUInt64()])
				bs.seek(textureInfo[j][0])
				textureType = ReadUnicodeString(bs)
				bs.seek(textureInfo[j][2])
				textureName = ReadUnicodeString(bs).replace("@", "")
				
				textureFilePath = ""
				textureFilePath2 = ""
				#if rapi.getInputName().find("natives".lower()) == -1:
				#	self.texNames.append((textureName + texExt).lower())
				#	
				if (rapi.checkFileExists(self.rootDir + "streaming/" + textureName + texExt)):
					textureFilePath = self.rootDir + "streaming/" + textureName + texExt						
					textureFilePath2 = rapi.getLocalFileName(self.rootDir + "streaming/" + textureName).rsplit('.', 1)[0] + ".dds"
							
				elif (rapi.checkFileExists(self.rootDir + textureName + texExt)):
					textureFilePath = self.rootDir + textureName + texExt
					textureFilePath2 = rapi.getLocalFileName(self.rootDir + textureName).rsplit('.', 1)[0] + ".dds"
					if bPrintFileList and not (rapi.checkFileExists(self.rootDir + textureName + texExt)):
						self.missingTexNames.append("DOES NOT EXIST: " + (('natives/' + (re.sub(r'.*natives\\', '', textureFilePath)).lower()).replace("\\","/")).replace(extractedNativesPath,''))
					
				elif (rapi.checkFileExists(extractedNativesPath + "streaming/" + textureName + texExt)):
					textureFilePath = extractedNativesPath + "streaming/" + textureName + texExt
					textureFilePath2 = rapi.getLocalFileName(extractedNativesPath + "streaming/" + textureName).rsplit('.', 1)[0] + ".dds"
							
				elif (rapi.checkFileExists(extractedNativesPath + textureName + texExt)):
					textureFilePath = extractedNativesPath + textureName + texExt
					textureFilePath2 = rapi.getLocalFileName(extractedNativesPath + textureName).rsplit('.', 1)[0] + ".dds"
					if bPrintFileList and not (rapi.checkFileExists(extractedNativesPath + textureName + texExt)):
						self.missingTexNames.append("DOES NOT EXIST: " + ('natives/' + (re.sub(r'.*natives\\', '', textureFilePath)).lower()).replace("\\","/").replace(extractedNativesPath,''))
					
				else:
					textureFilePath = self.rootDir + textureName + texExt
					textureFilePath2 = rapi.getLocalFileName(self.rootDir + textureName).rsplit('.', 1)[0] + ".dds"
					if bPrintFileList and not (textureFilePath.endswith("rtex" + texExt)):
						self.missingTexNames.append("DOES NOT EXIST: " + ('natives/' + (re.sub(r'.*natives\\', '', textureFilePath)).lower()).replace("\\","/").replace("streaming/",""))
				
				bAlreadyLoadedTexture = False
				
				for k in range(len(self.texList)):
					if self.texList[k].name == textureFilePath2:
						bAlreadyLoadedTexture = True
						
				if bPrintFileList: #and rapi.getInputName().find("natives".lower()) != -1:
					if not (textureName.endswith("rtex")):
						newTexPath = ((('natives/' + (re.sub(r'.*natives\\', '', textureFilePath))).replace("\\","/")).replace(extractedNativesPath,'')).lower()
						self.texNames.append(newTexPath)
						if newTexPath.find('streaming') != -1:
							testPath = newTexPath.replace('natives/' + nDir + '/streaming/', '')
							if rapi.checkFileExists(self.rootDir + testPath) or rapi.checkFileExists(extractedNativesPath + testPath):
								self.texNames.append(newTexPath.replace('streaming/',''))
								
				if doColorize:
					colors = [(0.0, 0.0, 0.0, 1.0), 	(1.0, 1.0, 1.0, 1.0), 	  (1.0, 0.0, 0.0, 1.0),	  	(0.0, 1.0, 0.0, 1.0), 		(0.0, 0.0, 1.0, 1.0), 	 (1.0, 1.0, 0.0, 1.0), 		(0.0, 1.0, 1.0, 1.0),\
							  (1.0, 0.0, 1.0, 1.0), 	(0.75, 0.75, 0.75, 1.0),  (0.5, 0.5, 0.5, 1.0),	  	(0.5, 0.0, 0.0, 1.0), 		(0.5, 0.5, 0.0, 1.0), 	 (0.0, 0.5, 0.0, 1.0), 		(0.5, 0.0, 0.5, 1.0),\
							  (0.0, 0.5, 0.5, 1.0), 	(0.0, 0.0, 0.5, 1.0), 	  (0.82, 0.7, 0.53, 1.0), 	(0.294, 0.0, 0.51, 1.0), 	(0.53, 0.8, 0.92, 1.0),  (0.25, 0.88, 0.815, 1.0),  (0.18, 0.545, 0.34, 1.0),\
							  (0.68, 1.0, 0.18, 1.0), 	(0.98, 0.5, 0.45, 1.0),   (1.0, 0.41, 0.7, 1.0),  	(0.0, 0.0, 0.0, 1.0), 		(1.0, 1.0, 1.0, 1.0), 	 (1.0, 0.0, 0.0, 1.0), 		(0.0, 1.0, 0.0, 1.0),\
							  (0.0, 0.0, 1.0, 1.0), 	(1.0, 1.0, 0.0, 1.0), 	  (0.0, 1.0, 1.0, 1.0),	  	(1.0, 0.0, 1.0, 1.0), 	 	(0.75, 0.75, 0.75, 1.0), (0.5, 0.5, 0.5, 1.0), 	 	(0.5, 0.0, 0.0, 1.0),\
							  (0.5, 0.5, 0.0, 1.0), 	(0.0, 0.5, 0.0, 1.0),	  (0.5, 0.0, 0.5, 1.0),	  	(0.0, 0.5, 0.5, 1.0), 		(0.0, 0.0, 0.5, 1.0), 	 (0.82, 0.7, 0.53, 1.0), 	(0.294, 0.0, 0.51, 1.0),\
							  (0.53, 0.8, 0.92, 1.0), 	(0.25, 0.88, 0.815, 1.0), (0.18, 0.545, 0.34, 1.0), (0.68, 1.0, 0.18, 1.0), 	(0.98, 0.5, 0.45, 1.0),  (1.0, 0.41, 0.7, 1.0)]
					colorNames = ['Black', 'White', 'Red', 'Lime', 'Blue', 'Yellow', 'Cyan', 'Magenta', 'Silver', 'Gray', 'Maroon', 'Olive', 'Green', 'Purple', 'Teal', 'Navy', 'Tan', 'Indigo', 'Sky Blue', 'Turquoise',\
					'Sea Green', 'Green Yellow', 'Salmon', 'Hot Pink', 'Black', 'White', 'Red', 'Lime', 'Blue', 'Yellow', 'Cyan', 'Magenta', 'Silver', 'Gray', 'Maroon', 'Olive', 'Green', 'Purple', 'Teal', 'Navy', 'Tan',\
					'Indigo', 'Sky Blue', 'Turquoise', 'Sea Green', 'Green Yellow', 'Salmon', 'Hot Pink']					
					
					material.setDiffuseColor(colors[i])
					if i < 10:
						myIndex = "0" + str(i)
					else:
						myIndex = str(i)
					self.texColors.append(myIndex + ": Material[" + str(i) + "] -- " + materialName + " is colored " + colorNames[i])
				else:
					if not bAlreadyLoadedTexture:
						if (textureName.endswith("rtex")):
							pass
						elif not (rapi.checkFileExists(textureFilePath)):
							if textureFilePath != "": 
								print("Error: Texture at path: " + str(textureFilePath) + " does not exist!")
						else:
							textureData = rapi.loadIntoByteArray(textureFilePath)
							#isATOS = "atos" in textureFilePath.lower()
							if texLoadDDS(textureData, self.texList) == True:
								self.texList[len(self.texList)-1].name = textureFilePath2
							else:
								print ("Failed to load", textureFilePath2)
								
					if textureType == "BaseMetalMap" or textureType == "BaseShiftMap" or "Base" in textureType and not bFoundBM:
						bFoundBM = True
						material.setTexture(textureFilePath2)
						material.setDiffuseColor(texBaseColour[i][0])
						material.setSpecularTexture(textureFilePath2)
						materialFlags |= noesis.NMATFLAG_PBR_SPEC #Not really :(
						material.setSpecularSwizzle( NoeMat44([[1, 1, 1, 0], [0, 0, 0, 1], [0, 0, 0, 0], [0, 0, 0, 0]]) )
						if "alba" in textureFilePath2.lower():
							material.setAlphaTest(0.05)
					elif textureType == "NormalRoughnessMap" and not bFoundNM:
						bFoundNM = True
						material.setNormalTexture(textureFilePath2)
						materialFlags |= noesis.NMATFLAG_PBR_ROUGHNESS_NRMALPHA
					elif textureType == "AlphaTranslucentOcclusionSSSMap" and not bFoundSSSM:
						bFoundSSSM = True
						material.setOpacityTexture(textureFilePath2)
						#material.setNextPass(textureFilePath2)
						material.setOcclTexture(textureFilePath2) 
						#matArray.append(textureFilePath2)
						try:
							#material.setBlendMode("GL_SRC1_ALPHA") 
							materialFlags2 |= noesis.NMATFLAG2_OPACITY_UV2 | noesis.NMATFLAG2_OCCL_UV1 | noesis.NMATFLAG2_OCCL_BLUE
						except:
							print ("Please update Noesis to fix MDF occlusion map preview")
							
					elif textureType == "Heat_Mask" and not bFoundHM:
						bFoundHM = True
					elif textureType == "BloodTexture" and not bFoundBT:
						bFoundBT = True
					
					if bFoundSpecColour:
						material.setSpecularColor(texSpecColour[i][0])
					if bFoundAmbiColour:
						material.setAmbientColor(texAmbiColour[i][0])
					if bFoundMetallicColour:
						material.setMetal(texMetallicColour[i][0], 0.25)
					if bFoundRoughColour:
						material.setRoughness(texRoughColour[i][0], 0.25)
					if bFoundFresnelColour:
						material.setEnvColor(NoeVec4((1.0, 1.0, 1.0, texFresnelColour[i][0])))
						
					if doPrintMDF:
						print(textureType + ":\n    " + textureName)
						
			material.setFlags(materialFlags)
			material.setFlags2(materialFlags2)
			self.matList.append(material)
			
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
		#print (self.texList)
		#print (self.texNames)
		return True
		
	'''MESH IMPORT ========================================================================================================================================================================'''
	def loadMeshFile(self, mdlList):
		
		global sGameName, bSkinningEnabled
		bs = self.inFile
		magic = bs.readUInt()
		meshVersion = bs.readUInt()
		fileSize = bs.readUInt()
		deferredWarning = ""
		bDoSkin = True
		
		sGameName = "RE2"
		sInputName = rapi.getInputName()
		if meshVersion == 21041600 or sInputName.find(".2109108288") != -1 or sInputName.find(".220128762") != -1: #RE2RT + RE3RT, and RE7RT
			sGameName = "RERT"
		elif sInputName.find(".1808282334") != -1:
			sGameName = "DMC5"
		elif sInputName.find(".1902042334") != -1:  #386270720
			sGameName = "RE3"
		elif sInputName.find(".2010231143") != -1:
			sGameName = "REVerse"
		elif meshVersion == 2020091500 or sInputName.find(".2101050001") != -1:
			sGameName = "RE8"
		elif (meshVersion == 2007158797 or sInputName.find(".2008058288") != -1): #Vanilla MHRise
			sGameName = "MHRise"
		elif (meshVersion == 21061800 or sInputName.find(".2109148288") != -1):  #MHRise Sunbreak version
			sGameName = "RERT"
			#sGameName = "MHRise"
		elif meshVersion == 352921600 or sInputName.find(".32") != -1:
			sGameName = "RE7"
		
		if sGameName != "RE7":
			unk02 = bs.readUInt()
		unk03 = bs.readUShort()
		numNodes = bs.readUShort()
		if sGameName != "RE7":
			unk04 = bs.readUInt()			
		LOD1Offs = bs.readUInt64()
		LOD2Offs = bs.readUInt64()
		occluderMeshOffs = bs.readUInt64()
		bonesOffs = bs.readUInt64()
		if sGameName != "RE7":
			topologyOffs = bs.readUInt64()
			
		bShapesHdrOffs = bs.readUInt64()
		floatsHdrOffs = bs.readUInt64()
		vBuffHdrOffs = bs.readUInt64()
		ukn3 = bs.readUInt64()
		nodesIndicesOffs = bs.readUInt64()
		boneIndicesOffs = bs.readUInt64()
		bshapesIndicesOffs = bs.readUInt64()
		namesOffs = bs.readUInt64()
		
		if LOD1Offs:
			bs.seek(LOD1Offs)
			countArray = bs.read("16B") #[0] = LODGroupCount, [1] = MaterialCount, [2] = UVChannelCount
			matCount = countArray[1]
			self.rootDir = GetRootGameDir()
			bLoadedMats = False
			if not (noesis.optWasInvoked("-noprompt")) and not rapi.noesisIsExporting() and not bRenameMeshesToFilenames:
				bLoadedMats = self.createMaterials(matCount);
			if bDebugMESH:
				print("Count Array")
				print(countArray)
		
		bs.seek(vBuffHdrOffs)
		if sGameName == "RE7":
			vertBuffSize = bs.readUInt()
			bs.seek(12,1)
			faceBuffSize = bs.readUInt()
			bs.seek(20,1)
			faceBuffOffs = bs.readUInt()
			bytesPerVert = 24 if bonesOffs == 0 else 40
			addBytes = 0
			if countArray[2] > 1: 
				addBytes = 4
				bytesPerVert += addBytes
			while bs.tell() % 16 != 0:
				bs.seek(1,1)
		else:
			vertElemHdrOffs = bs.readUInt64()
			vertBuffOffs = bs.readUInt64()
			faceBuffOffs = bs.readUInt64()
			if sGameName == "RERT":
				uknIntA = bs.readUInt()
				uknIntB = bs.readUInt()
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
		vertexBuffer = bs.readBytes(vertBuffSize)
		submeshDataArr = []
		
		if LOD1Offs:			
			bs.seek(LOD1Offs + 48 + 16) #unknown floats and bounding box
			#print(bs.tell())
			if sGameName != "RERT" and sGameName != "REVerse" and sGameName != "RE8" and sGameName != "MHRise":
				bs.seek(bs.readUInt64())
				
			#if numNodes == 0:
			#	print("Unsupported model type")
			#	return
			
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
				
			#Skeleton
			if bonesOffs:
				bs.seek(bonesOffs)
				boneCount = bs.readUInt()
				
				if sGameName == "RE7":
					bs.seek(floatsHdrOffs)
					boneMapCount = bs.readUInt()
					bs.seek(LOD1Offs+72)
					RE7SkinBoneMapOffs = bs.readUInt64()+16
				else:
					boneMapCount = bs.readUInt()
					
				bAddNumbers = False
				if bAddBoneNumbers == 1 or noesis.optWasInvoked("-bonenumbers"):
					bAddNumbers = True
				elif bAddBoneNumbers == 2 and boneCount > 256:
					bAddNumbers = True
					print ("Model has more than 256 bones, auto-enabling bone numbers...")
					
				bs.seek(bonesOffs + 16)
				
				if boneCount:
					hierarchyOffs = bs.readUInt64()
					localOffs = bs.readUInt64()
					globalOffs = bs.readUInt64()
					inverseGlobalOffs = bs.readUInt64()
					
					if sGameName == "RE7":
						bs.seek(RE7SkinBoneMapOffs)
						
					boneRemapTable = []
					if boneMapCount:
						for i in range(boneMapCount):
							boneRemapTable.append(bs.readShort())
					else:
						deferredWarning = "WARNING: Mesh has weights but no bone map"
						print ("WARNING: Mesh has weights but no bone map")
						boneRemapTable.append(0)
						
					if bDebugMESH:
						print("boneRemapTable:", boneRemapTable)

					boneParentInfo = []
					bs.seek(hierarchyOffs)
					for i in range(boneCount):
						boneParentInfo.append([bs.readShort(), bs.readShort(), bs.readShort(), bs.readShort(), bs.readShort(), bs.readShort(), bs.readShort(), bs.readShort()])
					
					trans = NoeVec3((100.0, 100.0, 100.0))
					bs.seek(localOffs)
					for i in range(boneCount):
						mat = NoeMat44.fromBytes(bs.readBytes(0x40)).toMat43()
						mat[3] *= trans
						boneName = names[countArray[1] + i]
						if bAddNumbers: 
							for j in range(len(boneRemapTable)):
								if boneParentInfo[i][0] == boneRemapTable[j]:
									if j<9:
										boneName = "b00" + str(j+1) + ":" + boneName
									elif j>8 and j<99:
										boneName = "b0" + str(j+1) + ":" + boneName
									elif j>98 and j<999:
										boneName = "b" + str(j+1) + ":" + boneName	
									break
						self.boneList.append(NoeBone(boneParentInfo[i][0], boneName, mat, None, boneParentInfo[i][1]))
						
					self.boneList = rapi.multiplyBones(self.boneList)
					
					if bRotateBonesUpright:
						rot_mat = NoeMat43(((1, 0, 0), (0, 0, 1), (0, -1, 0), (0, 0, 0)))
						for bone in self.boneList: 
							bone.setMatrix( (bone.getMatrix().inverse() * rot_mat).inverse()) 	#rotate upright in-place
						
				else:
					bDoSkin = False
			
			print(offsetInfo)
			for i in range(countArray[0]): # LODGroups
				meshVertexInfo = []
				ctx = rapi.rpgCreateContext()
				bs.seek(offsetInfo[i])
				numOffsets = bs.readUByte()
				bs.seek(3,1)
				uknFloat = bs.readUInt()
				offsetSubOffsets = bs.readUInt64()
				bs.seek(offsetSubOffsets)
				
				meshOffsetInfo = []
				
				for j in range(numOffsets):
					meshOffsetInfo.append(bs.readUInt64())
				
				for j in range(numOffsets): # MainMeshes
					bs.seek(meshOffsetInfo[j])
					meshVertexInfo.append([bs.readUByte(), bs.readUByte(), bs.readUShort(), bs.readUInt(), bs.readUInt(), bs.readUInt()])
					submeshData = []
					for k in range(meshVertexInfo[j][1]):
						if sGameName == "RERT" or sGameName == "REVerse" or sGameName == "MHRise" or sGameName == "RE8":
							submeshData.append([bs.readUInt(), bs.readUInt(), bs.readUInt(), bs.readUInt(), bs.readUInt64()])
						else:
							submeshData.append([bs.readUInt(), bs.readUInt(), bs.readUInt(), bs.readUInt()]) #0 MaterialID, 1 faceCount, 2 indexBufferStartIndex, 3 vertexStartIndex
					
					submeshDataArr.append(submeshData)
					
					for k in range(meshVertexInfo[j][1]): # Submeshes
					
						if bUseOldNamingScheme:
							meshName = "LODGroup_" + str(i+1) + "_MainMesh_" + str(j+1) + "_SubMesh_" + str(submeshData[k][0]+1)
						else:
							if bRenameMeshesToFilenames:
								meshName = os.path.splitext(rapi.getLocalFileName(sInputName))[0].replace(".mesh", "") + "_" + str(j+1) + "_" + str(k+1)
							elif bShorterNames:
								meshName = "LOD_" + str(i+1) + "_Main_" + str(j+1) + "_Sub_" + str(k+1)
							else:
								meshName = "LODGroup_" + str(i+1) + "_MainMesh_" + str(j+1) + "_SubMesh_" + str(k+1)
							
						rapi.rpgSetName(meshName)
						if bRenameMeshesToFilenames: 
							rapi.rpgSetMaterial(meshName)
						#else:
						#	rapi.rpgSetMaterial(meshName)
						matName = ""; matHash = 0
						
						#Search for material
						if bLoadedMats:
							matHash = hash_wide(names[matIndices[submeshData[k][0]]])
							if i == 0:
								for m in range(len(self.matHashes)):
									if self.matHashes[m] == matHash:
										if self.matNames[m] != names[nameRemapTable[submeshData[k][0]]]:
											print ("WARNING: " + meshName + "\'s material name \"" + self.matNames[m] + "\" in MDF does not match its material hash! \n	True material name: \"" + names[nameRemapTable[submeshData[k][0]]] + "\"")
										matName = self.matNames[m]
										#rapi.rpgSetLightmap(matArray[k].replace(".dds".lower(), ""))
										break
						if matName == "":
							if matHash == 0: 
								matHash = hash_wide(names[matIndices[submeshData[k][0]]])
							if bLoadedMats:
								print ("WARNING: " + meshName + "\'s material \"" + names[nameRemapTable[submeshData[k][0]]] + "\" hash " + str(matHash) + " not found in MDF!")
							self.matNames.append(names[nameRemapTable[submeshData[k][0]]])
							matName = self.matNames[len(self.matNames)-1]
										
						rapi.rpgSetMaterial(matName)
						rapi.rpgSetPosScaleBias((fDefaultMeshScale, fDefaultMeshScale, fDefaultMeshScale), (0, 0, 0))
						if bImportMaterialNames:
							rapi.rpgSetName(meshName + "__" + matName)
						
						if sGameName == "RE7":
							rapi.rpgBindPositionBufferOfs(vertexBuffer, noesis.RPGEODATA_FLOAT, bytesPerVert, (submeshData[k][3] * bytesPerVert))
							rapi.rpgBindNormalBufferOfs(vertexBuffer, noesis.RPGEODATA_BYTE, bytesPerVert, 12 + (submeshData[k][3] * bytesPerVert))
							rapi.rpgBindTangentBufferOfs(vertexBuffer, noesis.RPGEODATA_BYTE, bytesPerVert, 16 + (submeshData[k][3] * bytesPerVert))
							rapi.rpgBindUV1BufferOfs(vertexBuffer, noesis.RPGEODATA_HALFFLOAT, bytesPerVert, 20 + (submeshData[k][3] * bytesPerVert))
							if (countArray[2] > 1):
								rapi.rpgBindUV2BufferOfs(vertexBuffer, noesis.RPGEODATA_HALFFLOAT, bytesPerVert, 24 + (submeshData[k][3] * bytesPerVert))
							if bonesOffs > 0:
								rapi.rpgSetBoneMap(boneRemapTable)
								rapi.rpgBindBoneIndexBufferOfs(vertexBuffer, noesis.RPGEODATA_UBYTE, bytesPerVert, 24 + addBytes + (submeshData[k][3	] * bytesPerVert), 8)
								rapi.rpgBindBoneWeightBufferOfs(vertexBuffer, noesis.RPGEODATA_UBYTE, bytesPerVert, 32 + addBytes + (submeshData[k][3] * bytesPerVert), 8)
						else:
							if positionIndex != -1:
								rapi.rpgBindPositionBufferOfs(vertexBuffer, noesis.RPGEODATA_FLOAT, vertElemHeaders[positionIndex][1], (vertElemHeaders[positionIndex][1] * submeshData[k][3]))
							
							if normalIndex != -1 and bNORMsEnabled:
								if bDebugNormals and not bColorsEnabled:
									rapi.rpgBindColorBufferOfs(vertexBuffer, noesis.RPGEODATA_BYTE, vertElemHeaders[normalIndex][1], vertElemHeaders[normalIndex][2] + (vertElemHeaders[normalIndex][1] * submeshData[k][3]), 4)
								else:
									rapi.rpgBindNormalBufferOfs(vertexBuffer, noesis.RPGEODATA_BYTE, vertElemHeaders[normalIndex][1], vertElemHeaders[normalIndex][2] + (vertElemHeaders[normalIndex][1] * submeshData[k][3]))
									if bTANGsEnabled:
										rapi.rpgBindTangentBufferOfs(vertexBuffer, noesis.RPGEODATA_BYTE, vertElemHeaders[normalIndex][1], 4 + vertElemHeaders[normalIndex][2] + (vertElemHeaders[normalIndex][1] * submeshData[k][3]))
							
							if uvIndex != -1 and bUVsEnabled:
								rapi.rpgBindUV1BufferOfs(vertexBuffer, noesis.RPGEODATA_HALFFLOAT, vertElemHeaders[uvIndex][1], vertElemHeaders[uvIndex][2] + (vertElemHeaders[uvIndex][1] * submeshData[k][3]))
							if uv2Index != -1 and bUVsEnabled:
								rapi.rpgBindUV2BufferOfs(vertexBuffer, noesis.RPGEODATA_HALFFLOAT, vertElemHeaders[uv2Index][1], vertElemHeaders[uv2Index][2] + (vertElemHeaders[uv2Index][1] * submeshData[k][3]))
							
							#print (meshName, "has rigging:", bSkinningEnabled)
							if weightIndex != -1 and bSkinningEnabled and bDoSkin:
								rapi.rpgSetBoneMap(boneRemapTable)
								rapi.rpgBindBoneIndexBufferOfs(vertexBuffer, noesis.RPGEODATA_UBYTE, vertElemHeaders[weightIndex][1], vertElemHeaders[weightIndex][2] + (vertElemHeaders[weightIndex][1] * submeshData[k][3]), 8)
								rapi.rpgBindBoneWeightBufferOfs(vertexBuffer, noesis.RPGEODATA_UBYTE, vertElemHeaders[weightIndex][1], vertElemHeaders[weightIndex][2] + (vertElemHeaders[weightIndex][1] * submeshData[k][3]) + 8, 8)
								
							if colorIndex != -1 and bColorsEnabled:
								rapi.rpgBindColorBufferOfs(vertexBuffer, noesis.RPGEODATA_UBYTE, vertElemHeaders[colorIndex][1], vertElemHeaders[colorIndex][2] + (vertElemHeaders[colorIndex][1] * submeshData[k][3]), 4)
								
						if submeshData[k][1] > 0:
							bs.seek(faceBuffOffs + (submeshData[k][2] * 2))
							indexBuffer = bs.readBytes(submeshData[k][1] * 2)
							if bRenderAsPoints:
								rapi.rpgCommitTriangles(None, noesis.RPGEODATA_USHORT, (meshVertexInfo[j][4] - (submeshData[k][3])), noesis.RPGEO_POINTS, 0x1)
							else:
								rapi.rpgSetStripEnder(0x10000)
								rapi.rpgCommitTriangles(indexBuffer, noesis.RPGEODATA_USHORT, submeshData[k][1], noesis.RPGEO_TRIANGLE, 0x1)
								rapi.rpgClearBufferBinds()
								
				try:
					mdl = rapi.rpgConstructModelAndSort()
					if mdl.meshes[0].name.find("_") == 4:
						print ("\nWARNING: Noesis split detected!\n   Export this mesh to FBX with the advanced option '-fbxmeshmerge'\n")
						rapi.rpgOptimize()
				except:
					mdl = NoeModel()
				mdl.setBones(self.boneList)
				mdl.setModelMaterials(NoeModelMaterials(self.texList, self.matList))
				mdlList.append(mdl)
					
				if not bImportAllLODs:
					break
					
			print ("\nMESH Material Count:", matCount)
			if bLoadedMats:
				print ("MDF Material Count:", len(self.matList))
					
		if occluderMeshOffs:
			ctx = rapi.rpgCreateContext()
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
				#print ("indexCount is ", indexCount)
				ukn = bs.readUInt()
				indexCount2 = bs.readUInt()
				occluderMeshes.append([uknBytes, vertexCount, indexCount])
				bs.seek(lastVertPos)
				#print ("started at", bs.tell())
				vertexBuffer = bs.readBytes(12 * vertexCount)
				#print ("ended at", bs.tell())
				lastVertPos = bs.tell()
				bs.seek(lastFacesPos)
				#print ("started at", bs.tell())
				indexBuffer = bs.readBytes(indexCount * 2)
				#print ("ended at", bs.tell())
				lastFacesPos = bs.tell()
				rapi.rpgSetName("OccluderMesh_" + str(i))
				rapi.rpgBindPositionBuffer(vertexBuffer, noesis.RPGEODATA_FLOAT, 12)
				rapi.rpgSetStripEnder(0x10000)
				try:
					rapi.rpgCommitTriangles(indexBuffer, noesis.RPGEODATA_USHORT, indexCount, noesis.RPGEO_TRIANGLE, 0x1)
					rapi.rpgClearBufferBinds()
					try:
						mdl = rapi.rpgConstructModelAndSort()
						if mdl.meshes[0].name.find("_") == 4:
							print ("\nWARNING: Noesis split detected!\n   Export this mesh to FBX with the advanced option '-fbxmeshmerge'\n")
							rapi.rpgOptimize()
					except:
						mdl = NoeModel()
					mdlList.append(mdl)
				except:
					print("Failed to read Occluder Mesh")

		print (deferredWarning)
		
		return mdlList
		
def meshLoadModel(data, mdlList):
	mesh = meshFile(data)
	mdlList = mesh.loadMeshFile(mdlList)
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
	global w1, w2, bWriteBones, bReWrite, bRigToCoreBones #, doLOD
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
		openOptionsDialog = openOptionsDialogWindow(1000, 165, {"filepath":newMeshName, "exportType":exportType}) #int(len(newMeshName)*7.5)
		openOptionsDialog.createMeshWindow()
		newMeshName = openOptionsDialog.filepath or newMeshName
		if openOptionsDialog.doCancel:
			newMeshName = None
		elif openOptionsDialog.doRewrite:
			newMeshName = newMeshName + " -rewrite"
		elif openOptionsDialog.doWriteBones:
			newMeshName = newMeshName + " -bones"
	else:
		newMeshName = noesis.userPrompt(noesis.NOEUSERVAL_FILEPATH, "Export over " + exportType.upper(), "Choose a " + exportType.upper() + " file to export over", newMeshName, None)

	if newMeshName == None:
		print("Aborting...")
		return
		
	if noesis.optWasInvoked("-flip") or newMeshName.find(" -flip") != -1:
		newMeshName = newMeshName.replace(" -flip", "")
		print ("Exporting with OpenGL handedness")
		w1 = 127; w2 = -128
	
	if noesis.optWasInvoked("-bones") or newMeshName.find(" -bones") != -1:
		newMeshName = newMeshName.replace(" -bones", "")
		print ("Exporting with new skeleton...")
		bWriteBones = True
		
	if newMeshName.find(" -rewrite") != -1:
		newMeshName = newMeshName.replace(" -rewrite", "")
		print ("Exporting from scratch with new skeleton, Mainmesh and Submesh order...")
		bReWrite = True
		bWriteBones = True
		
	if newMeshName.find(" -match") != -1:
		newMeshName = newMeshName.replace(" -match", "")
		print ("Unmatched bones will be rigged to the hips and spine")
		bRigToCoreBones = True
		
	return newMeshName
	

def skelWriteFbxskel(mdl, bs):
	fileName = None
	fbxskelName = getExportName(fileName, "fbxskel")
	
	if fbxskelName == None:
		return 0
		
	while not (rapi.checkFileExists(fbxskelName)):
		print ("File not found!")
		fbxskelName = getExportName(fileName, "fbxskel")	
		fileName = fbxskelName
		if fbxskelName == None:
			return 0
			
	fbxskelFile = rapi.loadIntoByteArray(fbxskelName)
	f = NoeBitStream(fbxskelFile)
	magic = readUIntAt(f, 4)
	
	if magic != 1852599155:
		noesis.messagePrompt("Not a FBXSKEL file.\nAborting...")
		return 0
	
	boneCount = readUIntAt(f, 32)
	f.seek(48)
	
	fbxskelBones = []
	for b in range(boneCount):
		pos = f.tell()
		offset = f.readUInt64()
		f.seek(offset)
		fbxskelBones.append(ReadUnicodeString(f))
		f.seek(pos+64)
	
	for i, bone in enumerate(mdl.bones):
		if bone.name.find('_') == 8 and bone.name.startswith("bone"):
			bone.name = bone.name[9:len(bone.name)] #remove Noesis duplicate numbers
		if bone.name.find('.') != -1:
			bone.name = bone.name.split('.')[0] #remove blender numbers
	
	bs.writeBytes(f.getBuffer()) #copy file
	bones = noeCalculateLocalBoneTransforms(mdl.bones)
	
	for b, bone in enumerate(mdl.bones):
		for i, fbxBone in enumerate(fbxskelBones):
			if bone.name.split(":")[len(bone.name.split(":"))-1] == fbxBone:
				print(i, "Found bone", fbxBone, "in fbxskel")
				bs.seek(48 + i * 64 + 12)
				pName = bone.parentName.split(":")[len(bone.parentName.split(":"))-1]
				if pName in fbxskelBones:
					bs.writeShort(fbxskelBones.index(pName))
					
				bs.seek(48 + i * 64 + 16)
				mat = bones[b]#bone.getMatrix()
				mat[3] *= newScale
				bs.writeFloat(mat[3][0])
				bs.writeFloat(mat[3][1])
				bs.writeFloat(mat[3][2])
				bs.writeFloat(0)
				#bs.writeBytes(.toBytes()) #translation
				
				#bs.writeBytes(mat.toQuat().toBytes()) #rotation
				#rot = mat.toQuat()
				#rot = NoeQuat((-rot[0], -rot[2], rot[1], rot[3]))
				#bs.writeBytes(rot.toBytes())
				#bs.writeFloat(1); bs.writeFloat(1); bs.writeFloat(1) #scale
				
				break
	return 1
			

'''MESH EXPORT ========================================================================================================================================================================'''
def meshWriteModel(mdl, bs):
	global sExportExtension, w1, w2, bWriteBones, bReWrite, bRigToCoreBones, bAddBoneNumbers, sGameName #doLOD
	
	bWriteBones = noesis.optWasInvoked("-bones")
	bReWrite = noesis.optWasInvoked("-rewrite")
	
	w1 = -128
	w2 = 127
	if noesis.optWasInvoked("-flip"): 
		w1 = 127; w2 = -128
	
	if bAlwaysRewrite or noesis.optWasInvoked("-b"):
		bReWrite = True
	if bAlwaysWriteBones:
		bWriteBones = True
		
	def padToNextLine(bitstream):
		while bitstream.tell() % 16 != 0:
			bitstream.writeByte(0)
			
	def cross(a, b):
		c = [a[1]*b[2] - a[2]*b[1],
			 a[2]*b[0] - a[0]*b[2],
			 a[0]*b[1] - a[1]*b[0]]
		return c
		
	def roundValue(value):
		value = int(value * 127)
		if value < 0: 
			return value - 1 
		return value + 1
		
	def dot(v1, v2):
		return sum(x*y for x,y in zip(v1,v2))	
		
	print ("		----RE Engine MESH Export v2.9993 by alphaZomega----\nOpen fmt_RE_MESH.py in your Noesis plugins folder to change global exporter options.\nExport Options:\n Input these options in the `Advanced Options` field to use them, or use in CLI mode\n -flip  =  OpenGL / flipped handedness (fixes seams and inverted lighting on some models)\n -bones = save new skeleton from Noesis to the MESH file\n -bonenumbers = Export with bone numbers, to save a new bone map\n -meshfile [filename]= Input the location of a [filename] to export over that file\n -noprompt = Do not show any prompts\n -rewrite = save new MainMesh and SubMesh order (also saves bones)\n") #\n -lod = export with additional LODGroups") # 
	
	ext = os.path.splitext(rapi.getOutputName())[1]
	RERTBytes = 0
	
	sGameName = "RE2" 
	if ext.find(".1808282334") != -1:
		sGameName = "DMC5"
	elif ext.find(".1902042334") != -1:
		sGameName = "RE3"
	elif ext.find(".2010231143") != -1:
		sGameName = "REVerse"
	elif ext.find(".2101050001") != -1:
		sGameName = "RE8"
	if (ext.find(".2109108288") != -1) or (ext.find(".220128762") != -1): #RE2/RE3RT, and RE7RT
		sGameName = "RERT"
		RERTBytes = 8
	elif ext.find(".2109148288") != -1: #MHRise Sunbreak
		#sGameName = "MHRise"
		sGameName = "RERT"
		RERTBytes = 8
	elif ext.find(".2008058288") != -1: #Vanilla MHRise
		sGameName = "MHRise"
	elif ext.find(".32") != -1:
		sGameName = "RE7"
		print ("-rewrite is disabled for RE7")
		bReWrite = False #currently disabled for RE7
		return 0
		
	print ("\n				  ", sGameName, "\n")
	
	bDoUV2 = False
	bDoSkin = False
	bDoColors = False
	bAddNumbers = False
	numLODs = 1
	diff = 0	
	meshVertexInfo = []
	vertElemCountB = 5	
	newScale = (1 / fDefaultMeshScale)
	
	#merge Noesis-split meshes back together:	
	meshesToExport = sorted(mdl.meshes, key=lambda x: x.name) #sort by name (if FBX reorganized)
	if meshesToExport[0].name.find("_") == 4:
		print ("WARNING: Noesis-split meshes detected. Merging meshes back together...")
		ctx = rapi.rpgCreateContext()
		rapi.rpgOptimize()
		combinedMeshes = []
		lastMesh = None
		lastMeshIdx = 0
		offset = 0
		
		glbTriIdxes = []
		glbVertIdxes = []
		for i, mesh in enumerate(mdl.meshes):
			glbVertIdxes.append(mesh.glbVertIdx)
			glbTriIdxes.append(mesh.glbTriIdx)
			print (mesh.glbVertIdx, mesh.glbTriIdx)
			
		for i, mesh in enumerate(mdl.meshes):
			mesh.name = mesh.name[5:len(mesh.name)] #remove 0000_ prefix
			
			if lastMesh == None:
				lastMesh = copy.copy(mesh)
				lastMeshIdx = i
				offset += len(mesh.positions)
			elif mesh.name == lastMesh.name:
				if len(lastMesh.positions) == len(mesh.positions) and len(lastMesh.indices) == len(mesh.indices) \
				and mesh.positions[len(lastMesh.positions)-1] == lastMesh.positions[len(lastMesh.positions)-1]: #ignore real duplicates
					continue
				newIndices = []
				for j in range(len(mesh.indices)):
					newIndices.append(mesh.indices[j] + offset)
				#print(lastMesh.name, len(newIndices))
				#print (glbVertIdxes[lastMeshIdx], glbTriIdxes[lastMeshIdx])
				lastMesh.setPositions((lastMesh.positions + mesh.positions))
				lastMesh.setUVs((lastMesh.uvs + mesh.uvs))
				lastMesh.setUVs((lastMesh.lmUVs + mesh.lmUVs), 1)
				lastMesh.setTangents((lastMesh.tangents + mesh.tangents))
				lastMesh.setWeights((lastMesh.weights + mesh.weights))
				lastMesh.setIndices((lastMesh.indices + tuple(newIndices)))
				offset += len(mesh.positions)
			
			if i == len(mdl.meshes)-1 or mesh.name != mdl.meshes[i+1].name[5:len(mdl.meshes[i+1].name)]:
				combinedMeshes.append(lastMesh)
				lastMesh = None
				offset = 0
				
		meshesToExport = combinedMeshes

		print ("Recombined Mesh List:" )
		for mesh in meshesToExport:
			print (mesh.name, ", ", len(mesh.positions), "verts,", int(len(mesh.indices)/3), "faces")
			if len(mesh.positions) > 65535:
				print ("	WARNING: This mesh has more than the maximum amount of 65536 vertices")
				'''uniqueVerts = {} #try manual optimize:
				#newIndices = []
				newPositions = []
				newUV1 = []
				newUV2 = []
				newTangents = []
				newWeights = []
				for i, pos in enumerate(mesh.positions):
					key = str(pos[0]) + str(pos[1]) + str(pos[2])
					if key in uniqueVerts:
						uniqueVerts[key].append(i)
					else:
						uniqueVerts[key] = [i]
				for i, idx in enumerate(mesh.indices):
					pos = mesh.positions[idx]
					key = str(pos[0]) + str(pos[1]) + str(pos[2])
					if idx > 65535 and key in uniqueVerts:
						mesh.indices[i] = uniqueVerts[key][0]
						#newIndices.append(uniqueVerts[key][0])
					#else:
					#	newIndices.append(idx)
				for i, (pos, idxList) in enumerate(uniqueVerts.items()):
					newPositions.append(mesh.positions[ idxList[0] ])
					newUV1.append(mesh.uvs[ idxList[0] ])
					newUV2.append(mesh.lmUVs[ idxList[0] ])
					newTangents.append(mesh.tangents[ idxList[0] ])
					newWeights.append(mesh.weights[ idxList[0] ])
					#newIndices.append(idxList[0])
				mesh.setPositions(newPositions)
				mesh.setUVs(newUV1)
				mesh.setUVs(newUV2, 1)
				mesh.setTangents(newTangents)
				mesh.setWeights(newWeights)
				#mesh.setIndices(newIndices)
				print ("Optimized to", len(mesh.positions), "vertices", len(mesh.positions), "positions" )'''
	
	#Remove Blender numbers from all names
	for mesh in mdl.meshes:
		if mesh.name.find('.') != -1:
			print ("Renaming Mesh " + str(mesh.name) + " to " + str(mesh.name.split('.')[0]))
			mesh.name = mesh.name.split('.')[0]
		if len(mesh.lmUVs) <= 0: #make sure UV2 exists
			mesh.lmUVs = mesh.uvs
	
	#Validate meshes are named correctly
	objToExport = []
	for i, mesh in enumerate(meshesToExport):
		ss = mesh.name.lower().split('_')			
		if len(ss) >= 6:
			#if ss[0] == 'lodgroup' and ss[1].isnumeric() and ss[2] == 'mainmesh' and ss[3].isnumeric() and ss[4] == 'submesh' and ss[5].isnumeric():
			if ss[1].isnumeric() and ss[3].isnumeric() and ss[5].isnumeric():
				objToExport.append(i)
	
	submeshes = []
	f, newMeshName = None, None
	
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
			for mesh in submeshes:
				if len(mesh.weights) > 0:
					bDoSkin = True
					break
					
	#Prompt for source mesh to export over / export options:
	def showOptionsDialog():
		global bReWrite
		nonlocal bDoSkin, submeshes, f, newMeshName
		fileName = None
		if noesis.optWasInvoked("-meshfile"):
			newMeshName = noesis.optGetArg("-meshfile")
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
			magic = f.readUInt()
			if magic != 1213416781:
				noesis.messagePrompt("Not a MESH file.\nAborting...")
				return 0		
			bonesOffs = readUIntAt(f, 48)
			if bonesOffs > 0:
				bDoSkin = True
		else:
			checkReWriteMeshes()
			if not bReWrite:
				showOptionsDialog()
	
	if bReWrite:
		checkReWriteMeshes()
	else:
		showOptionsDialog()
	
	if not bReWrite:
		if newMeshName != None:
			print("Source Mesh:\n", newMeshName)
		else:
			return 0
	
	if bDoSkin:
		print ("  Rigged mesh detected, exporting with skin weights...")
	else:
		print("  No rigging detected")
		
	#check if exporting bones and create skin bone map if so:	
	vertElemCount = 3 
	if bDoSkin:
		vertElemCount += 1
		bonesList = []
		newSkinBoneMap = []
		
		if bAddBoneNumbers == 1 or noesis.optWasInvoked("-bonenumbers"):
			bAddNumbers = True
			
		elif bAddBoneNumbers == 2:
			if len(mdl.bones) > 256:
				print ("Model has more than 256 bones, auto-enabling bone numbers...")
				bAddNumbers = True
			else:
				for bone in mdl.bones:
					if bone.name.find(':') != -1:
						bAddNumbers = True
						print (bone.name, "has a \':\' (colon) in its name, auto-enabling bone numbers...")
						break
		
		for i, bone in enumerate(mdl.bones):
			if bone.name.find('_') == 8 and bone.name.startswith("bone"):
				print ("Renaming Bone " + str(bone.name) + " to " + bone.name[9:len(bone.name)] )
				bone.name = bone.name[9:len(bone.name)] #remove Noesis duplicate numbers
			if bone.name.find('.') != -1:
				print ("Renaming Bone " + str(bone.name) + " to " + str(bone.name.split('.')[0]))
				bone.name = bone.name.split('.')[0] #remove blender numbers
			
			if bone.name.find(':') != -1:
				bonesList.append(bone.name.split(':')[1]) #remove bone numbers
				if len(newSkinBoneMap) < 256:
					newSkinBoneMap.append(i)
			else:
				bonesList.append(bone.name)
				if not bAddNumbers and len(newSkinBoneMap) < 256:
					newSkinBoneMap.append(i)
					
		if bAddNumbers and len(newSkinBoneMap) == 0: #in case bone numbers is on but the skeleton has no bone numbers:
			print ("WARNING: No bone numbers detected, only the first 256 bones will be rigged")
			bAddNumbers = False
			for i, bone in enumerate(mdl.bones):
				if len(newSkinBoneMap) < 256:
					newSkinBoneMap.append(i)		
					
	newBBOffs = 0
	#OLD WAY (reading source file, no rewrite):
	#====================================================================
	if not bReWrite:
		f.seek(18)
		if sGameName == "RE7":
			f.seek(14)
		numNodes = f.readUShort()
		if sGameName != "RE7":
			f.seek(24)
		LOD1Offs = f.readUInt64()
		LOD2Offs = f.readUInt64()
		ukn2 = f.readUInt64()
		bonesOffs = f.readUInt64()
		if sGameName != "RE7":
			topologyOffs = f.readUInt64()
		bShapesHdrOffs = f.readUInt64()
		floatsHdrOffs = f.readUInt64()
		newBBOffs = floatsHdrOffs
		vBuffHdrOffs = f.readUInt64()
		ukn3 = f.readUInt64()
		nodesIndicesOffs = f.readUInt64()
		boneIndicesOffs = f.readUInt64()
		bshapesIndicesOffs = f.readUInt64()
		namesOffs = f.readUInt64()
		f.seek(LOD1Offs)
		countArray = f.read("16B")
		numMats = countArray[1]
		
		f.seek(vBuffHdrOffs)
		if sGameName == "RE7":
			vertBuffSize = f.readUInt()
			f.seek(12,1)
			faceBuffSize = f.readUInt()
			f.seek(20,1)
			faceBuffOffs = f.readUInt()
			addBytes = 0
			bytesPerVert = 24 
			if bonesOffs > 0:
				bDoSkin = True
				bytesPerVert = 40 
			if countArray[2] > 1: 
				bDoUV2 = True
				addBytes = 4
				bytesPerVert += addBytes
			while f.tell() % 16 != 0: 
				f.seek(1,1)
			vertBuffOffs = f.tell()
		else:
			vertElemHdrOffs = f.readUInt64()
			vertBuffOffs = f.readUInt64()
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
			if sGameName == "RE7":
				f.seek(floatsHdrOffs)
				boneMapCount = f.readUInt()
				f.seek(LOD1Offs+72)
				RE7SkinBoneMapOffs = f.readUInt64()+16
			else:
				f.seek(bonesOffs+4)
				boneMapCount = f.readUInt()
			
			f.seek(bonesOffs)			
			boneCount = f.readUInt()
			f.seek(12,1)
			hierarchyOffs = f.readUInt64()
			localOffs = f.readUInt64()
			globalOffs = f.readUInt64()
			inverseGlobalOffs = f.readUInt64()
			
			if sGameName == "RE7":
				f.seek(RE7SkinBoneMapOffs)
				
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
		
		if sGameName == "RERT" or sGameName == "REVerse" or sGameName == "MHRise" or sGameName == "RE8" or sGameName == "RE7":
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
					for s in range(len(objToExport)):
						#print (meshesToExport[objToExport[s]].name)
						sName = meshesToExport[objToExport[s]].name.split('_')
						if int(sName[1]) == (ldc+1) and int(sName[3]) == (mmc+1) and ((not bUseOldNamingScheme and int(sName[5]) == (smc+1)) or (bUseOldNamingScheme and int(sName[5]) == (matID))):
							submeshes.append(copy.copy(meshesToExport[objToExport[s]]))
							bFind = 1							
							break
					if not bFind:  #create invisible placeholder submesh
						blankMeshName = "LODGroup_" + str(ldc+1) + "_MainMesh_" + str(mmc+1) + "_SubMesh_" + str(smc+1)
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
		
	'''for mesh in mdl.meshes:
		bFound = False
		for submesh in submeshes:
			if submesh.name.split("_") < 7:
				submeshes.remove(submesh)
				print (mesh.name, "has too few underscores and was dropped from export" )
			if mesh.name == submesh.name:
				bFound = True
		if not bFound:
			print (mesh.name, "was dropped from the export" )'''
			
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
				print ("Vertex colors detected")
				break
		if bReWrite and bColorsExist:
			bDoColors = True
			break
			
	if bRotateBonesUpright:
		#rot_mat = NoeMat43(((1, 0, 0), (0, 0, 1), (0, -1, 0), (0, 0, 0)))
		rot_mat = NoeMat43(((1, 0, 0), (0, -1, 0), (0, 0, 1), (0, 0, 0)))
		for bone in mdl.bones:
			bone.setMatrix( (bone.getMatrix().inverse() * rot_mat).inverse()) 	#rotate back to normal
	
	#NEW WAY (rewrite)
	#====================================================================
	if bReWrite: #save new mesh order	
		bDoUV2 = True
	
		#prepare new submesh order:
		newMainMeshes = []; newSubMeshes = []; newMaterialNames = []
		indicesBefore = 0; vertsBefore = 0; mmIndCount = 0; mmVertCount = 0
		lastMainMesh = submeshes[0].name.split('_')[3]
		splitName = mesh.name.split('_')
		meshOffsets= []
		
		for mesh in submeshes:
			mat = mesh.name.split('__', 1)[1]
			if mat not in newMaterialNames:
				newMaterialNames.append(mat)
				
		numMats = len(newMaterialNames)
		print ("\nMESH Material Count:", numMats)
		
		for i, mesh in enumerate(submeshes):
			try:
				if len(splitName) <= 6:
					bReWrite = False
					break
				else:
					newMaterialID = newMaterialNames.index(mesh.name.split('__', 1)[1])
					if mesh.name.split('_')[3] != lastMainMesh:
						newMainMeshes.append((newSubMeshes, mmVertCount, mmIndCount))
						newSubMeshes = []; mmIndCount = 0; mmVertCount = 0
						lastMainMesh = mesh.name.split('_')[3]
						 
					newSubMeshes.append((newMaterialID, len(mesh.indices) , vertsBefore, indicesBefore))
					vertsBefore += len(mesh.positions)
					mmVertCount += len(mesh.positions)
					indicesBefore += len(mesh.indices)
					mmIndCount += len(mesh.indices)
					if i == len(submeshes)-1:
						newMainMeshes.append((newSubMeshes, mmVertCount, mmIndCount))
			except:
				print("Failed to parse mesh name", mesh.name)
		
		#header:
		bs.writeUInt(1213416781) #MESH
		if sGameName == "RE2" or sGameName == "RE3" or sGameName == "DMC5":
			bs.writeUInt(386270720) #version no
		elif sGameName == "RE8":
			bs.writeUInt(2020091500)
		elif sGameName == "RE7":
			bs.writeUInt(352921600)
		elif sGameName == "MHRise":
			bs.writeUInt(2007158797)
		elif sGameName == "RERT":
			bs.writeUInt(21041600)
			
		bs.writeUInt(0) #Filesize
		bs.writeUInt(0) #LODGroupHash
		if bDoSkin:
			bs.writeUShort(3) #flag
		else:
			bs.writeUShort(0)
		#print ("this model nodes:", len(mdl.bones) * bDoSkin + numMats)
		bs.writeUShort(len(mdl.bones) * bDoSkin + numMats) #Node Count
		bs.writeUInt(0) #LODGroupHash
		LOD1Offs = 128 if (sGameName == "RERT" or sGameName == "RE8" or sGameName == "MHRise") else 136
		
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
			
		bs.writeByte(1) #set to one LODGroup
		bs.writeByte(len(newMaterialNames)) #mat count
		bs.writeByte(2) #set to 2 UV channels
		bs.writeByte(1) #unknown
		bs.writeUInt(len(submeshes)) #total mesh count
		bs.writeUInt64(0)
		
		if sGameName == "RE2" or sGameName == "RE3" or sGameName == "DMC5":
			bs.writeFloat(0.009527391)	#unknown (these values taken from a RE2 model)
			bs.writeFloat(0.8515151)  	#unknown
			bs.writeFloat(0.04847997) 	#unknown
			bs.writeFloat(0.8639101)  	#unknown
		else:
			bs.writeFloat(0.07618849) 	#unknown
			bs.writeFloat(0.2573551)  	#unknown
			
		#Prepare for bounding box calc:	
		mainBBOffs = bs.tell()
		for i in range(4):
			bs.writeUInt64(0) #main bounding box placeholder
		
		#if sGameName == "RE2" or sGameName == "RE3" or sGameName == "DMC5":
		bs.writeUInt64(bs.tell()+8) #offset to LODOffsets
		
		if (bs.tell()+8) % 16 != 0:
			bs.writeUInt64(bs.tell()+16) #first (and only) LODOffset
		else:
			bs.writeUInt64(bs.tell()+8)
		padToNextLine(bs)
		
		#Write LODGroup:
		bs.writeUInt(len(newMainMeshes))
		bs.writeFloat(0.02667995) #unknown, maybe LOD distance change
		bs.writeUInt64(bs.tell()+8) #Mainmeshes offset
		
		newMainMeshesOffset = bs.tell()
		for i in range(len(newMainMeshes)):
			bs.writeUInt64(0)
		
		while(bs.tell() % 16 != 0):
			bs.writeByte(0)
		
		#write new MainMeshes:
		for i, mm in enumerate(newMainMeshes):
			newMMOffset = bs.tell()
			bs.writeByte(i) #Group ID
			bs.writeByte(len(mm[0])) #Submesh count
			bs.writeShort(0)
			bs.writeInt(0)
			bs.writeUInt(mm[1]) #MainMesh index count
			bs.writeUInt(mm[2]) #MainMesh vertex count
			meshVertexInfo.append([i, len(mm[0]), 0, 0, mm[1], mm[2]])
			
			for j, sm in enumerate(mm[0]):
				bs.writeUInt(sm[0])
				bs.writeUInt(sm[1])
				bs.writeUInt(sm[2])
				bs.writeUInt(sm[3])
				if sGameName != "RE7" and sGameName != "RE2" and sGameName != "RE3" and sGameName != "DMC5":
					bs.writeUInt64(0)
			pos = bs.tell()
			bs.seek(newMainMeshesOffset + i * 8)
			bs.writeUInt64(newMMOffset)
			meshOffsets.append(newMMOffset)
			bs.seek(pos)
		
		bonesOffs = bs.tell()
		bs.seek(48)
		if not bDoSkin:
			bs.seek(48,1) #to material indices offset instead
		bs.writeUInt64(bonesOffs)
		bs.seek(bonesOffs)
		mainmeshCount = len(newMainMeshes)
		
	if bDoUV2:
		vertElemCount += 1
	if bDoColors:
		vertElemCount += 1

	#save new skeleton:
	if (bReWrite or bWriteBones): 
		if bDoSkin:
			boneRemapTable = []
			
			if bAddNumbers and len(newSkinBoneMap) > 0:
				boneMapLength = len(newSkinBoneMap)
			else:
				boneMapLength = 256 if len(mdl.bones) > 256 else len(mdl.bones)
				
			if sGameName == "RE7":
				f.seek(floatsHdrOffs)
				boneMapCount = f.readUInt()
				f.seek(LOD1Offs+72)
				RE7SkinBoneMapOffs = f.readUInt64()+16
				f.seek(0)
				bs.writeBytes(f.readBytes(RE7SkinBoneMapOffs)) #to skin bone map
				#write skin bone map (RE7):
				if bAddNumbers and len(newSkinBoneMap) > 0:
					for i in range(len(newSkinBoneMap)):
						bs.writeUShort(newSkinBoneMap[i])
					boneRemapTable = newSkinBoneMap
				else:
					for i in range(boneMapLength): 
						bs.writeUShort(i)
						boneRemapTable.append(i)
				padToNextLine(bs)
				newMainMeshHdrOffs = bs.tell()
				
				f.seek(RE7SkinBoneMapOffs-8)
				RE7MainMeshHdrOffs = f.readUInt()
				f.seek(-12,1)
				RE7MainMeshCount = f.readUByte()
				f.seek(RE7MainMeshHdrOffs)
				diff = newMainMeshHdrOffs - RE7MainMeshHdrOffs
				bs.seek(RE7SkinBoneMapOffs-8)
				bs.writeUInt(newMainMeshHdrOffs)
				bs.seek(newMainMeshHdrOffs)
				bs.writeBytes(f.readBytes(bonesOffs - RE7MainMeshHdrOffs)) #to start of bones header
				bonesOffs = bs.tell()
				bs.seek(newMainMeshHdrOffs)
				f.seek(RE7MainMeshHdrOffs)
				for i in range(RE7MainMeshCount):
					bs.writeUInt64(f.readUInt64() + diff)
					meshOffsets[i] += diff
				bs.seek(bonesOffs)
			elif not bReWrite:
				bs.writeBytes(f.readBytes(bonesOffs)) #to bone name start
		
			#write new skeleton header
			bs.writeUInt(len(mdl.bones)) #bone count
			bs.writeUInt(boneMapLength)  #bone map count
			

			for b in range(5): 
				bs.writeUInt64(0)
			
			#write skin bone map:
			if sGameName != "RE7":
				if bAddNumbers and len(newSkinBoneMap) > 0:
					for i in range(len(newSkinBoneMap)):
						bs.writeUShort(newSkinBoneMap[i])
					boneRemapTable = newSkinBoneMap
				else:
					for i in range(boneMapLength): 
						bs.writeUShort(i)
						boneRemapTable.append(i)
				padToNextLine(bs)
			
			if (len(boneRemapTable) > 256):
				print ("WARNING! Bone map is greater than 256 bones!")
			
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
				elif bnName.startswith("root") or bnName.startswith("cog") or bnName.startswith("hip") \
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
		bs.seek(18)
		if sGameName == "RE7": bs.seek(-4,1)
		bs.writeUShort(numMats + len(mdl.bones) * bDoSkin) #numNodes
		if sGameName == "RE7": 
			bs.seek(24,1)
			bs.writeUInt64(bonesOffs)
			
		bs.seek(72)
		if sGameName == "RE7": bs.seek(-16,1)
		if bDoSkin:
			bs.writeUInt64(newBBOffs)
			bs.writeUInt64(newVertBuffHdrOffs)
			bs.seek(8, 1)
			bs.writeUInt64(newMatIndicesOffs)
			bs.writeUInt64(newBoneMapIndicesOffs)
			bs.seek(8, 1)
		else:
			bs.seek(8,1)
			bs.writeUInt64(newVertBuffHdrOffs)
			bs.seek(32,1)
		bs.writeUInt64(newNamesOffs)
		
		#copy + fix vertexBufferHeader
		bs.seek(newVertBuffHdrOffs)
		if sGameName == "RE7":
			f.seek(vBuffHdrOffs)
			bs.writeBytes(f.readBytes(48))
		else:
			newVertBuffOffs = newVertBuffHdrOffs + 72 + 8*bDoSkin + 8*bDoUV2 + 8*bDoColors + 2*RERTBytes
			bs.writeUInt64(bs.tell()+48+RERTBytes*2)
			bs.writeUInt64(newVertBuffOffs)
			if sGameName == "RERT":
				bs.writeUInt64(0)
			bs.writeUInt64(0)
			bs.writeUInt64(0)
			bs.writeShort(vertElemCount)
			bs.writeShort(vertElemCount)
			bs.writeUInt64(0)
			bs.writeInt(-newVertBuffOffs)
			
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
	if sGameName == "RE7":
		for mesh in submeshes:
			submeshVertexStride.append(vertexStrideStart)
			submeshVertexCount.append(len(mesh.positions))
			for v in range(len(mesh.positions)):
			
				bs.writeBytes((mesh.positions[v] * 0.01).toBytes())
				
				bs.writeByte(int(mesh.tangents[v][0][0] * 127 + 0.5000000001)) #normal
				bs.writeByte(int(mesh.tangents[v][0][2] * 127 + 0.5000000001))
				bs.writeByte(int(mesh.tangents[v][0][1] * 127 + 0.5000000001))
				bs.writeByte(0)
				bs.writeByte(int(mesh.tangents[v][2][0] * 127 + 0.5000000001)) #bitangent
				bs.writeByte(int(mesh.tangents[v][2][1] * 127 + 0.5000000001))
				bs.writeByte(int(mesh.tangents[v][2][2] * 127 + 0.5000000001))
				TNW = dot(cross(mesh.tangents[v][0], mesh.tangents[v][1]), mesh.tangents[v][2])
				if (TNW < 0.0):
					bs.writeByte(w1)
				else:
					bs.writeByte(w2)
					
				bs.writeHalfFloat(mesh.uvs[v][0])
				bs.writeHalfFloat(mesh.uvs[v][1])
				
				if bDoUV2:
					bs.writeHalfFloat(mesh.lmUVs[v][0])
					bs.writeHalfFloat(mesh.lmUVs[v][1])
				if bDoSkin:
					pos = bs.tell()
					for i in range(4):
						bs.writeFloat(0)
					bs.seek(pos)
					
					total = 0
					tupleList = []
					weightList = []
					for idx in range(len(mesh.weights[v].weights)):
						weightList.append(round(mesh.weights[v].weights[idx] * 255.0))
						total += weightList[idx]
					if bNormalizeWeights and total != 255:
						weightList[0] += 255 - total
						print ("Normalizing vertex weight", mesh.name, "vertex", v,",", total)
							
					for idx in range(len(mesh.weights[v].weights)):
						if idx > 8:
							print ("Warning: ", mesh.name, "vertex", v,"exceeds the vertex weight limit of 8!", )
							break
						elif mesh.weights[v].weights[idx] != 0:
							tupleList.append((weightList[idx], mesh.weights[v].indices[idx]))
							
					tupleList = sorted(tupleList, reverse=True) #sort in ascending order
					
					pos = bs.tell()
					lastBone = 0
					for idx in range(len(tupleList)):	
						bFind = False
						for b in range(len(boneRemapTable)):
							if names[boneInds[boneRemapTable[b]]] == bonesList[tupleList[idx][1]]:
								bs.writeUByte(b)
								lastBone = b
								bFind = True
								break	
						if bFind == False: #assign unmatched bones
							if not bRigToCoreBones:
								bs.writeUByte(lastBone)
							else:
								for b in range(lastBone, 0, -1):
									if names[boneInds[boneRemapTable[b]]].find("spine") != -1 or names[boneInds[boneRemapTable[b]]].find("hips") != -1:
										bs.writeUByte(b)
										break
					for x in range(8 - len(tupleList)):
						bs.writeUByte(lastBone)
					
					bs.seek(pos+8)
					for wval in range(len(tupleList)):
						bs.writeUByte(tupleList[wval][0])
					bs.seek(pos+16)
			vertexStrideStart += len(mesh.positions)
	else:
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
		for mesh in submeshes:
			for vcmp in mesh.tangents:
				bs.writeByte(int(vcmp[0][0] * 127 + 0.5000000001)) #normal
				bs.writeByte(int(vcmp[0][1] * 127 + 0.5000000001))
				bs.writeByte(int(vcmp[0][2] * 127 + 0.5000000001)) #roundValue
				bs.writeByte(0)
				bs.writeByte(int(vcmp[2][0] * 127 + 0.5000000001)) #bitangent
				bs.writeByte(int(vcmp[2][1] * 127 + 0.5000000001))
				bs.writeByte(int(vcmp[2][2] * 127 + 0.5000000001))
				TNW = dot(cross(vcmp[0], vcmp[1]), vcmp[2])
				if bReWrite:
					if (TNW > 0.0):
						bs.writeByte(w1)
					else:
						bs.writeByte(w2)
				else:
					if (TNW < 0.0):
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
						if idx > 8:
							print ("Warning: ", mesh.name, "vertex", i,"exceeds the vertex weight limit of 8!", )
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
								bs.writeUByte(b)
								lastBone = b
								bFind = True
								break	
						if bFind == False: #assign unmatched bones
							if not bRigToCoreBones:
								bs.writeUByte(lastBone)
							else:
								for b in range(lastBone, 0, -1):
									if names[boneInds[boneRemapTable[b]]].find("spine") != -1 or names[boneInds[boneRemapTable[b]]].find("hips") != -1:
										bs.writeUByte(b)
										break
										
					for x in range(8 - len(tupleList)):
						bs.writeUByte(lastBone)
					
					bs.seek(pos+8)
					for wval in range(len(tupleList)):
						bs.writeUByte(tupleList[wval][0])
					bs.seek(pos+16)
					
		colorsStart = bs.tell()
		if bDoColors:
			for m, mesh in enumerate(submeshes):
				if bColorsExist:
					for RGBA in mesh.colors: #write 0's
						for color in RGBA: 
							bs.writeUByte(int(color * 255 + 0.5))
				else:
					for pos in mesh.positions:
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
				if sGameName == "RERT" or sGameName == "REVerse" or sGameName == "MHRise" or sGameName == "RE8":
					bs.seek(8, 1)
				mainmeshVertexCount += submeshVertexCount[loopSubmeshCount]
				mainmeshFaceCount += submeshFaceSize[loopSubmeshCount]
				loopSubmeshCount += 1
			bs.seek(meshOffsets[mmc]+8)
			bs.writeUInt(mainmeshVertexCount)
			bs.writeUInt(mainmeshFaceCount)
	
	if sGameName == "RE7":
		bs.seek(vBuffHdrOffs + diff)
		bs.writeUInt(vertexDataEnd - vertexPosStart) #Vertex Buffer Size
		bs.seek(12,1)
		bs.writeUInt(faceDataEnd - vertexDataEnd) #Face Buffer Size
		bs.seek(20,1)
		bs.writeUInt64(vertexDataEnd) 	#Face Buffer Offset
		
	else: #Fix vertex buffer header:
		if bReWrite or bWriteBones:
			bs.seek(newVertBuffHdrOffs+16) 
		else: 
			bs.seek(vBuffHdrOffs+16)
		fcBuffSize = faceDataEnd - vertexDataEnd
		bs.writeUInt64(vertexDataEnd) #face buffer offset
		bs.seek(RERTBytes, 1)
		bs.writeUInt(vertexDataEnd - vertexPosStart) #vertex buffer size
		bs.writeUInt(fcBuffSize) #face buffer size
		bs.seek(4,1) #element counts
		bs.writeUInt64(fcBuffSize)
		bs.writeInt(-(vertexPosStart))
		
		if bReWrite:
			bs.seek(newVertBuffHdrOffs + 48 + (RERTBytes * 2))
		else:
			bs.seek(RERTBytes, 1)
			
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
	
	#fix main bounding box:
	bs.seek(LOD1Offs + 24)
	bs.writeBytes((min * newScale).toBytes()) #BBox min
	bs.writeBytes((max * newScale).toBytes()) #BBox max
	
	#fix skeleton bounding boxes:
	if bDoSkin and bCalculateBoundingBoxes:
		for idx, box in boneWeightBBs.items():
			try:
				if bReWrite or bWriteBones:
					remappedBoneIdx = newSkinBoneMap.index(idx)
				else:
					remappedBoneIdx = boneRemapTable.index(idx)
			except:
				continue
			bs.seek(newBBOffs+16+remappedBoneIdx*32)
			#print(names[boneInds[remappedBoneIdx]], bs.tell())
			boneWeightBBs[idx] = [box[0]*newScale, box[1]*newScale, box[2]*newScale, 1.0, box[3]*newScale, box[4]*newScale, box[5]*newScale, 1.0]
			box = boneWeightBBs[idx]
			for coord in box:
				bs.writeFloat(coord)
		#print ("boneWeightBBs:", boneWeightBBs)
		
	bs.seek(LOD1Offs)
	bs.writeByte(1)
	
	#disable shadow LODs
	bs.seek(32)
	if sGameName == "RE7": bs.seek(-8,1)
	bs.writeUShort(0)
	
	#disable normals recalculation data
	if sGameName != "RE7":
		bs.seek(56)
		bs.writeUInt(0)
		
	#set unknown flag to 3 (else crash)
	bs.seek(16)
	bs.writeUByte(3)
	
	#remove blendshapes offsets
	bs.seek(64)
	if sGameName == "RE7": bs.seek(-16,1)
	bs.writeUInt(0)
	bs.seek(112)
	if sGameName == "RE7": bs.seek(-16,1)
	bs.writeUInt(0)
	
	#fileSize
	bs.seek(8)
	bs.writeUInt(faceDataEnd) 
	return 1