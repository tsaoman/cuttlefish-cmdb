#!/bin/bash -ex

# run me from root's cron
# SCAN_DIR='/var/tmp/scans'
SCAN_DIR="/Users/$USER/desktop"
CMDB_URL='https://cephalapod.herokuapp.com'
PATH=$PATH:/usr/sbin:/sbin:/usr/local/bin

get_target_lan() {
  netstat -rn | grep default | egrep -v ':' | awk '{print $2}'
}

get_agent_ip() {
  ifconfig en0 | grep -w inet | awk '{print $2}'
}

get_agent_mac() {
  ifconfig en0 | grep -w ether| awk '{print $2}'
}

target_network=`get_target_lan`
agent_ip=`get_agent_ip`
agent_mac=`get_agent_mac`

mkdir -p $SCAN_DIR
if [ $# -eq 0 ]; then
  report_filename="$SCAN_DIR/nmap-${target_network}_`date +%Y-%m-%d_%H.%M.%S.`xml"
  nmap -O -sT -oX $report_filename $target_network/24
else
  report_filename=$1
fi
curl -o /dev/null $CMDB_URL/
sleep 10

attempts=0
MAX_ATTEMPTS=5
until curl -f -H "Expect:" -v -F agent_ip=${agent_ip} -F agent_mac=${agent_mac} -F file=@$report_filename ${CMDB_URL}/api/v1/agent/report; do
  sleep 30
  let attempts="$attempts + 1"
  if [ "$attempts" -gt 5 ]; then
    break
  fi
done
