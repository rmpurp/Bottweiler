#!/bin/bash

until python3.6 bot.py; do
    echo "Bot crashed.............. responding."
    sleep 1
done
