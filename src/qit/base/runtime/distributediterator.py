import math
from distributed import Executor

from qit.base.runtime.message import MessageTag, Message
from qit.base.transform import Transformation


def set_and_compute_unwrap(args):
    return set_and_compute(*args)


def set_and_compute(graph, action_factory, index, count):
    graph.set(index)

    if graph.size:
        count = min(max(graph.size - index, 0), count)

    if count == 0:
        return Message(MessageTag.PROCESS_ITERATOR_STOP)

    action = action_factory.create()

    try:
        for i in xrange(count):
            action.handle_item(graph.next())
        return Message(MessageTag.PROCESS_ITERATOR_ITEM, action.get_result())
    except StopIteration:
        return Message(MessageTag.PROCESS_ITERATOR_STOP)


class DistributedSplitIterator(Transformation):
    def __init__(self, parent, action_factory, config, parallel_subgraph):
        super(DistributedSplitIterator, self).__init__(parent)
        self.action_factory = action_factory
        self.config = config
        self.executor = Executor(config.address)
        self.parallel_subgraph = parallel_subgraph
        self.subgraph_iterator = self.parallel_subgraph.create()
        self.index = 0
        if self.parent.size:
            self.batch = int(math.ceil(
                (self.parent.size / float(config.worker_count))))
        else:
            self.batch = 100
        self.iterated_all = False

    def next(self):
        if self.iterated_all:
            raise StopIteration()

        if self.parent.size:
            task_count = int(math.ceil(self.parent.size / self.batch))
            self.iterated_all = True
        else:
            task_count = self.config.worker_count

        tasks = self._distribute_submit(task_count)
        data = self.executor.gather(tasks)

        result = []
        for item in data:
            if item.tag == MessageTag.PROCESS_ITERATOR_ITEM:
                result += item.data

        return result

    def _distribute_map(self, task_count):
        index = self.index
        args = [(self.subgraph_iterator, self.action_factory,
                 index + i * self.batch, self.batch)
                for i in xrange(task_count)]
        self.index += task_count * self.batch

        return self.executor.map(set_and_compute_unwrap, args)

    def _distribute_submit(self, task_count):
        index = self.index
        args = [(index + i * self.batch, self.batch)
                for i in xrange(task_count)]
        self.index += task_count * self.batch

        return [self.executor.submit(set_and_compute, self.subgraph_iterator,
                                      self.action_factory, *arg)
                for arg in args]

    def _distribute_broadcast(self, task_count):
        index = self.index
        args = [(index + i * self.batch, self.batch)
                for i in xrange(task_count)]
        self.index += task_count * self.batch

        [data_future] = self.executor.scatter(
            [self.subgraph_iterator], broadcast=True)

        return [self.executor.submit(set_and_compute, data_future,
                                     self.action_factory, *arg)
                for arg in args]