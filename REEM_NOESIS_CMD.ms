(
	--RE Engine MESH Noesis CMD tool
	--Version: v0.35
	--Last Release: June 30 2022
	--Authors: alphaZomega, mariokart64n
	local noesis_path = 		"C:\\Program Files\\Noesis\\Noesis.exe"
	
	local re2_pak_location = 	"F:\\modmanager\\REtool\\RE2_chunk_000\\natives\\x64\\"
	local re3_pak_location = 	"F:\\modmanager\\REtool\\RE3_chunk_000\\natives\\stm\\"
	local re7_pak_location = 	"F:\\modmanager\\REtool\\RE7_chunk_000\\natives\\x64\\"
	local re8_pak_location = 	"F:\\modmanager\\REtool\\RE8_chunk_000\\natives\\stm\\"
	local re2rt_pak_location = 	"F:\\modmanager\\REtool\\RE2rt_chunk_000\\natives\\stm\\"
	local re3rt_pak_location = 	"F:\\modmanager\\REtool\\RE3rt_chunk_000\\natives\\stm\\"
	local re7rt_pak_location = 	"F:\\modmanager\\REtool\\RE7rt_chunk_000\\natives\\stm\\"
	local dmc5_pak_location =	"F:\\modmanager\\REtool\\DMC_chunk_000\\natives\\x64\\"
	local mhrise_pak_location = "F:\\modmanager\\REtool\\MHRise_chunk_000\\natives\\stm\\"
	--local rt_pak_location = 	"F:\\modmanager\\REtool\\RE2RT_chunk_000\\natives\\stm\\"
	local show_ReWrite2 = true
	
	local current_pak_location = re2_pak_location
	local force_backface_culling = true
	local reimport_path = "F:\\"
	local python_plugin = "fmt_RE_MESH.py"
	local current_extension = ".2109108288"
	local current_extension2 = ".2109108288"
	local current_path_prefix = "stm"
	local names_to_objects --dictionary
	global formNoesisCMD
	
	struct losDic  (  --maxscript dictionary
		private  
		table = #(),  
		fn binSort a b =   (  
			if a[1] > b[1] then 1  
			else if a[1] < b[1] then -1  
			else 0  
		),  
		fn formatDic dic level:0 spaces:4 =   (  
			strm = "\n" as stringStream  
			padding = ""  
			if level != 0 then  (  
				for a=1 to level do for b=1 to spaces do padding += " "  
			)  
			for k in (dic.keys()) do  (  
				val = dic.getK k  
				case (classof val) of  (  
					(losDic):format "%%:\n%" padding k (formatDic val level:(level+1) spaces:spaces) to:strm  
					default:format "%%:%\n" padding k val to:strm  
				)  
			)  
			(strm as string)  
		),    
		public  
		fn count = keys.count,  
		fn getK k =   (  
			val = bsearch #(k) table binSort  
			if val == undefined then return val  
			val[2]  
		),  
		fn setK k v =  (  
			val = bsearch #(k) table binSort  
			if val == undefined then  (  
				append table #(k,v)  
				qsort table binSort  
				return this  
			)  
			val[2] = v  
			this  
		),  
		fn hasK k =  (  
			t = case (bsearch #(k) table binSort) of (  
				(undefined):false  
				default:true  
			)  
			t  
		),  
		fn delK k =  (  
			indx --findItem keysL (k as name)  
			for i=1 to table.count where table[i][1] == k do  (  
				indx = i  
				exit  
			)  
			if indx == 0 then throw ("there is no key "+k+" in dictionary")  
			deleteItem table indx  
			this  
		),  
		fn keys =  (  
			out = for k in table collect k[1]  
			out  
		),  
		fn pprint =  (  
			print (formatDic this)  
			ok  
		)  
	) 

	fn getAlignedOffset tell alignment = (
		local offset = case alignment of  (
			2: tell + (mod tell 2)
			4: bit.and (tell + 3) 0xFFFFFFFFFFFFFFFC
			8: bit.and (tell + 7) 0xFFFFFFFFFFFFFFF8
			16: bit.and (tell + 15) 0xFFFFFFFFFFFFFFF0
			default: tell
		)
		offset
	)

	fn ReadFixedString &bstream fixedLen = (
		local str = ""
		local length = 0 
		try (
			for s = 1 to fixedLen do (
				local c = (readshort bstream) as integer
				if c == 0 then exit
				fseek bstream -2 #seek_cur
				local d = readbyte bstream
				if d == 0 then continue 
				str += bit.intAsChar(d) 
				if d != 32 then length = s		
			)
		) catch ( "" ) --print "Error reading string" 
		substring str 1 length
	)

	fn detectedBools bstream tell = (
		local originalTell = ftell bstream
		local nonBoolTotal = 0
		local temp = 0
		fseek bstream tell #seek_set
		for i = 1 to 4 do (
			temp = ReadByte bstream
			if temp != 1 and temp != 0 then
				nonBoolTotal += 1
		)
		fseek bstream originalTell #seek_set
		if nonBoolTotal == 0 then
			return true
		return false
	)

	struct via_GameObject (
		Name,
		Tag,
		DrawSelf,
		UpdateSelf,
		TimeScale,
		offset
	)

	fn Read_via_GameObject &bstream timescale_offset = (
		local Info = via_GameObject()
		fseek bstream (getAlignedOffset (ftell bstream) 4) #seek_set
		info.offset = ftell bstream
		local NameSize = Readlong bstream
		Info.Name = ReadFixedString bstream (NameSize * 2)
		fseek bstream (getAlignedOffset (ftell bstream) 4) #seek_set
		local TagSize = Readlong bstream
		Info.Tag = ReadFixedString bstream (TagSize*2)
		Info.DrawSelf = ReadByte bstream
		Info.UpdateSelf = ReadByte bstream
		--fseek bstream (getAlignedOffset (ftell bstream) 4) #seek_set
		fseek bstream timescale_offset #seek_set
		Info.TimeScale = ReadFloat bstream
		print ("Found possible GameObject " + (info as string))
		Info
	)

	struct via_Transform (
		LocalPosition,
		LocalRotation,
		LocalScale,
		ParentBone,
		SameJointsConstraints,
		AbsoluteScaling
	)

	fn Read_via_Transform &bstream = (
		local Info = via_Transform()
		fseek bstream (getAlignedOffset (ftell bstream) 16) #seek_set
		Info.LocalPosition = (point3 (Readfloat bstream) (Readfloat bstream) (Readfloat bstream))--(point3 (ReadFloat bstream) (ReadFloat bstream) (ReadFloat bstream))
		Readlong bstream
		Info.LocalRotation = (quat (Readfloat bstream) (Readfloat bstream) (Readfloat bstream) (Readfloat bstream)) 
		Info.LocalScale = (point3 (Readfloat bstream) (Readfloat bstream) (Readfloat bstream))
		Readlong bstream
		fseek bstream (getAlignedOffset (ftell bstream) 4) #seek_set
		local ParentBoneSize = Readlong bstream
		Info.ParentBone = ReadFixedString bstream (ParentBoneSize*2)
		Info.SameJointsConstraints = ReadByte bstream
		Info.AbsoluteScaling = ReadByte bstream
		Info
	)

	fn readLongAt bstream pos = (
		local returnPos = ftell bstream
		fseek bstream pos #seek_set
		local long = readlong bstream
		fseek bstream returnPos #seek_set
		long
	)
	
	fn readByteAndReturn bstream = (
		local read_byte = readByte bstream
		fseek bstream -1 #seek_cur
		read_byte
	)
	
	fn detectedFloat bstream = (
		local flt = (Readfloat bstream)
		if flt == undefined then return false
		flt = abs flt
		(flt == 0 or (flt >= 0.000000001 and flt <= 100000000.0) )
	)
	
	fn detectedXform bstream = (
		local returnpos = ftell bstream
		local detected = true
		fseek bstream (getAlignedOffset (ftell bstream) 16) #seek_set
		for i=1 to 12 do (
			if not (detectedFloat bstream) then (
				detected = false
				exit
			)
		)
		fseek bstream returnpos #seek_set
		detected
	)
 
	fn detectedString bstream offset = ( 
		local pos = ftell bstream
		local result = false
		fseek bstream offset #seek_set
		if (ReadByte bstream) != 0 and (ReadByte bstream) == 0 and (ReadByte bstream) != 0 and (ReadByte bstream) == 0  and (ReadByte bstream) != 0 and (ReadByte bstream) == 0  then
			result = true
		fseek bstream pos #seek_set
		result
	)

	fn redetectStringBehind bstream is_second_time = (
		local pos = ftell bstream
		local slash_detected = false
		if detectedString bstream (ftell bstream) then (
			while (detectedString bstream (ftell bstream)) == true  do (--and readLongAt bstream ((ftell bstream) - 4) < pos - (ftell bstream)
				fseek bstream -2 #seek_cur
				slash_detected = slash_detected or ((readByteAndReturn bstream) == 47) --this fn is for gameobjects, not files
			)
			fseek bstream -2 #seek_cur
		)
		if not is_second_time and (detectedString bstream (ftell bstream - 10)) then (
			fseek bstream -10 #seek_cur
			redetectStringBehind bstream true
			if not detectedString bstream (ftell bstream + 4) then 
				fseek bstream pos #seek_set
		)
		if slash_detected then 
			fseek bstream pos #seek_set
	)

	fn findMesh bstream limitPoint = (
		local pos = ftell bstream
		local meshPath = ReadFixedString bstream 512
		local counter = 0
		local output --= ""
		format "Scanning from % to % for meshes\n" pos limitPoint
		try (
			while getFilenameType meshPath != ".mesh" do ( --meshPath != "" and
				if (ftell bstream) >= limitPoint then exit
				while (detectedString bstream (ftell bstream)) == false do (
					if (ftell bstream) >= limitPoint then exit
					fseek bstream 4 #seek_cur
				)
				fseek bstream (getAlignedOffset ((ftell bstream) - 2) 4) #seek_set
				meshPath = ReadFixedString bstream 512 
				fseek bstream (getAlignedOffset (ftell bstream) 4) #seek_set
			)
			if getFilenameType meshPath == ".mesh" and (findString (toLower meshPath) "occ" == undefined) then ( --
				local idx = findstring meshPath "/"
				while idx != undefined and idx != 0 do (
					meshPath = replace meshPath idx 1 "\\"
					idx = findstring meshPath "/"
				)
				meshPath = current_pak_location + meshPath + current_extension
				format "Found mesh: %\n\n" meshPath
				output = meshPath
			) else format "\n"
		) catch ( undefined )
		output
	)

	fn findGameObjects &bstream = (
		local GameObjectAddresses = #()
		local GameObjects = #()
		local pos = 0
		fseek bstream 0 #seek_end
		local fileSize = ftell bstream
		fseek bstream 0 #seek_set
		local tester = readlong bstream  #unsigned
		while tester != 5919570  do ( --find "RSZ"
			fseek bstream -2 #seek_cur
			tester = readlong bstream #unsigned
			if tester == undefined then exit
		)
		if tester == 5919570 then (
			fseek bstream (getAlignedOffset (ftell bstream) 4) #seek_set
			while tester != undefined do (
				while tester != undefined and tester != 3212836864 do ( -- 00 00 80 BF , timescale -1.0
					tester = readlong bstream #unsigned
				)
				if (pos < fileSize - 16) and (detectedBools bstream ((ftell bstream) - 8)) == true and detectedXform bstream then (
					append GameObjectAddresses (ftell bstream)
				)
				tester = ReadLong bstream
			)
			if GameObjectAddresses.count > 0 then (
				append GameObjectAddresses fileSize
				for i=1 to GameObjectAddresses.count-2 do (
					fseek bstream GameObjectAddresses[i] #seek_set
					local transform = Read_via_Transform bstream
					fseek bstream (GameObjectAddresses[i] - 36) #seek_set
					local pos2 = ftell bstream
					while not detectedString bstream (ftell bstream) and pos2 - (ftell bstream) < 12 do
						fseek bstream -2 #seek_cur
					if pos2 - (ftell bstream) == 12 then
						fseek bstream pos2 #seek_set
					if detectedString bstream (ftell bstream) then
						redetectStringBehind bstream false
					local gameobject = Read_via_GameObject bstream (GameObjectAddresses[i]-4)
					local mesh = findMesh bstream GameObjectAddresses[i+1]
					if mesh != undefined then (
						append GameObjects #(gameobject, transform, mesh)
						--format "%, % \n" (ftell bstream) (GameObjects[GameObjects.count][3] as string)
					)
				)
			)
		)
		GameObjects
	)

	fn collectSkinBones node = (
		fn findNodesByName list name = (
			for node in list where stricmp node.name name == 0 collect node
		)
		max modify mode
		local bones = #()
		for sk in node.modifiers where iskindof sk Skin do (
			modpanel.setcurrentobject sk
			nodes = for n in (refs.dependson sk) where isvalidnode n collect n
			
			for k=1 to skinops.getnumberbones sk do (
				name = skinops.getbonename sk k 0
				join bones (findNodesByName nodes name)
			)
		)
		bones
	)	

	fn selectSkeleton node = (
		local originalSelection = selection as array
		local bones = collectSkinBones node
		while bones[1].parent != undefined do
			bones[1] = bones[1].parent
		bones = #(bones[1])
		for p in bones where p.children != undefined do join bones p.children
		join originalSelection bones
		select originalSelection
	)

	fn findBoneIdx skinMod bnName = ( 
		for i=1 to (skinOps.GetNumberBones skinMod) do ( 
			if bnName == (skinOps.GetBoneName skinMod i 0) then (
				return i 
			)
		)
		return 0
	)
	
	try(destroydialog formNoesisCMD; clearlistener())catch()
	print current_pak_location
	
	local gamesList = #("RE2 RT", "RE3 RT", "RE2", "RE3", "DMC5", "RE7", "RE7 RT", "RE8", "MHRise", "MHRSunbreak")
	local currentItem = "RE2 RT"
	local currentItemIdx = 1
	local currentItemIdx2 = 1
	
	rollout formNoesisCMD "REEM Noesis 0.35" (
		
		group "Import" (
			button btn_import "Import Mesh" align:#center
			checkbox chk_resetScene "Reset On Import" checked:false align:#left
			checkbox chk_legacyFBX "Use Legacy FBX" checked:false align:#left 
			checkbox chk_fbxMerge "fbxmeshmerge" checked:true align:#left tooltip:"Merges together meshes that have been split apart and have \"0001_\" before their names"
			checkbox chk_folder "Import Folder" checked:false align:#left
			button btn_import_SCN "Import SCN File" tooltip:"Tries to load positioned mesh files from a SCN file"
		)
		group "Export" (
			button btn_export "Export to Game" align:#center
			checkbox chk_flipHandedness "DirectX handedness" checked:true align:#left
			checkbox chk_writeBones "Write skeleton" checked:false align:#left
			checkbox chk_reWrite "ReWrite MESH" checked:false align:#left
			dropdownlist list_gameSelection items:gamesList width:110 height:24 align:#center
			label lbl_currentExt ".mesh.2109108288" align:#center 
			
			--checkbox chk_ReWrite2 "ReWrite 2nd MESH" checked:false align:#left
			--dropdownlist list_gameSelection2 items:gamesList width:110 height:24 align:#center
			--label lbl_currentExt2 ".mesh.2109108288" align:#center
		)
		group "Utilities" (		
			button BtnRemoveBoneNumbers "Add/Remove Bone Numbers" align:#center 
			--button BtnSkinOnTop "Move Skin to Top of Stack" align:#center 
			button BtnSetScale "xScale" offset:[-30,0]
			edittext FldScale "" text:"1.0" fieldWidth:60 labelOnTop:false offset:[70,-25]
			button btn_reimport "Reimport Noesis FBX" align:#center
			button BtnAnimToBlender "Export FBX Animation" align:#center
		)
		group "Config" (
			checkbox chk_showPlugOpt  "Show FBX Options" checked:true align:#left
			checkbox chk_delFBX  "Delete FBX Files" checked:true align:#left
			checkbox chk_bnNumbers  "Use Bone Numbers" checked:true align:#left
			checkbox chk_showCMD  "Show Console" checked:false align:#left enabled:true
			label lbl_noesis "Noesis Path:" align:#left
			edittext edt_noesis "" align:#left
			button btn_noesis "Browse" align:#center
			label lbl_scnpath "Extracted Pak Path:" align:#left
			edittext edt_scnpath "" align:#left
			button btn_scnpath "Browse" align:#center
		)
		local ScaleValue = 1.0
		local cmd = ""
		local fbx_path = ""
		
		fn checkDialog = (
			local hwnd = dialogMonitorOps.getWindowHandle()
			if (uiAccessor.getWindowText hwnd == "Import Name Conflict") then (
				uiAccessor.PressButtonByName hwnd "OK"
			)
			true
		)
		
		fn waitForFileUnlock file file_open_limit:30 = (
			local i = 0
			while i < file_open_limit do (
				if (try(renameFile file (file + ".tmp"))catch(false)) do (
					renameFile (file + ".tmp") file
					exit
				)
				sleep 1
				i += 1
			)
		)
		
		fn noesisComponentsFound = (
			local state = false
			if doesFileExist noesis_path do (
				state = true
			)
			state
		)
		
		fn Import_MESH cmd setCoords = (
			
			
			if cmd == undefined then 
				cmd = "undefined"
			
			if doesFileExist cmd then (
				local showFbxOptions = chk_showPlugOpt.checked
				
				local files = #(cmd)
				if chk_folder.checked and setCoords == undefined then --sets up multi-mesh folder import (not for SCN files)
					files = getFiles (getFilenamePath cmd + "\\*.mesh.*")
				
				for f = 1 to files.count do (
					cmd = files[f]
					
					local key = getFilenameFile (getFilenameFile cmd)
					local old_obj = undefined
					local already_imported = false
					if setCoords != undefined then (
						--format "grabbing value from key %" key
						old_obj = names_to_objects.getK key
						if old_obj != undefined then
							already_imported = true
						--format ", found = %\n" already_imported
					)
					
					if chk_resetScene.checked do 
						resetMaxFile #noPrompt
						
					--local old_obj_idx = findItem imported_names cmd
					--if old_obj_idx == 0 or imported_objects[old_obj_idx] == undefined then (
					
					if not already_imported then (
						fbx_path = (getFilenamePath cmd) + key + ".fbx"
						cmd = (
							"\"" + noesis_path + "\" ?cmode \"" + cmd + "\" \"" + fbx_path + "\"" \
							 + (if chk_legacyFBX.checked then " -fbxoldexport -fbxexportver FBX201400" else "") \
							 + (if chk_bnNumbers.checked then " -bonenumbers" else "") \
							 + (if chk_fbxMerge.checked then " -fbxmeshmerge" else "") \
							 + (" -noprompt") \
						)
						if chk_showCMD.checked then (
							DOSCommand ("\"" + cmd + "\"") 
						) else (
							HiddenDOSCommand ("\"" + cmd + "\"") startpath:(getFilenamePath noesis_path) donotwait:false
						)
						waitForFileUnlock(fbx_path)
						if showFbxOptions then (--chk_impPrompt
							success = importFile fbx_path using:FBXIMP
						) else (
							success = importFile fbx_path #noPrompt using:FBXIMP
						)
						if chk_delFBX.checked then 
							deleteFile fbx_path
						if force_backface_culling then 
							for obj in selection where (classof obj == Editable_mesh) do 
								obj.backfaceCull = on
						format "%\n" cmd
					) else (
						select old_obj
						copyNodes = #(); maxOps.cloneNodes selection cloneType:#copy newNodes:&copyNodes #nodialog
						select copyNodes
						success = true
					)
					
					if success and chk_bnNumbers.checked then (				
							
						with redraw off (
							local objSelected = selection as array
							if setCoords != undefined and not already_imported then
								names_to_objects.setK key objSelected 
								
							local meshes = for obj in objSelected where (classof obj == Editable_mesh) collect obj 
							local bones = for obj in objSelected where (superclassof obj == Helper or classof obj == BoneGeometry) collect obj 
							for bone in bones do hide bone
							container = Point size:1.0
							local uniqueNames = #(); local mainmeshes = #()
							container.name = key
							------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
							if setCoords != undefined then (
								if container.name != setCoords[1].Name then
									container.name = setCoords[1].Name + " (" + container.name + ")"
								print ("Loaded " + key + " " + (setCoords[2] as string))
								container.rotation = setCoords[2].LocalRotation
								container.scale = setCoords[2].LocalScale
								container.pos = setCoords[2].LocalPosition
								container.transform.controller.value *= (matrix3 [1,0,0] [0,0,1] [0,-1,0] [0,0,0])
								container.pos.controller.value *= 100
							)
							for mesh in meshes do ( -- create MainMesh containers
								fs = filterstring mesh.name "_"
								if appendIfUnique uniqueNames (fs[1] + "_" + fs[2] + "_" + fs[3] + "_" + fs[4]) then (
									mainmesh = Point size:1.0
									mainmesh.name = (fs[1] + "_" + fs[2] + "_" + fs[3] + "_" + fs[4])
									mainmesh.parent = container
									mainmesh.transform = container.transform
									append mainmeshes mainmesh
								)
								if setCoords != undefined then 
									mesh.transform = container.transform
								mesh.parent = mainmeshes[mainmeshes.count]
							)
							
							for mesh in meshes do (
								mesh.material = undefined
								mesh.wirecolor = color (random 0 255) (random 0 255) (random 0 255)
								if getNumVerts mesh == 3 or mesh.modifiers[#Skin] == undefined or already_imported then continue
								select mesh
								max modify mode
								mesh.modifiers[#Skin].bone_Limit = 8 
								for b = 1 to bones.count do (
									if b == 1 and setCoords != undefined then
										bones[b].transform = container.transform
									bones[b].showLinks = true
									bones[b].showLinksOnly = true
									bones[b].wirecolor = yellow
									fs = filterstring bones[b].name ":"
									if fs[2] != undefined then (
										if (getuserprop bones[b] "Bone_Number") == undefined do setuserprop bones[b] "Bone_Number" fs[1]
										if (getuserprop bones[b] "Bone_Name") == undefined do setuserprop bones[b] "Bone_Name" fs[2]
									)
									bnIdx = findBoneIdx mesh.modifiers[#Skin] bones[b].name
									if bnIdx == 0 then ( -- add bones to Skin that have numbers but are not currently in
										if fs.count > 1 then 
											skinOps.addBone mesh.modifiers[#Skin] bones[b] 0
									) else if fs.count == 1 then ( -- remove bones from Skin that have no numbers
										skinOps.selectbone mesh.modifiers[#Skin] bnIdx
										skinOps.removebone mesh.modifiers[#Skin]
									)
								)
							)
						)
					)
					chk_showPlugOpt.checked = false
				)
			) else print("Not found: " + cmd)
		)
		
		on formNoesisCMD open do (
			if doesFileExist (try(noesis_path)catch("")) do (
				edt_noesis.text = noesis_path
				)
			if doesFileExist (try(current_pak_location)catch("")) do (
				edt_scnpath.text = current_pak_location
				)
			)
			
		on btn_noesis pressed do (
			cmd = getOpenFileName types:"Noesis.exe|noesis.exe|All|*.*|"
			if cmd != undefined and cmd != "" do (
				edt_noesis.text = noesis_path = cmd
			)
		)
		
		on edt_noesis changed cmd do (
			edt_noesis.text = noesis_path = cmd
		)
		
		on btn_scnpath pressed do (
			cmd = getSavePath types:"re_chunk_000 Folder|Folder|All|*.*|"
			if cmd != undefined and cmd != "" do (
				edt_scnpath.text = current_pak_location = cmd
			)
		)
		
		on edt_scnpath changed cmd do (
			edt_scnpath.text = current_pak_location = cmd
		)
		
		on list_gameSelection selected i do (
			currentItem = gamesList[i]
			currentItemIdx = i
			lbl_currentExt.caption = case currentItem of 
				(
					"RE2 RT": ".mesh.2109108288"
					"RE3 RT": ".mesh.2109108288"
					"RE2": ".mesh.1808312334"
					"RE3": ".mesh.1902042334"
					"DMC5": ".mesh.1808282334"
					"RE7": ".mesh.32"
					"RE7 RT": ".mesh.220128762"
					"RE8": ".mesh.2101050001"
					"MHRise": ".mesh.2008058288"
					"MHRSunbreak": ".mesh.2109148288"
					default: ""
				)
			current_pak_location = case currentItem of 
				(
					"RE2 RT": re2rt_pak_location
					"RE3 RT": re3rt_pak_location
					"RE2": re2_pak_location
					"RE3": re3_pak_location
					"DMC5": dmc5_pak_location
					"RE7": re7_pak_location
					"RE7 RT": re7rt_pak_location
					"RE8": re8_pak_location
					"MHRise": mhrise_pak_location
					"MHRSunbreak": mhrise_pak_location
					default: ""
				)
			print current_pak_location 
			current_extension = replace lbl_currentExt.caption 1 5 ""
			edt_scnpath.text = current_pak_location
		)
		
		on list_gameSelection2 selected i do (
			currentItem2 = gamesList[i]
			currentItemIdx2 = i
			lbl_currentExt2.caption = case currentItem2 of 
				(
					"RE2 RT": ".mesh.2109108288"
					"RE3 RT": ".mesh.2109108288"
					"RE2": ".mesh.1808312334"
					"DMC5": ".mesh.1808282334"
					"RE3": ".mesh.1902042334"
					"RE7": ".mesh.32"
					"RE7 RT": ".mesh.220128762"
					"RE8": ".mesh.2101050001"
					"MHRise": ".mesh.2008058288"
					"MHRSunbreak": ".mesh.2109148288"
					default: ""
				)
			current_extension2 = replace lbl_currentExt2.caption 1 5 ""
		)
		
		on chk_reWrite changed state do (
			if chk_reWrite.checked == true and chk_writeBones.checked == false then
				chk_writeBones.checked = true
		)
		
		on chk_reWrite2 changed state do (
			if chk_reWrite2.checked then (
				if not chk_writeBones.checked then
					chk_writeBones.checked = true
				if not chk_reWrite.checked then
					chk_reWrite.checked = true
			)
		)
		
		on chk_writeBones changed state do (
			if chk_writeBones.checked == false and chk_reWrite.checked == true then
				chk_reWrite.checked = false
		)
		
		on btn_import_SCN pressed do ( 
			--if doesFileExist re2_pak_location then (
				if noesisComponentsFound() then (
					names_to_objects = losDic()
					files = #(getOpenFileName types:"All|*.*|")
					if files[1] != undefined then (
						actionMan.executeAction 0 "40472" --open listener
						if chk_folder.checked then
							files = getFiles (getFilenamePath files[1] + "\\*.scn.*") --import multiple SCN files from one folder
						for scnFile in files do (
							format "\n\nImporting % :\n\n" scnFile
							local f = fopen scnFile "rb"
							local Objects = findGameObjects f
							fclose f
							if Objects.count > 0 then (
								for obj in Objects do (
									Import_MESH obj[3] obj 
								)
							) else print "No Meshes detected"
						)
					)
					names_to_objects = undefined
					gc()
				) else (messagebox "Failed to Locate Noesis!")
			--) else messagebox "Failed to Locate Extracted Pak!"
		)
		
		/*
			--Dictionary example
			dic = losDic()  
			--set keys  
			dic.setK "pappa" 9999  
			--embeded dictonaries  
			dic.setK "powers" (losDic())  
			dic.setK "object" (sphere())  
			--set key in  the embeded dictionary  
			(dic.getK "powers").setK "lazerEyes" true  
			(dic.getK "powers").setK "bulletProof" true  
			--query the available keys  
			print "------keys------"  
			print (dic.keys())  
			print "----------------"  
			  
			--loop throug a dictionary  
			print "print keys and values"  
			for k in dic.keys() do format "%:%\n" k (dic.getK k)  
			  
			print "preaty print"  
			--prety print the dictionary  
			dic.pprint()  
		*/
		
		on btn_import pressed do (
			if noesisComponentsFound() then (
				cmd = getOpenFileName types:"RE Engine Model|*.1808282334;*.1902042334;*.2010231143;*.2008058288;*.2109148288;*.2109108288;*.2101050001;*.32;*.220128762;*.1808312334|All|*.*|"
				Import_MESH cmd undefined
			) else (messagebox "Failed to Locate Noesis!")
		)
		
		on btn_export pressed do (
			if noesisComponentsFound() then ( 
				cmd = ""
				if chk_reWrite.checked then (
					cmd  = case currentItem of (
						"RE2": getSaveFileName types:"RE2(*.1808312334)|*.1808312334|"
						"DMC5": getSaveFileName types:"DMC5(*.1808282334)|*.1808282334|"
						"RE3": getSaveFileName types:"RE3(*.1902042334)|*.1902042334|"
						"RE7": getSaveFileName types:"RE7(*.32)|*.32|"
						"RE7 RT": getSaveFileName types:"RE7 RT(*.220128762)|*.220128762|"
						"RE8": getSaveFileName types:"RE8(*.2101050001)|*.2101050001|"
						"MHRise": getSaveFileName types:"MHRise(*.2008058288)|*.2008058288|"
						"MHRSunbreak": getSaveFileName types:"MHRSunbreak(*.2109148288)|*.2109148288|"
						"RE2 RT": getSaveFileName types:"RT(*.2109108288)|*.2109108288|"
						"RE3 RT": getSaveFileName types:"RT(*.2109108288)|*.2109108288|"
						default: getSaveFileName types:" \
							DMC5(*.1808282334)|*.1808282334| \
							RE2(*.1808312334)|*.1808312334| \
							RE3(*.1902042334)|*.1902042334| \
							RE7(*.32)|*.32| \
							RE8(*.2101050001)|*.2101050001| \
							RE7 RT(*.220128762)|*.220128762| \
							RE2 RT(*.2109108288)|*.2109108288| \
							RE3 RT(*.2109108288)|*.2109108288| \
							MHRise(*.2008058288)|*.2008058288| \
							MHRSunbreak(*.2109148288)|*.2109148288|"
					) 
				) else
					cmd = getOpenFileName types:"RE Engine Model|*.1808282334;*.1902042334;*.2010231143;*.2008058288;*.2109148288;*.2109108288;*.2101050001;*.32;*.220128762;*.1808312334|All|*.*|"
					
				if cmd != undefined and cmd != "" then (
					fbx_path = (getFilenamePath cmd) + (getFilenameFile (getFilenameFile cmd)) + ".fbx"
					if chk_reWrite.checked then (
						lbl_currentExt.caption = ".mesh" + (getFilenameType cmd)
						out_path = (getFilenamePath cmd) + (getFilenameFile (getFilenameFile cmd)) + lbl_currentExt.caption
					) else
						out_path = (getFilenamePath cmd) + (getFilenameFile (getFilenameFile cmd)) + ".NEW.mesh" + (getFilenameType  cmd)
						
					if findString (toLower fbx_path) ".ORIG.fbx" != undefined then (
						newExtension = getFilenameType out_path
						meshPath = (replace fbx_path (findString (toLower fbx_path) "ORIG.fbx") 8 ("mesh" + newExtension))
						format "Changing file output from % to %\n" (getFilenameFile out_path) (getFilenameFile meshPath)
						out_path = meshPath
					)
					originalSelection = selection as array
					copyNodes = #()
					
					for obj in originalSelection where obj.modifiers[#Skin] != undefined do ( 
						try (
							selectSkeleton obj
							if chk_writeBones.checked then ( --Create dummy mesh with all bones in skin modifier so that FBX will save all bones
								maxOps.cloneNodes obj cloneType:#copy newNodes:&copyNodes #nodialog
								lastSelection = (selection as array); select copyNodes[1]; copyNodes[1].name = "FBXBoneStorage"
								for bn in lastSelection do 
									if superclassof bn == Helper or classof bn == BoneGeometry then 
										skinops.addBone copyNodes[1].modifiers[#Skin] bn 0
								selectmore lastSelection
							)
							exit
						) catch ( print "Could not select skeleton! Select bones manually before export" )
					)
					if chk_showPlugOpt.checked then (--chk_expPrompt
						exportFile fbx_path selectedOnly:true using:FBXEXP
					) else (
						exportFile fbx_path #noPrompt selectedOnly:true using:FBXEXP
					)
					if copyNodes[1] != undefined then delete copyNodes[1]
					if doesFileExist fbx_path do (

						waitForFileUnlock(fbx_path)
						cmd = (
							"\"" + noesis_path + "\" ?cmode \"" + fbx_path + "\" \"" + out_path + "\"" \
							+ (if chk_writeBones.checked then " -bones" else "") \
							+ (if not chk_flipHandedness.checked then " -flip" else "") \
							+ (if chk_bnNumbers.checked then " -bonenumbers" else "") \
							+ (if chk_reWrite.checked then " -rewrite" else (" -meshfile \"" + cmd + "\"")) \ 
						)
						
						if chk_showCMD.checked then 
							DOSCommand ("\"" + cmd + "\"")
						else 
							HiddenDOSCommand ("\"" + cmd + "\"") startpath:(getFilenamePath noesis_path) donotwait:false
						
						waitForFileUnlock(fbx_path)
						
						/*if chk_ReWrite2.checked then (
							local cmd2 = replace cmd (findString cmd lbl_currentExt.caption) lbl_currentExt.caption.count lbl_currentExt2.caption
							if chk_showCMD.checked then 
								DOSCommand ("\"" + cmd2 + "\"")
							else 
								HiddenDOSCommand ("\"" + cmd2 + "\"") startpath:(getFilenamePath noesis_path) donotwait:false
							
							waitForFileUnlock(fbx_path)
						)*/
						
						if chk_delFBX.checked do 
							deleteFile fbx_path
					)
					
					format "Command:\n%\n" cmd	
					if cmd2 != undefined then 
						format "Command2:\n%\n" cmd2
						
					
					select originalSelection
				)
			) else (messagebox "Failed to Locate Noesis!")
		)
		
		on btn_reimport pressed do (
			if true then ( --with redraw off (
				if noesisComponentsFound() then (
					if superclassof $ != GeometryClass then return false
					local cmd = reimport_path + "ReImportedMeshout.fbx"
					local newFile = cmd; 
					local origNode = $
					local fbx_path = reimport_path + "ReImportedMesh.fbx"
					local copyNodes = #(); maxOps.cloneNodes selection cloneType:#copy newNodes:&copyNodes #nodialog
					select copyNodes[1]; collapsestack $; $.name = origNode.name
					if chk_showPlugOpt.checked then (--chk_expPrompt
						if not (exportFile fbx_path selectedOnly:true using:FBXEXP) then format ("Failed to export %\n" fbx_path)
					)
					else (
						if not (exportFile fbx_path #noPrompt selectedOnly:true using:FBXEXP) then format ("Failed to export %\n" fbx_path)
					)
					if doesFileExist fbx_path do (
						waitForFileUnlock(fbx_path)
						cmd = (
							"\"" + noesis_path + "\" ?cmode \"" + fbx_path + "\" \"" + cmd + "\"" + " -noanims -notex -fbxmeshmerge"  -- + (if chk_noesisOpt.checked then " -RPGOptimize" else "")
						)
						if chk_showCMD.checked then (
							DOSCommand ("\"" + cmd + "\"")
						)
						else (
							HiddenDOSCommand ("\"" + cmd + "\"") startpath:(getFilenamePath noesis_path) donotwait:false
						)
						
						format "%\n" cmd
						waitForFileUnlock(fbx_path)
						waitForFileUnlock(newFile)
						local oldObj = objects as array
						
						if chk_showPlugOpt.checked then (
							if not (importFile newFile using:FBXIMP) then ( format "Failed to import %\n" newFile)
						) else ( if not (importFile newFile #noPrompt using:FBXIMP) then ( format "Failed to import %\n" newFile) )
						
						if chk_delFBX.checked do (
							deleteFile fbx_path
							deleteFile newFile
						)
						
						newObj = for o in objects where findItem oldObj o == 0 collect o
						for obj in newObj do (
							if superclassof obj == GeometryClass then 
								selectmore obj
							else delete obj
						)
						
						/*if origNode.modifiers[#Skin] != undefined then (
							collapsestack $
							addModifier $ (Skin_Wrap())
							skinWrap = $.modifiers["Skin_Wrap"]
							skinWrap.weightAllVerts = true
							skinWrap.falloff = 1.0
							skinWrap.Distance = 0.05
							skinWrap.meshList = #(origNode)
							skinWrap.convertToSkin false
							$.modifiers[#Skin].bone_Limit = 8
							deleteModifier $ $.modifiers["Skin_Wrap"]
						)*/
					)	
					delete copyNodes[1]
				) else (messagebox "Failed to Locate Noesis!")
			)
		)
		
		on BtnRemoveBoneNumbers pressed do (
			select selection[1]
			if not (classof $ == Editable_mesh and $.modifiers["Skin"] != undefined) then (
				messageBox "Select one (1) submesh with a Skin modifier"
				return false
			)
			with redraw off (
				local sourceMesh = $
				local skinBoneMapS = #()
				local sourceBones = collectSkinBones sourceMesh
				local bHasNumbers = false
				max modify mode
				theSkinS = sourceMesh.modifiers[#skin]
				if ( filterString (skinOps.GetBoneName theSkinS 1 0) ":")[2] != undefined then 
					bHasNumbers = true
				if bHasNumbers == true then ( --remove numbers
					for i = 1 to (skinOps.getnumberbones theSkinS) do (
						local boneName = skinOps.GetBoneName theSkinS i 0
						local bs = filterString boneName ":"
						if bs[2] == undefined then (bs[2] = getuserprop sourceBones[i] "Bone_Number")
						if bs[2] != undefined then (
							sourceBones[i].name = bs[2]
							append skinBoneMapS i
							if (getuserprop sourceBones[i] "Bone_Number") == undefined do setuserprop sourceBones[i] "Bone_Number" bs[1]
							if (getuserprop sourceBones[i] "Bone_Name") == undefined do setuserprop sourceBones[i] "Bone_Name" bs[2]
						)
					)
				) 
				else ( --restore numbers
					for b = 1 to (sourceBones.count) do (
						local BN = getuserprop sourceBones[b] "Bone_Number"
						local prop = getuserprop sourceBones[b] "Bone_Name"
						--if prop != undefined then ( sourceBones[b].name = prop )
						if BN != undefined then ( sourceBones[b].name = BN + ":" + sourceBones[b].name)
					)
				)		
			)
		)
		
		on BtnSkinOnTop pressed do (
			local meshes = for obj in (selection as array) where (classof obj == Editable_mesh) collect obj 
			with redraw off (
				for msh in meshes do (
					if classof msh.modifiers[1] == Skin then continue
					local theSkinArray = for i = msh.modifiers.count to 1 by -1 where classof msh.modifiers[i] == Skin collect #(i, msh.modifiers[i])
					skinUtils.ExtractSkinData msh
					local skinData = (maxOps.getNodeByHandle objects[objects.count].inode.handle)
					select msh
					selectmore skinData
					for modifier in theSkinArray do deleteModifier msh (modifier[1]) --delete all collected modifiers by index
					for modifier in theSkinArray do addModifier msh modifier[2] --add back all collected instances on top of the stack
					skinUtils.ImportSkinDataNoDialog true false false false false 0.01 0
					delete skinData
				)
			)
		)
		
		on FldScale entered num do (
			ScaleValue = try(num as float)catch(1.0)
			FldScale.text = ScaleValue as string
		)
		
		on BtnSetScale pressed do (
			local object = $
			if superclassof object == GeometryClass and object.modifiers[#skin] != undefined then (
				local bones = collectSkinBones object
				while bones[1].parent != undefined do
					bones[1] = bones[1].parent
				object = bones[1]
			)
			if (superclassof object == Helper or classof object == BoneGeometry) then (
				with undo on (
					local bone = object
					while bone.parent != undefined do bone = bone.parent
					local delta = (matrix3 [1,0,0][0,0,-1][0,1,0][0,0,0])--inverse bone.transform
					if ScaleValue == 1 then
						bone.transform = (matrix3 [1,0,0] [0,0,1] [0,-1,0] bone.pos)
					else bone.transform *= delta * (matrix3 [ScaleValue,0,0] [0,0,ScaleValue] [0,-ScaleValue,0] [0,0,0]) -- 
				)
			) else 
				messagebox "Select the root bone"
		)
		
		on BtnSetScale rightclick do (
			if ScaleValue == 1.0 then ScaleValue = 0.393701
			else if ScaleValue == 0.393701 then ScaleValue = 2.54
			else if ScaleValue == 2.54 then ScaleValue = 1.0
			FldScale.text = ScaleValue as string
		)
		
		on BtnAnimToBlender pressed do (
			objSelected = selection as array
			cmd = getSaveFileName types:"FBX animation|*.fbx|All|*.*|"
			if cmd != undefined then (
				dummy = mesh vertices:#([0,0,0],[0,0,0],[0,0,0]) faces:#([1,2,3])
				selectmore dummy
				selectmore objselected
				dummy.name = "dummy"
				dummySkin = Skin()
				addModifier dummy dummySkin
				max modify mode
				modPanel.setCurrentObject dummySkin
				for obj in objSelected do (
					if superclassof obj == Helper or superclassof obj == BoneGeometry then 
						skinops.addBone dummySkin obj 0
				)
				if cmd != undefined and cmd != "" do (
					fbx_path = (getFilenamePath cmd) + (getFilenameFile (getFilenameFile cmd)) + "_(Max).fbx"
					if chk_showPlugOpt.checked then (--chk_expPrompt
						exportFile fbx_path selectedOnly:true
					) else (
						exportFile fbx_path #noPrompt selectedOnly:true
					)
					if doesFileExist fbx_path do (
						waitForFileUnlock(fbx_path)
						cmd = (
							"\"" + noesis_path + "\" ?cmode \"" + fbx_path + "\" \"" + cmd + "\"" + " -notex"  -- + (if chk_noesisOpt.checked then " -RPGOptimize" else "")
						)
						if chk_showCMD.checked then (
							DOSCommand ("\"" + cmd + "\"")
						)
						else (
							HiddenDOSCommand ("\"" + cmd + "\"") startpath:(getFilenamePath noesis_path) donotwait:false
						)
						
						format "%\n" cmd
						waitForFileUnlock(fbx_path)
						if chk_delFBX.checked do
							deleteFile fbx_path
					)	
				)
				if chk_delFBX.checked do
					delete dummy
			)
			select objSelected
		)
	)
	createdialog formNoesisCMD
)