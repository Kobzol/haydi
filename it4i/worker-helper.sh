#!/bin/bash

PROJECT_PATH=~/projects/haydi
PROJECT_PATH=$(cd ${PROJECT_PATH}; pwd)

source ${PROJECT_PATH}/it4i/env_init.sh

SRC_DIR=`dirname $0`/../src
PBS_O_WORKDIR=$1
export PYTHONPATH=${PBS_O_WORKDIR}:${SRC_DIR}:${PYTHONPATH}

workon pypy

for ((i=0; i < $2; i++))
{
    taskset -c ${i} dask-worker --nthreads=1 --nprocs=1 --no-nanny $3 &
}
