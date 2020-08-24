#!/usr/bin/env bash

##    直接播放先不写了...太难了...就直接复制一下算了
#
#     获取onedrive视频直链或直接播放, 强耦合了rclone, 所以需要传入和rclone一样的相对路径
#     并且这有一个坑, onedrive的直链带有感叹号!, 所以在url_transform()里需要用sed转义, 
#   并且在最后的mpv 地址需要echo出来, 而且不能加双引号
##

PLAYLIST_BASE_FOULDER="${HOME}/.local/onedirect/playlist"
TMP_LINK_LIST_PREFIX="onedrive_direct_link_"
PLAYABLE_EXT=".mp4|.mp3|.avi|.webm|.mkv"
# 剪贴板复制命令 mac下可使用pbcopy， Linux可用clipcopy，自己尝试更改
COPY_COMMAND="pbcopy" && [ `uname` != "Darwin" ] && COPY_COMMAND="clipcopy"

print_usage() {
    echo -e "该脚本在基础的获取onedrive直链功能上额外增加了一些扩展功能，并且可以和rclone配合使用

\033[32mCommand，接收参数类型分类\033[0m
rclone路径:
  pl                                      查看playlist
  dl [-r <regex>] [-p <playlist>] <path>  获取某个文件夹下所有直链并保存,可以使用正则匹配
  show [-p <playlist>]                    查看上次保存的某个目录的直链
  get [-p <playlist>]                     弹出上次保存的某个目录的第一个直链(show不会删除记录，get会)
  play [-d] [-p <playlist>]               直接播放，只会展示视频扩展名的文件，并且能自动识别对应字幕文件 (-d 删除原纪录)

onedrive分享链接 或 rclone路径:
  trans <path>                            转换成直链"
}

url_transform() {
        # 传入的url即从onedrive网页获取的云端文件“公开”共享url
		# person onedrive
        # 传入
        # https://onedrive.live.com/redir?resid=6EB85EA240738233!2198&authkey=!ADh1A_ee1OlrKpE&ithint=video%2cmp4&e=fdFK0W
        # 生成
        # https://storage.live.com/items/$[resid]?authkey=$[authkey]

		# busniess onedrive
		# 传入
		# https://swccd1-my.sharepoint.com/personal/mopip77_5tb_fun/_layouts/15/guestaccess.aspx\?share\=EWbVjempPgRAsHohbbdn6cgBfGtMPK3n6JYT7krZcgd0cQ\&cid\=d5fab802-0f98-4416-b52b-27f285063f10

		# 生成 (只需要在后面添加&download=1)
		# https://swccd1-my.sharepoint.com/personal/mopip77_5tb_fun/_layouts/15/guestaccess.aspx\?share\=EWbVjempPgRAsHohbbdn6cgBfGtMPK3n6JYT7krZcgd0cQ\&cid\=d5fab802-0f98-4416-b52b-27f285063f10&download=1
		# 其中download = 1需要获得share地址后手动添加, 添加以后可以下载, 当然也可以直接播放

		if [[ "${1}" =~ "sharepoint" ]]
		then
            # 现在rclone link获取的直链可能不带?e=xxxx,所以需要添加的不是&download=1而是?download=1
            if [[ "${1}" =~ "?" ]]
            then
			    echo "${1}&download=1"
            else
                echo "${1}?download=1"
            fi
		else
            # echo "url:$1"
            local playable_link=$(curl -s --head "$1" | grep location | awk '{print $2}')
            # echo "playable_link:${playable_link}"
			local params=`echo "${playable_link}" | cut -d'?' -f2`
			local p1=`echo "${params}" | cut -d'&' -f1`
			local p2=`echo "${params}" | cut -d'&' -f2`
			if [[ `echo ${p2} | cut -d'=' -f1` = "resid" ]]
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

get_real_path() {
    # 既可传入rclone的路径，也可传入onedrive分享链接(两者以是否为http开头区分)，最终返回直链
    share_link=${1}
    if [ "${1:0:4}" != "http" ]
    then 
        share_link=$(rclone link "${1}")
    fi
    playable_link=`url_transform "${share_link}"`
    echo ${playable_link}
}

exit_if_empty_string() {
    if [ -z $1 ]
    then
        exit 1
    fi
}

try_delete_file() {
    local filename="$1"
    if [[ -f ${filename} && -z `cat ${filename}` ]]
    then
        rm ${filename}
    fi
}


preprocess() {
    mkdir -p ${PLAYLIST_BASE_FOULDER}
}

download_func() {
    local onedrive_path="${@: -1}"
    exit_if_empty_string ${onedrive_path}
    local regex_expression=""
    while getopts "r:p:" opt; do
        case $opt in
            r)
                regex_expression="${OPTARG}"
            ;;
            p)
                playlist_name="${OPTARG}"
            ;;
        esac
    done

    # 如果没传入正则, 使用grep -E "" 即为全匹配
    OLD_IFS="$IFS"
    IFS=$'\n'  # 换行
    filenames=($(rclone lsf "${onedrive_path}" | grep -E "${regex_expression}"))
    IFS=$OLD_IFS
    
    [ "${onedrive_path: -1}" != "/" ] && onedrive_path="${onedrive_path}/"

    playlist_path="${PLAYLIST_BASE_FOULDER}/${playlist_name}"
    [ -e ${playlist_path} ] && rm ${playlist_path}

    # 由于不会在并发下保存原有顺序, 所以获取和保存链接分开执行
    # 获取链接
    for idx in `seq 0 $((${#filenames[@]} - 1))`
    do
        {
            fn="${filenames[$idx]}"
            # 暂存在/dev/shm下, 减少磁盘的io, mac没有，哎。。。
            get_real_path "${onedrive_path}${fn}" > "/tmp/${TMP_LINK_LIST_PREFIX}${idx}"
            echo -e "\033[32m[Done]\033[0m ${fn}"
        }&  # 多线程, 全部后台执行
    done
    wait

    # 保存连接
    for idx in `seq 0 $((${#filenames[@]} - 1))`
    do
        fn="${filenames[$idx]}"
        echo "${fn},$(cat /tmp/${TMP_LINK_LIST_PREFIX}${idx})" >> ${playlist_path}
    done

    # delete tmp
    rm /tmp/${TMP_LINK_LIST_PREFIX}*
}

show_func() {
    while getopts "p:" opt; do
        case $opt in
            p)
                playlist_name="${OPTARG}"
            ;;
        esac
    done
    local playlist_path="${PLAYLIST_BASE_FOULDER}/${playlist_name}"
    if [ ! -f ${playlist_path} ]
    then
        echo "该播放列表不存在"
        return
    fi

    awk -F, '{printf("\033[36m%s\033[0m,%s\n\n", $1, $2)}' "${playlist_path}"
}

