#! /bin/sh

busybox app >> /dev/ttySAK0
busybox reboot -f
