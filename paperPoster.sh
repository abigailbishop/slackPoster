#!/bin/bash

path="/Users/abigailbishop/Documents/GradSchool/Slack/slackPoster/lazy-astroph-"
list='astroph hep wipac'

for i in $list; do
    rm /Users/abigailbishop/.lazy_astroph
    $path$i/lazy_astroph.py -w $path$i/webhook $path$i/inputs
done
