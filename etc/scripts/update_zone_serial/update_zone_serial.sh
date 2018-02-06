# Update ONS zone serial

ONS_ZONE_DB=$1

serial_token="; serial"
# get serial number
serial=$(grep "$serial_token" "$ONS_ZONE_DB" | awk '{print $1}')
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
sed -i -e "s/.*$serial_token.*/ $newserial $serial_token/" $ONS_ZONE_DB
