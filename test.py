import unittest
import requests
from client import Node, ClusterClient
from settings import *


class TestNodeIntegration(unittest.TestCase):
    def setUp(self):
        self.node = Node(NODE_1, API_ENDPOINT)
        self.node.delete_all()

    def test_create_success(self):
        response = self.node.create_object({"groupId": "1"})
        self.assertTrue(response)

        response = self.node.create_object({"groupId": "2"})
        self.assertTrue(response)

    def test_create_error(self):
        # wrong key
        response = self.node.create_object({"GROUP_ID": "1"})
        self.assertFalse(response)

        # duplicate
        response = self.node.create_object({"groupId": "1"})
        self.assertTrue(response)

    def test_delete_success(self):
        response = self.node.create_object({"groupId": "1"})
        self.assertTrue(response)

        response = self.node.delete_object({"groupId": "1"})
        self.assertTrue(response)

    def test_delete_error(self):
        response = self.node.create_object({"groupId": "1"})
        self.assertTrue(response)

        # wrong key
        response = self.node.delete_object({"GROUP_ID": "1"})
        self.assertFalse(response)

        # not found
        response = self.node.delete_object({"groupId": "2"})
        self.assertFalse(response)


class TestClusterClient(unittest.TestCase):
    def setUp(self):
        self.nodes = []
        for node_url in NODE_URLS:
            node = Node(node_url, API_ENDPOINT)
            node.delete_all()
            self.nodes.append(node)

        self.cluster = ClusterClient(self.nodes)

    def test_create_success(self):
        data = {"groupId": "1"}
        status = self.cluster.create_object(data)
        self.assertTrue(status)

        for node in self.nodes:
            obj = node.get_object("1")
            self.assertTrue("groupId" in obj)
            self.assertEqual(obj["groupId"], "1")

    def test_delete_success(self):
        data = {"groupId": "44"}
        status = self.cluster.create_object(data)
        self.assertTrue(status)

        status = self.cluster.delete_object(data)
        self.assertTrue(status)

        for node in self.nodes:
            obj = node.get_object("44")
            self.assertFalse(obj)

    def test_create_all_error(self):
        data = {"groupId": "1"}
        status = self.cluster.create_object(data)
        self.assertTrue(status)

        # duplicate
        data = {"groupId": "1"}
        status = self.cluster.create_object(data)
        self.assertFalse(status)

    def test_delete_all_error(self):
        # not found
        data = {"groupId": "10"}
        status = self.cluster.delete_object(data)
        self.assertFalse(status)


if __name__ == "__main__":
    unittest.main()
