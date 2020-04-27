/* Copyright (C) 2019 Clemson University

   Contributor Ola Jeppsson <ola.jeppsson@gmail.com>

   This file is part of Embench.

   SPDX-License-Identifier: GPL-3.0-or-later */

#include <support.h>
long long start_time = 0;
void
initialise_board ()
{

}

void __attribute__ ((noinline)) __attribute__ ((externally_visible))
start_trigger ()
{
   timer_start();
   start_time = get_count_my();
}

void __attribute__ ((noinline)) __attribute__ ((externally_visible))
stop_trigger ()
{
   long long counts = get_count_my();
   printf("counts:%ld\n", counts-start_time);
}
