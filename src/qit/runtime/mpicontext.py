from context import ParallelContext
from qit.iterator import Iterator
from qit.session import session
from qit.transform import JoinTransformation, SplitTransformation


MpiRun = True

try:
    from mpi4py import MPI

    if MPI.COMM_WORLD.Get_size() < 2:
        raise Exception()
except:
    MpiRun = False


class MpiWorker(object):
    def __init__(self, size, rank):
        self.size = size
        self.rank = rank
        self.comm = MPI.COMM_WORLD
        session.set_worker(self)

    def run(self):
        while True:
            status = MPI.Status()
            msg = self.comm.recv(source=MPI.ANY_SOURCE,
                                 tag=MPI.ANY_TAG, status=status)
            print(msg)

    def post_message(self, msg):
        # send to master
        self.comm.send(msg, 0, tag=MpiTag.NOTIFICATION_MESSAGE)


class MpiTag(object):
    NOTIFICATION_MESSAGE = 100

    ITERATOR_ITEM = 200
    ITERATOR_STOP = 201

    NODE_JOB_REQUEST = 400
    NODE_JOB_OFFER = 401

    ITERATOR_REGION_START = 1000


class NodeGraph(object):
    def __init__(self, size):
        self.size = size
        self.iterator_regions = []
        self.available_node = 1
        self.jobs = {}

    def assign_job(self, node, iterator):
        self.jobs[node] = iterator

    def get_available_node(self):
        assert self.available_node < self.size

        node = self.available_node
        self.available_node += 1

        return node

    def get_iterator(self, node):
        if node in self.jobs:
            return self.jobs[node]
        else:
            return []


class MpiIterator(Iterator):
    def __init__(self):
        super(MpiIterator, self).__init__()
        self.comm = MPI.COMM_WORLD

    def write(self, str):
        #  print("[{0}]: {1}".format(self.comm.Get_rank(), str))
        pass


class MpiReceiveIterator(MpiIterator):
    def __init__(self, group_count, source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG):
        super(MpiReceiveIterator, self).__init__()
        self.group_count = group_count
        self.stop_count = 0
        self.source = source
        self.tag = tag

    def next(self):
        self.write("Receive receiving...")
        status = MPI.Status()
        message = self.comm.recv(source=self.source,
                                 tag=self.tag,
                                 status=status)

        self.write("Receive received {}".format(message))

        if status.tag == MpiTag.ITERATOR_ITEM:
            return message
        elif status.tag == MpiTag.ITERATOR_STOP:
            self.stop_count += 1
            if self.group_count == self.stop_count:
                raise StopIteration()
            else:
                return self.next()


class MpiRegionJoinIterator(MpiIterator):
    def __init__(self, parent, destination):
        super(MpiRegionJoinIterator, self).__init__()
        self.parent = parent
        self.destination = destination

    def next(self):
        try:
            item = next(self.parent)

            self.write("RegionJoin sending to {0}".format(self.destination))
            self.comm.send(item, self.destination, tag=MpiTag.ITERATOR_ITEM)
        except:
            self.write("RegionJoin ending")
            self.comm.send("", self.destination, tag=MpiTag.ITERATOR_STOP)
            raise StopIteration()


class MpiRegionSplitIterator(MpiIterator):
    def __init__(self, source):
        super(MpiRegionSplitIterator, self).__init__()
        self.source = source

    def next(self):
        self.write("RegionSplit requesting data from {0}".format(self.source))
        self.comm.send("", self.source, tag=MpiTag.NODE_JOB_REQUEST)

        status = MPI.Status()
        message = self.comm.recv(source=self.source,
                                 tag=MPI.ANY_TAG,
                                 status=status)

        self.write("RegionSplit received item {}".format(message))

        if status.tag == MpiTag.NODE_JOB_OFFER:
            return message
        elif status.tag == MpiTag.ITERATOR_STOP:
            raise StopIteration()


