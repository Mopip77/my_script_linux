#!/bin/bash

H=$HOME

destFolderPath="$H/Desktop/configFiles"

if [ ! -d $destFolderPath ]
then
	mkdir $destFolderPath
fi

# 要备份的文件
files=(
"$H/.vimrc"
"$H/.zshrc"
"$H/.autokey"
"$H/.tmux.conf"
"$H/.myScript"
"$H/.config/mpv"
)

for file in ${files[*]}
do
	cp -r $file $destFolderPath
done

