#!/bin/bash

# $1 = workdir
# $2 = worker count
# $3 = profile
# $4 = master

PROJECT_PATH=~/projects/haydi
PROJECT_PATH=$(cd ${PROJECT_PATH}; pwd)

source ${PROJECT_PATH}/it4i/env_init.sh

SRC_DIR=`dirname $0`/../src
PBS_O_WORKDIR=$1
export PYTHONPATH=${PBS_O_WORKDIR}:${SRC_DIR}:${PYTHONPATH}

workon pypy

for ((i=0; i < $2; i++))
{
    if [[ $3 == "1" ]]
    then
        python -m profile -o worker${i}.pstats `which dask-worker` --nthreads=1 --nprocs=1 --no-nanny $4 &
    else
        taskset -c ${i} dask-worker --nthreads=1 --nprocs=1 --no-nanny $4 &
    fi
}
