#!/bin/bash

# Script to synchronize the ons server with gs1 prefixes file
# This file have to be downloaded from a server
# The ons server is reload automatically
# See parameters below 

echo "DNAME update"

FILE_TO_GET="gs1.txt"
SERVER="http://telma/ons"

DB_ONS_PATH="/var/ons"
ONS_SCRIPT="/etc/ons/scripts/rc.d/onsctl"
FILE="gs1-prefixes.txt"

ONSNAME="onseu"
ONS="$ONSNAME.test"

# dowload the prefixes files
wget -q -nH $SERVER/$FILE_TO_GET
echo "Saved new gs1 prefixes file..."

if [ ! -f $FILE ]; then
    touch $FILE
    echo ';serial:0' >> $FILE
fi

# get the last serial and the new one 
SERIAL_NEW=`head -3 $FILE_TO_GET | grep ';serial' | cut -d ':' -f2`
SERIAL_OLD=`head -3 $FILE | grep ';serial' | cut -d ':' -f2`

# get the default ons server
DEFAULT_ONS=`head -3 $FILE_TO_GET | grep ';default' | cut -d ':' -f2`

# compare version and call dname generation script
if [ $SERIAL_NEW -gt $SERIAL_OLD ]; then
    echo "Proceeding..."

    # rename the files
    mv -f $FILE $FILE.old
    mv -f $FILE_TO_GET  $FILE

    # call the script with the right parameters (filename and ons names) 
    ./dname-gen.py $FILE $ONS $DEFAULT_ONS > $DB_ONS_PATH/$ONSNAME/db-dname.$ONS
    
    # reload ons server
    echo -n "$ONSNAME server : "
    # $ONS_SCRIPT reload $ONSNAME
    $ONS_SCRIPT restart 1>/dev/null && echo "Reload [ok]. Done." || echo "Reload [ko]"
else
    echo "Cancel... old or same version downloaded !"
    rm -f $FILE_TO_GET
fi
