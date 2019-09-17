#!/bin/bash

command=`cat command_input.txt`
echo "================= Running 1 Anura measurement ================="
yes "server=qa" | head -n 1 | xargs -i -P 1 python measure.py ${command}1 --{}
# echo "================= Running 10 Anura measurements ================="
yes "server=qa" | head -n 10 | xargs -i -P 10 python measure.py ${command}10 --{}
# echo "================= Running 30 Anura measurements ================="
yes "server=qa" | head -n 30 | xargs -i -P 30 python measure.py ${command}30 --{}

# echo "================= SENDING TEST REPORT EMAIL ================="
CURRENTDATE=`date +%d-%b-%Y`
mpack -s Worker-Test-Report_${CURRENTDATE} Test_Report_* daphnezhou@nuralogix.ai,HiradKarimi@nuralogix.ai
# echo "================= EMAIL SENT ================="
