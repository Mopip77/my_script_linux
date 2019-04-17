#!/bin/bash

registerExcute(){
    echo -e "#\!/bin/sh\n${py3Path} ${rootPath}/src/run.py \$1" > cron
    chmod 755 cron
    sudo mv cron /usr/bin/backupThem
}

registerCrontab(){
    crontab -l >> conc && \
    echo "0 13,19 * * * ${py3Path} ${rootPath}/src/run.py run" >> conc && \
    crontab conc && \
    rm conc
    echo "添加自动执行任务成功, 每日13点和19点整点自动备份, 也可通过crontab自行修改"
}

setDefaultDestPath(){
    local flag

    while true;
    do
        echo "请输入默认文件夹备份根路径:"
        read defaultDestPath
        if [ -e $defaultDestPath ]
        then
            echo "路径已存在,是否清空并使用?[y/N]"
            read flag
            if [ "$flag" = 'y' ]
            then
                rm -rf "${defaultDestPath}"
                break
            fi
        else
            break
        fi
    done
    mkdir -p "$defaultDestPath"
}

setDefaultTrashPath(){
    defaultTrashPath="${defaultDestPath}/_cycle_"
    local settingTrashPath
    local flag

    while true;
    do
        echo -e "请输入默认回收站路径\n留空则置于[${defaultTrashPath}]:"
        read settingTrashPath
        if [ -z $settingTrashPath ]
        then
            break
        elif [ -e $settingTrashPath ]
        then
            echo "路径已存在,是否清空并使用?[y/N]"
            read flag
            if [ "$flag" = 'y' ]
            then
                rm -rf "${settingTrashPath}"
                defaultTrashPath=${settingTrashPath}
                break
            fi
        else
            defaultTrashPath=${settingTrashPath}
            break
        fi
    done
    mkdir -p "$defaultTrashPath"
}

setConfig(){
    echo  "DATETIME_PATTERN: \"%Y-%m-%d_%H:%M:%S\"
DEFAULT_DESTPATH: ${defaultDestPath}
TRASH_FOLDER_PATH: ${defaultTrashPath}
EXPIRED_PERIOD: 604800 # 60 * 60 * 24 * 7" > "${rootPath}/config.yaml"

    echo "" > "${rootPath}/folder_reference.txt"
}

# start installation

py3Path=`which python3`

if [ "$py3Path" = '' ]
then 
    echo "python3不存在,无法执行"
    exit 1 
fi

usr=`env | grep USER | cut -d "=" -f 2`
if [ $usr = "root" ]
then
    echo "不能使用sudo权限"
    exit 1
fi

rootPath=$(cd `dirname $0`; pwd)
existJob=`crontab -l`

if [[ "${existJob}" =~ "${rootPath}/src/run.py" ]]
then
    echo "任务已存在,不再重复安装"
    exit 0
else

    setDefaultDestPath
    setDefaultTrashPath
    # deploy config and component
    sudo cp "${rootPath}/notify-cron.sh" /usr/bin/notify-cron
    setConfig

    registerExcute
    registerCrontab

    echo "安装成功, 使用 backupThem -h 看看如何使用"
fi


