#!/bin/bash

if [ $# -eq 0 ]; then
        echo "usage: $0 <user>"
        exit 1
fi

if [ -z $1 ]; then
        echo "expecting username argument got null, usage: $0 <username> "
        exit 1
fi
user_name=$1
chage -l ${user_name}
