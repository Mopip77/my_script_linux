#!/usr/bin/env bash

##    直接播放先不写了...太难了...就直接复制一下算了
#
#     获取onedrive视频直链或直接播放, 强耦合了rclone, 所以需要传入和rclone一样的相对路径
#     并且这有一个坑, onedrive的直链带有感叹号!, 所以在url_transform()里需要用sed转义, 
#   并且在最后的mpv 地址需要echo出来, 而且不能加双引号
##

LINK_SAVE_FILE="${HOME}/.onedrive_direct_links.txt"
TMP_LINK_LIST_PREFIX="onedrive_direct_link_"

print_usage() {
    echo "[Usage] 
  onedirect [-option] command

[Command]
  show                  查看上次保存的某个目录的直链
  get                   弹出上次保存的某个目录的第一个直链
  path                  获取某个文件的直链
  -r path [re]          获取某个文件夹下所有直链并保存,可以使用正则匹配
	trans                 通过网页获得文件的共享链接可直接用trans转换成直链

直链格式为rclone的默认路径格式例如 one:/share/a.mkv
获取ondrive的视频直链, 会直接复制到剪贴板, 可用播放器直接播放"
}

url_transform() {

		# person onedrive
    # 传入
    # https://onedrive.live.com/redir?resid=6EB85EA240738233!2178&authkey=!AAjIornQjEBG8NA
    # 生成
    # https://storage.live.com/items/$[resid]?authkey=$[authkey]

		# busniess onedrive
		# 传入
		# https://swccd1-my.sharepoint.com/personal/mopip77_5tb_fun/_layouts/15/guestaccess.aspx\?share\=EWbVjempPgRAsHohbbdn6cgBfGtMPK3n6JYT7krZcgd0cQ\&cid\=d5fab802-0f98-4416-b52b-27f285063f10

		# 生成
		# https://swccd1-my.sharepoint.com/personal/mopip77_5tb_fun/_layouts/15/guestaccess.aspx\?share\=EWbVjempPgRAsHohbbdn6cgBfGtMPK3n6JYT7krZcgd0cQ\&cid\=d5fab802-0f98-4416-b52b-27f285063f10&download=1
		# 其中download = 1需要获得share地址后手动添加, 添加以后可以下载, 当然也可以直接播放

		if [[ "${1}" =~ "sharepoint" ]]
		then
			echo "${1}&download=1"
		else
			local params=`echo "${1}" | cut -d'?' -f2`
			local p1=`echo "${params}" | cut -d'&' -f1`
			local p2=`echo "${params}" | cut -d'&' -f2`
			if [ `echo ${p2} | cut -d'=' -f1` = "resid" ]
			then
					local temp="${p1}"
					p1="${p2}"
					p2="${temp}"
			fi
			local resid=`echo ${p1} | cut -d'=' -f2`
			local authkey=`echo ${p2} | cut -d'=' -f2`
			echo "https://storage.live.com/items/${resid}?authkey=${authkey}"
		fi
}

# 传入onedrive路径
get_real_path() {
    local share_link=$(rclone link "${1}")
    local playable_link=$(curl -s --head "$share_link" | grep location | awk '{print $2}')
    url_transform "${playable_link}"
}

if [ "$1" = "-h" ]
then
    print_usage
elif [ "$1" = "show" ]
then
    awk -F, '{printf("\033[36m%s\033[0m,%s\n\n", $1, $2)}' "${LINK_SAVE_FILE}"
    # cat ${onedirve_direct_links}
elif [ "$1" = "get" ]
then
    str=`head -n1 ${LINK_SAVE_FILE}` && sed -i '1d' ${LINK_SAVE_FILE}
    filename=`echo "${str}" | awk -F, '{print $1}'`
    link=`echo "${str}" | awk -F, '{print $2}'`
    echo -e "\033[36m[Name]\033[0m ${filename}\n\033[36m[Path]\033[0m ${link}"
    echo "${link}" | xclip -in -selection clipboard
elif [ "$1" = "trans" ]
then
    playable_link=$(curl -s --head "$1" | grep location | awk '{print $2}')
    url_transform "${playable_link}"
elif [ "$1" = "-r" ]
then
    # 如果没传入正则, 使用grep -E "" 也就是全匹配所以这里不做区分 $3为正则
    OLD_IFS="$IFS"
	IFS=$'\n'  # 换行
    filenames=($(rclone lsf "$2" | grep -E "$3"))
    IFS=$OLD_IFS

    prefix_path="${2}"
    [ "${prefix_path: -1}" != "/" ] && prefix_path="${prefix_path}/"
    
    [ -e ${LINK_SAVE_FILE} ] && rm ${LINK_SAVE_FILE}
    
    # 由于不会在并发下保存原有顺序, 所以获取和保存链接分开执行
    # 获取链接
    for idx in `seq 0 $((${#filenames[@]} - 1))`
    do
        {
            fn="${filenames[$idx]}"
            # 暂存在/dev/shm下, 减少磁盘的io
            get_real_path "${prefix_path}${fn}" > "/dev/shm/${TMP_LINK_LIST_PREFIX}${idx}"
            echo -e "\033[32m[Done]\033[0m ${fn}"
            # echo "${fn},${real_path[$i]}" >> ${LINK_SAVE_FILE}
        }&  # 多线程, 全部后台执行
    done
    wait

    # 保存连接
    for idx in `seq 0 $((${#filenames[@]} - 1))`
    do
        fn="${filenames[$idx]}"
        # real_path=cat "/dev/shm/${TMP_LINK_LIST_PREFIX}${idx}"
        echo "${fn},$(sudo cat /dev/shm/${TMP_LINK_LIST_PREFIX}${idx})" >> ${LINK_SAVE_FILE}
    done

    # delete tmp
    sudo rm /dev/shm/${TMP_LINK_LIST_PREFIX}*
else
    real_path="`get_real_path \"$1\"`"
    echo "${real_path}"
    echo "${real_path}" | xclip -in -selection clipboard
fi
