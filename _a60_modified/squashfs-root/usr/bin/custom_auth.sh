#!/bin/sh
# Custom Authentication Handler for EN-818/EN-818T
# This script is called during authentication events

USER_ID=$1
AUTH_TYPE=$2  # finger, card, password
AUTH_RESULT=$3  # success, fail

LOG_FILE="/tmp/auth.log"
echo "$(date): User $USER_ID - $AUTH_TYPE - $AUTH_RESULT" >> $LOG_FILE

case $AUTH_RESULT in
    "success")
        echo "Access granted to user $USER_ID via $AUTH_TYPE" >> /dev/ttySAK0
        # Custom success actions here
        ;;
    "fail")
        echo "Access denied for user $USER_ID via $AUTH_TYPE" >> /dev/ttySAK0
        # Custom failure actions here
        ;;
esac

# Return result to main application
exit 0
