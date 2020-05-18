#!/bin/bash

./qemu-system-loongson \
            -M ls3a-test \
            -kernel $1\
            -net nic \
            -serial stdio \
            -m 4096 \
            -s \
            -nographic \
            -monitor tcp::12351,server,nowait  \
            -smp 1 -d cpu,single -D qemu.log 