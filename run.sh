#!/bin/sh

uptime -m api &
uptime -m server &

wait
