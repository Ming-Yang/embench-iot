/* Copyright (C) 2019 Clemson University

   Contributor Ola Jeppsson <ola.jeppsson@gmail.com>

   This file is part of Embench.

   SPDX-License-Identifier: GPL-3.0-or-later */

#include <support.h>
#include <time.h>
#include <stdio.h>

struct timespec time1, time2;
long long diff(struct timespec start, struct timespec end)
{
    struct timespec temp;
    if ((end.tv_nsec-start.tv_nsec)<0) {
        temp.tv_sec = end.tv_sec-start.tv_sec-1;
        temp.tv_nsec = 1000000000+end.tv_nsec-start.tv_nsec;
    } else {
        temp.tv_sec = end.tv_sec-start.tv_sec;
        temp.tv_nsec = end.tv_nsec-start.tv_nsec;
    }
    return temp.tv_sec*1000000000+temp.tv_nsec;
}

void
initialise_board ()
{
  __asm__ volatile ("nop" : : : "memory");
}

void __attribute__ ((noinline)) __attribute__ ((externally_visible))
start_trigger ()
{
  clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &time1);
}

void __attribute__ ((noinline)) __attribute__ ((externally_visible))
stop_trigger ()
{
  clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &time2);
  fprintf(stderr, "time %ldns\n", diff(time1, time2));
}
