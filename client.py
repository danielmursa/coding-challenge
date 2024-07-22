import os
import time
import requests
import logging
from settings import *
from logging import FileHandler
from config import LocalConfig, DockerConfig
from concurrent.futures import ThreadPoolExecutor, as_completed

# ENV
config_type = os.getenv("ENV", "local")
if config_type == "local":
    config = LocalConfig
else:
    config = DockerConfig


# Logger Config
file_handler = logging.FileHandler(config.LOG_FILE_CLIENT)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
file_handler.setLevel(config.LOG_LEVEL)
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logger.addHandler(file_handler)
    logger.setLevel(config.LOG_LEVEL)


def retry_request(func, max_retries=MAX_RETRIES, delay=DELAY):
    """
    A decorator that retries a function call if it fails with a requests.RequestException. Retries use exponential backoff.

    Parameters:
        - func
        - max_retries
        - delay

    Returns
    """

    def wrapper(*args, **kwargs):
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except requests.RequestException as e:
                if attempt == max_retries - 1:
                    raise e
                time.sleep(delay * (2**attempt))

    return wrapper


class Node:
    def __init__(self, url, endpoint):
        self.url = url
        self.endpoint = endpoint

    @retry_request
    def make_request(self, method, data=None):
        """
        Makes an HTTP request.

        Parameters:
            - method
            - data

        Returns
        """
        url = f"{self.url}/{self.endpoint}"
        response = requests.request(method, url, json=data, timeout=5)
        response.raise_for_status()
        return response

    def create_object(self, data):
        """
        Sends a POST request to create an object.

        Parameters:
            - data

        Returns:
            - bool
        """
        try:
            self.make_request(POST, data)
            logger.info(f"CREATE OK for {self.url}")

            return True
        except requests.RequestException as e:
            logger.error(e)
            return False

    def delete_object(self, data):
        """
        Sends a DELETE request to remove an object.

        Parameters:
            - data

        Returns:
            - bool:
        """
        try:
            self.make_request(DELETE, data)
            logger.info(f"DELETE OK for {self.url}")
            return True
        except requests.RequestException as e:
            logger.error(e)
            return False

    def get_object(self, id):
        """
        Sends a GET request to retrieve an object by its ID.

        Parameters:
            - id

        Returns:
            - dict or None
        """
        try:
            response = requests.request(
                GET, f"{self.url}/{self.endpoint}/{id}", timeout=5
            )
            if response:
                return response.json()
            else:
                return None
        except requests.RequestException as e:
            logger.error(e)
            return None

    def delete_all(self):
        try:
            requests.request(DELETE, f"{self.url}/v1/groups", timeout=5)
            return True
        except requests.RequestException as e:
            logger.error(e)
            return False


class ClusterClient:
    def __init__(self, nodes, max_workers=5):
        self.nodes = nodes
        self.max_workers = max_workers

    def create_object(self, data):
        """
        Creates an object on all nodes and rolls back if any creation fails.

        Parameters:
            - data

        Returns:
            - bool
        """
        successful_nodes = []
        failed_nodes = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(node.create_object, data): node for node in self.nodes
            }

            for future in as_completed(futures):
                node = futures[future]
                if future.result():
                    successful_nodes.append(node)
                else:
                    logger.error(f"Failed to create object on node {node.url}")
                    failed_nodes.append(node)

        if failed_nodes:
            logger.info(
                f"Start _rollback_create for nodes: {[node.url for node in successful_nodes]}"
            )
            self._rollback_operation(data, successful_nodes, DELETE)
            status = False
            logger.info(
                f"End _rollback_create for nodes: {[node.url for node in successful_nodes]}"
            )
        else:
            status = True

        return status

    def delete_object(self, data):
        """
        Deletes an object from all nodes and rolls back if any deletion fails.

        Parameters:
            - data

        Returns:
            - bool
        """
        successful_nodes = []
        failed_nodes = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(node.delete_object, data): node for node in self.nodes
            }

            for future in as_completed(futures):
                node = futures[future]
                if future.result():
                    successful_nodes.append(node)
                else:
                    logger.error(f"Failed to delete object on node {node.url}")
                    failed_nodes.append(node)

        if failed_nodes:
            logger.info(
                f"Start _rollback_delete for nodes: {[node.url for node in successful_nodes]}"
            )
            self._rollback_operation(data, successful_nodes, POST)
            status = False
            logger.info(
                f"End _rollback_delete for nodes: {[node.url for node in successful_nodes]}"
            )
        else:
            status = True

        return status

    def _rollback_operation(self, data, nodes, operation):
        """
        Rolls back an operation on the specified nodes.

        Parameters:
            - data 
            - nodes 
            - operation

        Returns:
            - None
        """
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            if operation == POST:
                futures = {
                    executor.submit(node.create_object, data): node for node in nodes
                }
            else:
                futures = {
                    executor.submit(node.delete_object, data): node for node in nodes
                }

            for future in as_completed(futures):
                node = futures[future]
                try:
                    future.result()
                except Exception as e:
                    logger.error(
                        f"Failed to _rollback_{operation} on node {node.url}: {e}"
                    )
