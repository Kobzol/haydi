#!/usr/bin/env python

from __future__ import print_function

import argparse
import os
import subprocess
import time
import socket
import sys
import platform
import multiprocessing

from distributed import Client

PORT = 9010
HTTP_PORT = PORT + 1
CPUS = multiprocessing.cpu_count()


def count_workers(address):
    return sum(Client(address).ncores().values())


def get_nodes():
    with open(os.environ["PBS_NODEFILE"]) as f:
        return [line.strip() for line in f]


def get_program_path(name):
    return subprocess.Popen(["which", name],
                            stdout=subprocess.PIPE).communicate()[0].strip()


def is_scheduler_alive(address):
    try:
        Client(address)
        return True
    except IOError as e:
        return False


def main():
    print("PLATFORM: {}".format(platform.python_implementation()),
          file=sys.stderr)

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--profile",
                        action="store_true",
                        help="profile script and cluster")
    parser.add_argument("program")
    parser.add_argument("program_args",
                        nargs=argparse.REMAINDER,
                        default=[],
                        help="arguments for the launched program")

    args = parser.parse_args(os.environ["HAYDI_ARGS"].split(" "))
    program = args.program

    print("PROFILE: {}".format(args.profile), file=sys.stderr)

    # start scheduler
    hostname = socket.gethostname()
    master = "{}:{}".format(hostname, PORT)

    scheduler_args = []
    if args.profile:
        scheduler_args += ["python", "-m", "profile", "-o", "scheduler.pstats"]

    scheduler_args += [
        get_program_path("dask-scheduler"),
        "--port", str(PORT),
        "--http-port", str(HTTP_PORT)
    ]
    print("SCHEDULER: {}".format(" ".join(scheduler_args)), file=sys.stderr)
    subprocess.Popen(scheduler_args)

    while not is_scheduler_alive(master):
        time.sleep(1)

    # start workers
    dirname = os.path.dirname(os.path.abspath(__file__))

    nodes = get_nodes()
    total_worker_count = len(nodes) * CPUS - 1
    for i, node in enumerate(nodes):
        worker_count = CPUS - 1 if i == 0 else CPUS
        worker_args = [
            "ssh", node, "--",
            os.path.join(dirname, "worker-helper.sh"),
            os.environ["PBS_O_WORKDIR"],
            str(worker_count),
            "1" if args.profile else "0",
            master
        ]

        print("WORKER {}: {}".format(i, " ".join(worker_args)),
              file=sys.stderr)
        subprocess.Popen(worker_args, cwd=dirname)

    # wait for workers to connect
    while True:
        worker_count = count_workers(master)
        print("WORKER COUNT: {}".format(worker_count), file=sys.stderr)
        if worker_count == total_worker_count:
            break
        time.sleep(2)

    # start program
    popen_args = ["time", "-p"]

    if args.profile:
        popen_args += ["python", "-m", "profile", "-o", "script.pstats"]
    else:
        popen_args += ["python"]

    program = os.path.abspath(program)
    popen_args += [program, "--scheduler", hostname, "--port", str(PORT)]
    popen_args += args.program_args

    print("PROGRAM: {}".format(popen_args), file=sys.stderr)
    subprocess.Popen(popen_args, cwd=os.environ["PBS_O_WORKDIR"]).wait()


if __name__ == "__main__":
    main()
