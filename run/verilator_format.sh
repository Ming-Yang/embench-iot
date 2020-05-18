#!/bin/bash

OBJCOPY=loongisa-linux-gnu-objcopy
OBJDUMP=loongisa-linux-gnu-objdump
int_list=("aha-mont64" "crc32" "edn" "huffbench" "matmult-int" "nettle-aes" "nettle-sha256" "nsichneu" "picojpeg" "qrduino" "sglib-combined")
float_list=("cubic" "minver" "nbody" "slre" "st" "statemate" "ud" "wikisort")
cur_dir=$(pwd)

# gcc -o convert convert_double.c
cd ../bd/src/

if [ $1=build ];then
    for dir in ${int_list[*]}
    do
        cd $dir
        for file in $(ls)
        do
            if [ -x $file ];then
                # $OBJCOPY -O binary -j .text -j .rodata $file axi_ram_text.elf
                # $OBJCOPY -O binary -j .data $file axi_ram_data.elf
                $OBJDUMP -alD $file > godson_test.s
            fi
        done
        python3 $cur_dir/trace_helper.py dump -p . --align 3
        # $cur_dir"/convert" axi_ram_text.elf axi_ram_data.elf
        rm *.elf *.o
        cd ..
    done
fi

zip -r $cur_dir/embench_int.zip ${int_list[*]}



