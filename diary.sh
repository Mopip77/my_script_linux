## 整体逻辑就是根据当天日期建立文件夹和日记文件，然后打开文件夹（方便转移静态资源）和日记文件
## Tips：可以看看markdown文件编辑器有没有自动移动图片的功能，可以设置自动复制到'./assets/'

DIARY_DIR="/Users/mopip77/Desktop/onedrive/personal/diary"
SUB_PATH=$(date "+%Y/%m")
DIARY_FILE_NAME=$(date "+%Y-%m-%d.md")

real_dir="${DIARY_DIR}/${SUB_PATH}"
real_assets_dir="${real_dir}/assets"
real_diary_file="${real_dir}/${DIARY_FILE_NAME}"

[[ ! -d ${real_dir} ]] && mkdir -p ${real_dir}
[[ ! -d ${real_assets_dir} ]] && mkdir -p ${real_assets_dir}
[[ ! -f ${real_diary_file} ]] && touch ${real_diary_file}

# Macos 中使用typora保存
open -a Typora ${real_diary_file}
open ${real_dir}
