py3Path=`which python3`

if [ "$py3Path" = '' ]
then 
    echo "python3不存在,无法执行"
    exit 1 
fi

rootPath=$(cd `dirname $0`; pwd)

existJob=`crontab -l`

if [[ "$existJob" =~ "${rootPath}/run.py" ]]
then
    echo "任务已存在,不再重复安装"
    exit 1
else
    crontab -l >> conf && \
    echo "* 19 * * * ${py3Path} ${rootPath}/run.py run" >> conf && \
    crontab conf && \
    rm conf
    echo "安装成功, 每日19点自动备份, 也可通过crontab自行修改"
fi
