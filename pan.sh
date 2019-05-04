#!/bin/bash
SCRIPT_PATH="/home/mopip77/Desktop/BaiduPCS-Go-v3.5.6-linux-amd64"
FILE_STORE_PATH="/我的资源/"
TMP_LIST_FILE="/tmp/baidu_pan.tmp"
DOWNLOAD_PATH="/home/mopip77/Desktop/BaiduPCS-Go-v3.5.6-linux-amd64/download/1131301918_Mopip77/apps/baidu_shurufa"

cd $SCRIPT_PATH
# 切换权限账号
./BaiduPCS-Go config set -appid=266719

if [[ $# -eq 1 && $1 == "del" ]]
then
	echo -e "\033[46;30m 使用rm命令删除文件\033[0m:"
  ./BaiduPCS-Go ls "$FILE_STORE_PATH"
  ./BaiduPCS-Go cd "$FILE_STORE_PATH"
	./BaiduPCS-Go
elif [[ $# -eq 1 && $1 == "bt" ]]
then
	# 磁力下载
	echo -e "\033[46;30m 输入磁力链接:\033[0m:"
	read btLink
	./BaiduPCS-Go od add -path=$FILE_STORE_PATH "$btLink"
	watch -n 3 ./BaiduPCS-Go ls "$FILE_STORE_PATH"
else
	# 下载
	./BaiduPCS-Go ls "$FILE_STORE_PATH" > $TMP_LIST_FILE 
  ./BaiduPCS-Go ls "$FILE_STORE_PATH"
	echo -e "\033[46;30m 输入文件(夹)编号下载: \033[0m"
  read dlCodes

	# 记录所有下载文件的名字
	index=0
	dlFileNames=()
	for i in ${dlCodes[*]}
	do
	  # 前五行无用, 也不用sed删了, 直接加一下吧
		let num=i+5
		# 由于会有名字中会有空格,直接用awk的print$5,会指定不全,所以要从5到fieldNum都打印
		fileName=($(cat $TMP_LIST_FILE | awk 'BEGIN{i=4}NR=="'$num'"{while(i++<NF) print $i}'))
		dlFileNames[$index]=`echo ${fileName[@]}`
		#fieldNum=$(cat $TMP_LIST_FILE | awk 'NR=="'$num'"{print NF}')
		#queryStr=""
		#for i in `seq 5 $fieldNum`;do queryStr="$queryStr\$$i,";done
		 #去掉queryStr最后的逗号
		#dlFileNames[$index]=$(cat $TMP_LIST_FILE | awk 'NR=="'$num'"{print ${queryStr:0:${#queryStr}-1}}')
		let index=index+1
	done

	echo $dlFileNames

	# 转移所有下载文件
	./BaiduPCS-Go cd $FILE_STORE_PATH
	for i in "${dlFileNames[@]}";do ./BaiduPCS-Go cp "$i" /apps/baidu_shurufa;done
	
  # 下载所有文件
  ./BaiduPCS-Go cd /apps/baidu_shurufa/
	./BaiduPCS-Go config set -appid=265486
	for i in "${dlFileNames[@]}";do ./BaiduPCS-Go d "$i";done

	# 删除要下载的文件(/app/baidu_shurufa文件夹下的)
	for i in "${dlFileNames[@]}";do ./BaiduPCS-Go rm "$i";done
	nemo $DOWNLOAD_PATH
fi
