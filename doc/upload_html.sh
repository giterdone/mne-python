#!/usr/bin/env bash

# scp -r build/html/* martinos:/web/html/mne/
rsync -rltvz --delete build/html/ martinos:/web/html/mne/ -essh
