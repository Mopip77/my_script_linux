#!/bin/bash

###############################################################
##               自动同步转码程序                               ##
##                                                           ##
##  对于高码率的文件（例如flac和wav格式的音频进行转码）             ##
##  并在对应的转码文件夹下创建完全一样的文件夹结构                   ##
##                                                           ##
###############################################################

ROOT_PATH="/Users/bjhl/gogo"          # 音乐文件夹
ENCODE_PATH="/Users/bjhl/encode"      # 转码后的文件夹，可以不存在
SUPPORT_TRANSCODE_EXT=(flac wav)
COPY_EXT=(jpeg jpg png)

checkSupportExt() {
	local type="$1"
	for supportType in ${SUPPORT_TRANSCODE_EXT[@]}; do
		[ "${supportType}" = "${type}" ] && exit 0
	done

	exit 1
}

checkCopyExt() {
	local type="$1"
	for supportType in ${COPY_EXIT[@]}; do
		[ "${supportType}" = "${type}" ] && exit 0
	done

	exit 1
}

encode() {
	local sourceFile="$1"
	local targetFolder="$2"
	local fileName="$3"
	local targetFile="${targetFolder}/${fileName}.aac"
	if [ -f "${targetFile}" ]; then
		echo "[file exists skipping...] ${targetFile}"
		return 0
	fi

	echo "transcoding from [${sourceFile}] to [${targetFolder}]"
	ffmpeg -n -v error -i "${sourceFile}" -ar 44100 -ac 2 -ab 320k "${targetFile}"
}

sync() {
	# 当前文件夹路径
	local folderPath="$1"
	local targetPath="$2"

	if [ ! -d "${targetPath}" ]; then
		echo "mkdir: ${targetPath}"
		mkdir "${targetPath}"
	fi

	OLD_IFS="$IFS"
	IFS=$'\n'
	for f in `ls "${folderPath}"`; do
		# 当前文件
		local file="${folderPath}/${f}"

		[ -L "${file}" ] && continue  # 如果是链接文件直接过滤，怕有死循环
		[ -d "${file}" ] && sync "${file}" "${targetPath}/${f}"
		if [ -f "${file}" ]; then
			local ext="${file##*.}"
			local fn="${f%.*}"
			if `checkSupportExt "${ext}"`; then
				encode "${file}" "${targetPath}" "${fn}"
			elif `checkCopyExt "${ext}"`; then
				echo "[copy file] ${file}"
				cp "${file}" "${targetPath}/${f}"
			else
				echo "[ext not support] ${file}"
			fi
		fi
	done
	IFS=$OLD_IFS
}

folderPrepare() {
	if [[ "${ENCODE_PATH}" =~ "${ROOT_PATH}" ]]; then
		echo "不可以套娃哦！"
		exit 0
	fi

	if [ ! -d "${ROOT_PATH}" ]; then
		echo "您的原文件夹呢？"
		exit 0
	fi

	if [ ! -d "${ENCODE_PATH}" ]; then
		mkdir -p "${ENCODE_PATH}"
	fi
}

main() {
	folderPrepare "${ROOT_PATH}" "${ENCODE_PATH}"
	sync "${ROOT_PATH}" "${ENCODE_PATH}"
}

main
