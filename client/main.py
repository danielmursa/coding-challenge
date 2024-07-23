# main.py
import json
import argparse
from settings import *
from client import ClusterClient, Node

CREATE = "create"
DELETE = "delete"


def main():
    """
    python main.py create '{"groupId": "1"}'
    python main.py delete '{"groupId": "1"}'
    """
    parser = argparse.ArgumentParser(
        description="Create or delete objects in a cluster."
    )
    parser.add_argument(
        "operation",
        choices=[CREATE, DELETE],
        help="Operation to perform: create or delete",
    )
    parser.add_argument("data", help="Data for the operation (e.g., JSON string)")

    # Parse arguments
    args = parser.parse_args()
    operation = args.operation
    data = args.data

    try:
        data = json.loads(data)
    except json.JSONDecodeError:
        print("Invalid JSON data provided.")
        return

    # Example usage
    nodes = []
    for node_url in NODE_URLS:
        nodes.append(Node(node_url, API_ENDPOINT))

    cluster = ClusterClient(nodes)

    # Perform the operation
    try:
        if operation == CREATE:
            cluster.create_object(data)
        elif operation == DELETE:
            cluster.delete_object(data)
        else:
            parser.print_help()
    except Exception as e:
        print(f"Operation failed: {e}")


if __name__ == "__main__":
    main()
