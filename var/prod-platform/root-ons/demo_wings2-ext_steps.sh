#!/bin/bash

# Script used for the demo (WINGS2-ext) :
#   - change settings for CMT or DB files 
#   - mandatory parameter : step number in demo (0, 1, 2...)

exec 1>/dev/null
exec 2>&1
STEP=$1

# Usage
if [ "$STEP" == "" ]
then
    echo "Usage : $0 [step-number]"
    exit 1
fi

CMT_FILE="/var/www/cmt/cmt_wings2-ext.txt"

# Demo step by step 
case $STEP in

    1)  # step 1 (reset) : simple case french product OK + redirect indian product + mexican product KO
        cp $CMT_FILE.default $CMT_FILE
        ;;

    2)  # step 2 : F-ONS synchronized, all redirections OK 
        sed -i -e "s/^; 750/750/" $CMT_FILE # CMT : enable mexico (750)
        ;;
    *)
        ;;
esac 

cd $(dirname $(readlink -f $0))
# Update redirections
./update_redirections.sh ./db.wings2-ext-fr-root-ons 
./update_redirections.sh ./db.wings2-ext-in-root-ons 
./update_redirections.sh ./db.wings2-ext-mx-root-ons

# flush recursive server
rndc -s 2001:660:3003:6::7:133 flush

exit 0
