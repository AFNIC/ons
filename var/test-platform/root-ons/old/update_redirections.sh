#!/bin/bash

# Script to synchronize the ONS servers (according to the CMT).
# The CMT file has to be downloaded from a proper server.
# The serial of the ONS root zone is incremented automatically.
# The ONS server is reloaded automatically.

####### Parameters 

if [ "$1" != "onseu.test" ] && [ "$1" != "onsam.test" ] && [ "$1" != "onsas.test" ]
then
    echo "Usage : $0 [onseu.test|onsam.test|onsas.test]"
    exit 1
fi

if [ "$1" == "onseu.test" ]
then
    ONS_ROOT_DB="db.onseu-root-ons"
fi

if [ "$1" == "onsam.test" ]
then
    ONS_ROOT_DB="db.onsam-root-ons"
fi

if [ "$1" == "onsas.test" ]
then
    ONS_ROOT_DB="db.onsas-root-ons"
fi

# URL Of the CMT
REMOTE_CMT="http://ons.rd.nic.fr/cmt/cmt.txt"

# Local filename of the downloaded CMT
LOCAL_CMT="cmt.txt"

# Backup of modified files
DELETE_OLD_FILES="NO"

# ONS Peer Root managed
CURRENT_ONS_ROOT="$1"

# IP of ONS server
ONS_ROOT_ADDR="192.134.7.134"

# Redirections file
REDIRECT_FILE="$ONS_ROOT_DB.redirect"

REDIRECT_TYPE=DNAME
# REDIRECT_TYPE=NAPTR
####### End Parameters 


#
#
#
echo "Update redirections for ONS Peer Root : $CURRENT_ONS_ROOT"

# Download the CMT (prefixes file)

if [ -f $LOCAL_CMT ];
then
    mv -f $LOCAL_CMT "$LOCAL_CMT.old"
fi

echo "Downloading new Common Mapping Table (CMT) : $REMOTE_CMT"

wget -q "$REMOTE_CMT" -O $LOCAL_CMT

if [ ! -f $LOCAL_CMT ]; then
    echo "[ko]"
    echo "No CMT found. Update canceled !"
    exit 1
fi

# Generate the redirections
echo "Generating $REDIRECT_TYPE redirections..."

if [ -f $REDIRECT_FILE ];
then
    mv -f $REDIRECT_FILE "$REDIRECT_FILE.old"
fi

echo "; F-ONS redirections (from Common Mapping Table)" > $REDIRECT_FILE

# Parse CMT lines in DNAME RR
while read line
do
    if [[ "$line" =~ ^default_ons_root:(.*)$ ]] # get default root
    then
        default_ons_root=${BASH_REMATCH[1]}
        continue
    elif [[ "$line" =~ ^serial:(.*)$ ]] # get version of the CMT
    then
        serial=${BASH_REMATCH[1]}
        continue 
    elif [[ "$line" =~ ^([0-9]+)(-)?([0-9]+)?:(.*):(.*)$ ]] 
    then
        # CMT line format is 'prefix1-prefixN:MO_name:onsroot_name'
        gs1_prefix1=${BASH_REMATCH[1]}
        if [ "${BASH_REMATCH[3]}" != "" ]
        then
            gs1_prefix2=${BASH_REMATCH[3]}
        else
            gs1_prefix2=$gs1_prefix1
        fi
        gs1_member=${BASH_REMATCH[4]}
        onsroot=${BASH_REMATCH[5]}
    else
        continue
    fi

    if [ "$onsroot" == "_default" ]
    then
        if [ "$default_ons_root" == "" ] 
        then
            # continue if no default root is defined for non assigned prefixes
            continue    
        else
            onsroot=$default_ons_root          
        fi
    fi

    if [ "$CURRENT_ONS_ROOT" = "$onsroot" ]
    then
        continue
    fi

    index1=`expr $gs1_prefix1 + 0`
    index2=`expr $gs1_prefix2 + 0`

    for (( i=$index1; i<=$index2; i++ ))
    do
        prefix=$i
            
        if [ $i -lt 10 ]
        then
            prefix="00$prefix"
        elif [ $i -lt 100 ]
        then
            prefix="0$prefix"
        fi

        inverted_prefix=${prefix:2:1}.${prefix:1:1}.${prefix:0:1} # invert prefix

        # write DNAME or NAPTR in the zone file
        if [ "$REDIRECT_TYPE" = "DNAME" ]
        then 
            echo "$inverted_prefix.sgtin.id.$CURRENT_ONS_ROOT. DNAME $inverted_prefix.sgtin.id.$onsroot. ; $gs1_member ($prefix)" >> $REDIRECT_FILE
        elif [ "$REDIRECT_TYPE" = "NAPTR" ]
        then
            echo "*.$inverted_prefix.sgtin.id.$CURRENT_ONS_ROOT. NAPTR 0 0 \"\" \"\" \"!^urn:epc:id:([a-z]+):([0-9]+).([0-9]+)\$!\\\\3.\\\\2.\\\\1.id.$onsroot.!\" . ; $gs1_member ($prefix)" >> $REDIRECT_FILE
        fi
    done
done < $LOCAL_CMT


# Update ONS zone serial

serial_token="; serial"
# get serial number
serial=$(grep "$serial_token" "$ONS_ROOT_DB" | awk '{print $1}')
# get serial number's date
serialdate=$(echo $serial | cut -b 1-8)
# get today's date in same style
date=$(date +%Y%m%d)
# compare date and serial date
if [ $serialdate = $date ]
then
    # if equal, just add 1
    newserial=$(expr $serial + 1)
else
    # if not equal, make a new one and add 00
    newserial=$(echo $date"00")
fi

# edit zonefile in place, leaving a backup (.old)
# sed -i.old -e "s/.*$serial_token.*/ $newserial $serial_token/" $ONS_ROOT_DB # Prod Option


# Reload ONS server

echo -n "Reloading ONS server : "
/usr/sbin/rndc -s $ONS_ROOT_ADDR reload $CURRENT_ONS_ROOT

# Delete old files

if [ "$DELETE_OLD_FILES" = "YES" ]
then
    rm -f "$LOCAL_CMT.old" "$REDIRECT_FILE.old" "$ONS_ROOT_DB.old"
fi

exit 0
