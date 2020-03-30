#/bin/bash

## 保存在DIARY_DIR文件夹中，按【年/月】的文件夹结构来保存，即一个月的所有日记保存在一个文件夹中
## 日记文件以markdown格式保存，所有图片、视频、音乐资源放在同级文件夹的assets文件夹下

## 整体逻辑就是根据当天日期建立文件夹和日记文件，然后打开文件夹（方便转移静态资源）和日记文件
## Tips：可以看看markdown文件编辑器有没有自动移动图片的功能，可以设置自动复制到'./assets/'

## 使用 diary pack来将上个月的日记文件夹压缩成year-month-pack.zip，使用crontab在每个月1号来执行吧
## 0 12 1 * * diary pack

DIARY_DIR="/Users/mopip77/Desktop/onedrive/personal/diary"
SUB_PATH=$(date "+%Y/%m")
DIARY_FILE_NAME=$(date "+%Y-%m-%d.md")

real_dir="${DIARY_DIR}/${SUB_PATH}"
real_assets_dir="${real_dir}/assets"
real_diary_file="${real_dir}/${DIARY_FILE_NAME}"

if [ "$1" == "pack" ]; then
    # 压缩上个月的日记，获得上个月的年份和月份 (Macos 写法，macos的date方法和linux不同)
    # 该方法为上个月1号
    last_month_year=$(date -v1d -v-1m "+%Y")
    last_month_month=$(date -v1d -v-1m "+%m")
    last_month_dir="${DIARY_DIR}/${last_month_year}/${last_month_month}"
    [[ -d ${last_month_dir} ]] && zip -r "${last_month_year}-${last_month_month}-pack.zip" "${last_month_dir}"
else
    # 写日记
    [[ ! -d ${real_dir} ]] && mkdir -p ${real_dir}
    [[ ! -d ${real_assets_dir} ]] && mkdir -p ${real_assets_dir}
    [[ ! -f ${real_diary_file} ]] && touch ${real_diary_file}

    # Macos 中使用typora保存
    open -a Typora ${real_diary_file}
    open ${real_dir}
fi
