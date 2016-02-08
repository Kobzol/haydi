from context import Context


class SerialContext(Context):
    def compute_action(self, graph, action):
        self.preprocess_graph(graph)

        for item in list(graph.create()):
            action.handle_item(item)

    def preprocess_graph(self, graph):
        """
        Removes all split transformations.
        :type graph: graph.Graph
        """
        skipped = []
        for node in graph.nodes:
            if node.factory.klass.is_split():
                skipped.append(node)

        for skipped_node in skipped:
            graph.skip(skipped_node)