class MpiSplitIterator(MpiIterator):
    def __init__(self, parent, group):
        super(MpiSplitIterator, self).__init__()
        self.parent = parent
        self.group = group

    def next(self):
        try:
            item = next(self.parent)
            self.write("Split generated item {0}".format(item))
            status = MPI.Status()
            self.comm.recv(source=MPI.ANY_SOURCE,
                           tag=MpiTag.NODE_JOB_REQUEST,
                           status=status)
            self.write("Split sending to {0}".format(status.source))
            self.comm.send(item, status.source, tag=MpiTag.NODE_JOB_OFFER)
        except:
            for node in self.group:
                self.comm.send("", node, MpiTag.ITERATOR_STOP)
            raise StopIteration()


class MpiContext(ParallelContext):
    def __init__(self):
        super(MpiContext, self).__init__()
        self.comm = MPI.COMM_WORLD
        self.size = self.comm.Get_size()
        self.rank = self.comm.Get_rank()
        self.node_graph = None

        if self.comm.Get_size() < 2:
            raise BaseException("MPI context has to be run with at"
                                "least 2 MPI processes")

    def init(self):
        pass

    def is_master(self):
        return self.rank == 0

    def compute_action(self, graph, action):
        self.preprocess_splits(graph)

        self.node_graph = NodeGraph(self.size)
        first_node = self.node_graph.get_available_node()
        previous_node = first_node

        for node in graph.nodes:
            if isinstance(node.iterator, JoinTransformation):
                previous_node = self._parallelize_iterator(node, previous_node)

        start_iterator = MpiRegionJoinIterator(graph.nodes[0].iterator, 0)
        self.node_graph.assign_job(first_node, start_iterator)

        if self.rank == 0:
            return self._master(graph, action)

        return None

    def transmit_to_master(self, message):
        self.comm.send(message, 0, MpiTag.NOTIFICATION_MESSAGE)

    def _master(self, graph, action):
        while self._receive_msg(action):
            pass

        while True:
            status = MPI.Status()
            self.comm.iprobe(source=MPI.ANY_SOURCE,
                             tag=MPI.ANY_TAG,
                             status=status)
            if status.count > 0:
                self._receive_msg(action)
            else:
                break

    def _receive_msg(self, action):
        status = MPI.Status()
        message = self.comm.recv(source=MPI.ANY_SOURCE,
                                 tag=MPI.ANY_TAG,
                                 status=status)

        if status.tag == MpiTag.NOTIFICATION_MESSAGE:
            session.post_message(message)
        elif status.tag == MpiTag.ITERATOR_ITEM:
            action.handle_item(message)
        elif status.tag == MpiTag.ITERATOR_STOP:
            return False

        return True

    def _parallelize_iterator(self, join, previous_node):
        split = join

        # assumes that the graph is correct with respect
        # to split-join pairing and we deal only with transformations
        # TODO: copy iterator attributes
        while not isinstance(split.iterator, SplitTransformation):
            split = split.inputs[0]

        splitter_node = self.node_graph.get_available_node()

        # MPI > parallel region > Join
        joiner_node = previous_node
        parallel_iter_begin = MpiRegionJoinIterator(join.iterator.parent,
                                                    joiner_node)
        parallel_iter_end = MpiRegionSplitIterator(splitter_node)
        split.output.iterator.parent = parallel_iter_end
        # assign to multiple nodes
        group = []

        for i in xrange(split.iterator.process_count):
            node = self.node_graph.get_available_node()
            # TODO: split into multiple processes
            self.node_graph.assign_job(node, parallel_iter_begin)
            group.append(node)

        # MPI > Join
        join_iterator = MpiReceiveIterator(len(group))
        join_iterator.size = join.iterator.size
        join.iterator = join_iterator
        if join.output:
            join.output.iterator.parent = join_iterator

        # Split > MPI
        input_iterator = MpiSplitIterator(split.iterator.parent, group)
        input_iterator.size = split.iterator.size
        self.node_graph.assign_job(splitter_node, input_iterator)

        return splitter_node


comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()
if rank != 0:
    MpiWorker(size, rank).run()
    exit(0)
