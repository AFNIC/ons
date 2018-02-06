#!/bin/bash

# Script used for the demo (DUMMY ONS ROOT - onseu.test, onsam.test, onsas.test) :
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

CMT_FILE="/var/www/cmt/cmt_demo.txt"
ONSEU_DB="./db.onseu-root-ons"
ONSAM_DB="./db.onsam-root-ons"
ONSAS_DB="./db.onsas-root-ons"

cd $(dirname $(readlink -f $0))

# Demo step by step 
case $STEP in

    1)  # step 1 : simple case OK + redirect onsas OK + malta KO
        cp $ONSEU_DB.default $ONSEU_DB # reset onseu zone file
        cp $ONSAS_DB.default $ONSAS_DB # reset onseu zone file
        cp $CMT_FILE.default $CMT_FILE # reset CMT
        ;;

    2)  # step 2 : Malta in european root OK; from others roots : KO 
        sed -i -e "s/^; 1.4.8.4.5.3.5.sgtin.id/1.4.8.4.5.3.5.sgtin.id/" $ONSEU_DB  
        ;;

    3)  # step 3 : sync CMT => Malta OK from all roots
        sed -i -e "s/^; 535/535/" $CMT_FILE # CMT : enable Malta prefix (535)
        ;;

    4)  # step 4 : move Malta to onsas Root 
        sed -i -e "s/^1.4.8.4.5.3.5.sgtin.id/; 1.4.8.4.5.3.5.sgtin.id/" $ONSEU_DB # remove from onseu
        sed -i -e "s/^; 1.4.8.4.5.3.5.sgtin.id/1.4.8.4.5.3.5.sgtin.id/" $ONSAS_DB # enable in onsas
        sed -i -e "s/^535/; 535/" $CMT_FILE # CMT : disable Malta prefix (535)
        ;;

    5)  # step 5 : sync CMT => Malta redirection OK for all roots 
        sed -i -e "s/^; 535:GS1 Malta:onseu.test/535:GS1 Malta:onsas.test/" $CMT_FILE # CMT : move Malta prefix to onsas root (535) 
        ;;

    *)
        ;;
esac 

# Update redirections
./update_redirections.sh $ONSEU_DB
./update_redirections.sh $ONSAM_DB
./update_redirections.sh $ONSAS_DB

# flush recursive server
rndc -s 2001:660:3003:6::7:133 flush

exit 0