get_func() {
    while getopts "p:" opt; do
        case $opt in
            p)
                playlist_name="${OPTARG}"
            ;;
        esac
    done
    playlist_path="${PLAYLIST_BASE_FOULDER}/${playlist_name}"
    if [ ! -f ${playlist_path} ]
    then
        echo "该播放列表不存在"
        return
    fi
    local str=`head -n1 ${playlist_path}`
    gsed -i '1d' ${playlist_path}
    local filename=${str%,*}
    local link=${str##*,}
    try_delete_file ${playlist_path}
    echo -e "\033[36m[Name]\033[0m ${filename}\n\033[36m[Path]\033[0m ${link}\n链接已复制到剪贴板, 可用播放器直接播放"
    echo "${link}" | `$COPY_COMMAND`
}

play_func() {
    local delete_after_play=false
    while getopts "dp:" opt; do
        case $opt in
            d)
                delete_after_play=true
            ;;
            p)
                playlist_name="${OPTARG}"
            ;;
        esac
    done

    local playlist_path="${PLAYLIST_BASE_FOULDER}/${playlist_name}"
    if [ ! -f ${playlist_path} ]
    then
        echo "该播放列表不存在"
        return
    fi

    # 用于先展示playlist_path文件，然后手动选择视频文件，并且会匹配出相应的字幕文件，播放后删除playlist_path的所选项以及其字幕文件
    # 行数
    ln=`cat  ${playlist_path} | grep -E ${PLAYABLE_EXT} | wc -l`
    # 显示可播放列表，用于选择
    OLD_IFS="$IFS"
    IFS=$'\n'
    for i in `cat ${playlist_path} | grep -E ${PLAYABLE_EXT} | awk -F, '{print "\033[32m["NR"]\033[0m" " " $1}'`; do
        echo -e "${i}"
    done
    IFS=$OLD_IFS
    echo -e "\n请输入需要播放的视频序号："
    read line_num
    if [[ ${line_num} -gt 0 && ${line_num} -le ${ln} ]]
    then
        # 删除原有播放记录标志，必须在item赋值前清楚，否则无法找到对应的字幕匹配项
        gsed -i -e 's/\\033\[31m\[\*\]\\033\[0m//g' ${playlist_path}
        item=`cat ${playlist_path} | grep -E ${PLAYABLE_EXT} | gsed -n "${line_num}p"`
        vn_full=`echo ${item} | awk -F, '{print $1}'`
        video_url=`echo ${item} | awk -F, '{print $2}'`
        # 视频名，不带扩展名
        vn=${vn_full%.*}
        subtitle_args=`cat ${playlist_path} | awk -F, -v vn_full="${vn_full}" -v vn="${vn}" -v vnc=${#vn} '{if ($1 != vn_full && substr($1, 1, vnc) == vn) print "--sub-file="$2}'`
        if [ ${delete_after_play} == true ]
        then
            gsed -i "/^${vn}/d" ${playlist_path}
            try_delete_file ${playlist_path}
        else
            # 标记最后一次播放的视频，由于之前输入的行数是筛选过后的，所以和真实行数不匹配，只能用视频全名来匹配，并且使用@分隔，防止视频名出现/
            gsed -i -e 's@^'"${vn_full}"'@\\033[31m[*]\\033[0m'"${vn_full}"'@' ${playlist_path}
        fi
        mpv ${video_url} ${subtitle_args}
    else
        echo "所选文件超出范围"
    fi
}

main() {
    playlist_name="default"
    case $1 in
    pl)
        # 查看playlist
        ls ${PLAYLIST_BASE_FOULDER} | while read playlist; do
            playlist_path="${PLAYLIST_BASE_FOULDER}/${playlist}"
            item_count=`cat ${playlist_path} | wc -l`
            echo -e "\033[32m${playlist}${item_count}项\033[0m"

            OLD_IFS="$IFS"
            IFS=$'\n'  # 换行
            for item in `cat ${playlist_path}`; do
                echo -e "  ${item%,*}"
            done
            IFS=$OLD_IFS
            echo ""
        done
    ;;
    dl)
        download_func "${@:2}"
    ;;
    show)
        show_func "${@:2}"
    ;;
    get)
        get_func "${@:2}"
    ;;
    play)
        play_func "${@:2}"
    ;;
    trans)
        playable_link=`get_real_path "${2}"`
        echo -e "${playable_link}\n链接已复制到剪贴板, 可用播放器直接播放"
        echo "${playable_link}" | `$COPY_COMMAND`
    ;;
    *)
        print_usage
    ;;
    esac
}

preprocess
main "$@"
