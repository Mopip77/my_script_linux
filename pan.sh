#!/bin/bash
SCRIPT_PATH="/home/mopip77/Desktop/BaiduPCS-Go-v3.5.6-linux-amd64"
FILE_STORE_PATH="/我的资源/"

cd $SCRIPT_PATH
./BaiduPCS-Go config set -appid=266719

if [[ $# -eq 1 && $1 == "del" ]]
then
	echo -e "\033[46;30m 使用rm命令删除文件\033[0m:"
  ./BaiduPCS-Go ls "$FILE_STORE_PATH"
  ./BaiduPCS-Go cd "$FILE_STORE_PATH"
	./BaiduPCS-Go
else
  #需要确定指定文件是否存在
  allFile=$(./BaiduPCS-Go ls "$FILE_STORE_PATH" ) 
  ./BaiduPCS-Go ls "$FILE_STORE_PATH"
  echo -e "\033[46;30m 输入文件名下载: \033[0m"
  read curFile
  if [[ !($allFile =~ $curFile) ]]; then
    echo -e "\033[46;30m 发生错误，检查【${FILE_STORE_PATH:1:-1}】文件夹下是否有指定文件 \033[0m"
  else
    ./BaiduPCS-Go cp "$FILE_STORE_PATH$curFile" /apps/baidu_shurufa/
    ./BaiduPCS-Go cd /apps/baidu_shurufa/
    ./BaiduPCS-Go config set -appid=265486
    ./BaiduPCS-Go d $curFile
    exo-open --launch FileManager '/home/mopip77/Desktop/BaiduPCS-Go-v3.5.6-linux-amd64/download/1131301918_Mopip77/apps/baidu_shurufa'
  fi
fi
