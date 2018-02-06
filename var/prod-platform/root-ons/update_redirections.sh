#!/bin/bash

# Script to synchronize the ONS servers (according to the CMT).
# The CMT file has to be downloaded from a proper server.
# The serial of the ONS root zone is incremented automatically.
# The ONS server is reloaded automatically.

# Parameters 

if [ "$#" != "1" ] 
then
    echo "Usage : $0 <ons_root_zone_file>"
    exit 1
fi

# ONS zone file
ONS_ROOT_DB="$1"

# Redirections file
REDIRECT_FILE="$ONS_ROOT_DB.redirect"

# Load conf for this Root to retreive : 
# REMOTE_CMT, LOCAL_CMT, GS1_ID_TYPE, ONS_ROOT_ADDR, CURRENT_ONS_ROOT, REDIRECT_TYPE (DNAME)
. ./$REDIRECT_FILE.conf

#
#
echo "Update redirections for ONS Peer Root : $CURRENT_ONS_ROOT"

# Download the CMT (prefixes file)

echo "Downloading new Common Mapping Table (CMT) : $REMOTE_CMT"

wget -q $REMOTE_CMT -O $LOCAL_CMT

if [ ! -f $LOCAL_CMT ]
then
    echo "[ko]"
    echo "No CMT found. Update canceled !"
    exit 1
fi

# Generate the redirections
echo "Generating $REDIRECT_TYPE redirections..."

if [ -f $REDIRECT_FILE ]
then
    mv -f $REDIRECT_FILE $REDIRECT_FILE.old
fi

echo "; F-ONS redirections (from Common Mapping Table)" > $REDIRECT_FILE

# Check if current ONS Root is part of CMT
parse=0
while read line
do
    if [[ "$line" =~ ^([0-9]+)(-)?([0-9]+)?:(.*):(.*)$ ]] 
    then
        if  [[ "${BASH_REMATCH[5]}" == "$CURRENT_ONS_ROOT" ]]
        then
            parse=1
            break
        fi
    fi
done < $LOCAL_CMT

# Parse CMT lines in DNAME RR
[[ $parse -eq 1 ]] && while read line
do
    # if [[ "$line" =~ ^serial:(.*)$ ]] # get version of the CMT
    # then
    #    serial=${BASH_REMATCH[1]}
    #    continue 
    if [[ "$line" =~ ^([0-9]+)(-)?([0-9]+)?:(.*):(.*)$ ]] 
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
        
        if [[ "${BASH_REMATCH[5]}" != "" ]]
        then
            onsroot=${BASH_REMATCH[5]}
        else
            continue
        fi
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
            echo "$inverted_prefix.$GS1_ID_TYPE.id.$CURRENT_ONS_ROOT. DNAME $inverted_prefix.$GS1_ID_TYPE.id.$onsroot. ; $gs1_member ($prefix)" >> $REDIRECT_FILE
        elif [ "$REDIRECT_TYPE" = "NAPTR" ]
        then
            echo "*.$inverted_prefix.$GS1_ID_TYPE.id.$CURRENT_ONS_ROOT. NAPTR 0 0 \"\" \"\" \"!^urn:epc:id:([a-z]+):([0-9]+).([0-9]+)\$!\\\\3.\\\\2.\\\\1.id.$onsroot.!\" . ; $gs1_member ($prefix)" >> $REDIRECT_FILE
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
sed -i.old -e "s/.*$serial_token.*/ $newserial $serial_token/" $ONS_ROOT_DB


# Reload ONS server

echo -n "Reloading ONS server : "
/usr/sbin/rndc -s $ONS_ROOT_ADDR reload $CURRENT_ONS_ROOT

# Delete old files

if [ "$DELETE_OLD_FILES" = "YES" ]
then
    rm -f "$REDIRECT_FILE.old" "$ONS_ROOT_DB.old"
fi

exit 0
