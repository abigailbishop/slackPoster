# slackPoster

This code is essentially copied and pasted from the wonderful Michel Zingale. His respository is available here: https://github.com/zingale/lazy-astroph

How it works:
In each directory is a copy of the code, a file containing the keyword inputs, and a file called "webhook" (which is git ignored because Slack says the link should be kept secret).
In this main directory is a shell script that will remove the parameter file created by the code, then run each code in turn. 
