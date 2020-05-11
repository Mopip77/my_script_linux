#!/bin/bash
##
# 快速切换路由器IP和DNS服务器到主路由或旁路由
# 脚本需要root权限
##

ROUTE_IP="192.168.2.1"
PROXY_IP="192.168.2.2"

CUR_IP="$(netstat -nr | awk '{if ($1 == "default"){print $2}}' | grep 192.168)"

main() {
    if [ "${CUR_IP}" = "${ROUTE_IP}" ] 
    then
        route change default ${PROXY_IP}
        networksetup -setdnsservers Wi-Fi ${PROXY_IP}

        osascript -e "display notification \"路由器IP与DNS:${PROXY_IP} \" with title \"更换路由器IP为旁路由\""
    elif [ "${CUR_IP}" = "${PROXY_IP}" ]
    then
        route change default ${ROUTE_IP}
        networksetup -setdnsservers Wi-Fi ${ROUTE_IP}

        osascript -e "display notification \"路由器IP与DNS:${ROUTE_IP} \" with title \"更换路由器IP为主路由\""
    else
        osascript -e "display notification \"当前路由器IP:${CUR_IP} 不在预备列表中\" with title \"更换路由器IP\""
    fi
}

main
