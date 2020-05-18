#!/bin/bash
int_list=("aha-mont64" "crc32" "edn" "huffbench" "matmult-int" "nettle-aes" "nettle-sha256" "nsichneu" "picojpeg" "qrduino" "sglib-combined")
float_list=("cubic" "minver" "nbody" "slre" "st" "statemate" "ud" "wikisort")
cur_dir=$(pwd)

cd ../bd/src/
for dir in ${int_list[*]}
do
    cd $dir
    for file in $(ls)
    do
        if [ -x $file ];then
            if [ $1 = debug ];then
                $cur_dir/qemu-system-loongson \
                -M ls3a-test \
                -kernel $file\
                -net nic \
                -serial stdio \
                -m 4096 \
                -s \
                -nographic \
                -monitor tcp::12351,server,nowait  \
                -smp 1 -d cpu,single -D $file.log 

                cat $file.log | python3 $cur_dir/trace_helper.py convert > golden_trace.txt
                rm $file.log
            else
                $cur_dir/qemu-system-loongson \
                -M ls3a-test \
                -kernel $file\
                -net nic \
                -serial stdio \
                -m 4096 \
                -s \
                -nographic \
                -monitor tcp::12351,server,nowait  \
                -smp 1
            fi
        fi
    done
    cd ..
done
