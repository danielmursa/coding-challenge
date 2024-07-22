# API Consumer Client Module (Coding-Challenge Swisscom)

## Introduction

This project provides a client module to reliably create and delete groups on a cluster of nodes. The cluster consists of several nodes, each identified by a host name.<br>
The module ensures that any operation (CREATE or DELETE) is performed consistently on all nodes in the cluster, gracefully handling API instability. In the event of an error (e.g. connection timeout or HTTP 500 error), the module rolls back the changes to maintain consistency across the cluster.

## Objectives

1. **Create Groups**: Ensure that when a group is created, it is successfully recorded on all nodes in the cluster.
1. **Delete Groups**: Ensure that when a group is deleted, it is removed from all nodes in the cluster.
1. **Handle Failures**: In case of errors such as connection timeouts or 500 server errors, the operation should be rolled back to maintain consistency across nodes.

## Assumptions

1. **Cluster Configuration**: The cluster configuration is provided as a list of hostnames, each constant was saved in a specific external file to allow for greater verstability of the system.
2. **API Instability**: The API may return errors such as connection timeouts or HTTP 500 errors, which need to be handled appropriately, are also considered errors if the object is not found in the node or if an attempt is made to insert it but gives a duplicate error.
3. **Atomic Operations**: Both creation and deletion of objects should be treated as atomic operations across all nodes. If any node fails to complete the operation, changes on all nodes should be rolled back.
4. **HTTP Methods**: The API supports HTTP methods for creating (`POST`) and deleting (`DELETE`) objects. In addition, new APIs have been added to return the resource given by Id.
5. **Consistency**: It is essential that the state of objects (groups) is consistent on all nodes. This means that if a group is created, it must be present on all nodes, and if a group is deleted, it must be removed from all nodes.
6. **Retry Logic**: The client module implements retry logic to handle transient errors (e.g. network problems). If an operation fails due to a transient problem, the module retries the operation for a configurable number of times before declaring it to have failed, thus giving the possibility of not causing the error immediately if it occurs due to a minor cause, such as system problems. Example a max_retries of 3 was placed.
7. **Rollback Mechanism**: If an operation fails, the client module will undo all changes made to ensure cluster consistency. For instance, if a cluster creation operation is partially successful (i.e. succeeds on some nodes but fails on others), the module will delete the cluster from the nodes where it was successfully created.
8. **Error Reporting**: The client module will provide detailed error reporting to facilitate troubleshooting. This includes logging which nodes encountered errors and the nature of the errors.
9. **Flask Applications**: Each node in the cluster runs a Flask application that provides the API endpoints needed to create and delete groups. These applications are configured via environment variables and Docker, as specified in the `docker-compose.yml` file.
10. **Docker Environment**: The Flask applications are deployed using Docker, and the environment configurations (such as ports and volumes) are managed through the `docker-compose.yml` file.
11. **Data Persistence**: Data related to groups is persisted in the `./data` directory on the host machine, which is mounted into the Docker containers running the Flask applications.
12. **Concurrency**: Using threads in the Node and ClusterClient classes significantly enhances the efficiency and scalability of the system by managing simultaneous operations across multiple nodes more quickly and robustly.

## Structure Project
swisscom_api/<br> 
│<br> 
├── <b>app.py                </b># Main application script for run nodes api<br> 
├── <b>client.py             </b># Client<br> 
├── <b>config.py             </b># Configuration settings and constants<br> 
├── <b>settings.py           </b># Settings for the application environment<br> 
├── <b>test.py               </b># UnitTests for the application<br> 
├── <b>main.py               </b># Entry point for the client<br> 
├── <b>utils.py              </b># Utility functions and helper methods<br> 
├── <b>Dockerfile            </b># Dockerfile to build the Docker image<br> 
├── <b>docker-compose.yml    </b># Docker Compose file to define and manage multi-container setup<br> 
├── <b>requirements.txt      </b># Python dependencies for the application<br> 
├── <b>readme.md             </b># This README file<br> 
├── <b>logs/                 </b># Directory for storing application logs<br> 
└── <b>data/                 </b># Directory for shared data between nodes<br> 


## Flask Application for Cluster Nodes

For each node in the cluster, a Flask application has been created. These Flask applications contain the necessary configurations for the APIs, providing endpoints to create and delete groups.


#### Prerequisites

- Python 3.7
- Flask
- Flask-SQLAlchemy
- SQLAlchemy
- Configurations (LocalConfig or DockerConfig)

#### Configuration

The application uses environment-based configuration:

- **Local Configuration**
- **Docker Configuration**


#### API Endpoints

Each Flask application runs on its respective node and exposes the following API endpoints:
```python
@app.route("/")
@app.route("/v1/groups", methods=["GET"])
@app.route("/v1/group/<groupId>/", methods=["GET"])
@app.route("/v1/group/", methods=["POST"])
@app.route("/v1/group/", methods=["DELETE"])
@app.route("/v1/groups/", methods=["DELETE"])
```
## Client Module

`ClusterClient` is a Python module designed to interact with a cluster of nodes. <br>
It provides functionality for creating, deleting, and retrieving objects across multiple nodes with robust error handling and retry mechanisms.

### Components

#### 1. Node Class
Represents an individual node in the cluster with methods to interact with it.

#### Methods:
- **`__init__(self, url, endpoint)`**: Initializes a Node with a base URL and an endpoint.
- **`make_request(self, method, data=None)`**: Sends an HTTP request with retries on failure.
- **`create_object(self, data)`**: Sends a POST request to create an object on the node.
- **`delete_object(self, data)`**: Sends a DELETE request to delete an object from the node.
- **`get_object(self, id)`**: Sends a GET request to retrieve an object by ID.
- **`delete_all(self)`**: Deletes all objects from the node's specific endpoint.


#### 2. ClusterClient Class
Manages interactions with a cluster of `Node` objects.

#### Methods:
- **`__init__(self, nodes, max_workers=5)`**: Initializes the client with a list of `Node` objects and a maximum number of worker threads.
- **`create_object(self, data)`**: Creates an object on all nodes. Rolls back if any node fails.
- **`delete_object(self, data)`**: Deletes an object from all nodes. Rolls back if any node fails.
- **`_rollback_operation(self, data, nodes, operation)`**: Handles rollbacks for specified operations (create or delete).


## Docker Setup

This project utilizes Docker to manage and deploy a Python application across multiple nodes. The setup consists of:

- A Dockerfile to build a Python application container.
- A `docker-compose.yml` file to define and run multiple containers as services.


## Installation and Usage


1. **Clone the Repository:**
   ```bash
   git clone https://github.com/danielmursa/coding-challenge
   cd https://github.com/danielmursa/coding-challenge
   ```

2. **Build the Docker images:**

   ```bash
   docker-compose build
   ```

3. **Start the services:**

   ```bash
   docker-compose up
   ```

4. **Run cluster:**
    `main.py` is a Python script designed to manage operations within a cluster environment. 
    The script allows users to create or delete groups of objects across multiple nodes in a cluster.

   ```bash
   python main.py --help

   python main.py create '{"groupId": "1"}'
   python main.py delete '{"groupId": "1"}'
   ```

5. **Stop and remove the containers:**

   ```bash
   docker-compose down
   ```

## Error Handling

- **Retries:** The module uses exponential backoff to retry failed requests.
- **Rollbacks:** If an operation fails, the module attempts to rollback changes on all nodes where the operation was successful.

## Logger Handling

The system uses Python’s logging module to capture and report various events and errors. Logs are configured to provide information about successful operations and errors encountered during execution. <br>
Different log levels (INFO, ERROR) are used to differentiate between normal operation messages and error messages.


## Conclusion

The **API Consumer** module offers a robust solution for managing objects across a distributed cluster of nodes. By addressing the inherent challenges of API instability, such as connection timeouts and server errors, this module ensures reliable and consistent operations. 

### Key Benefits

1. **Reliability** 
   - **Retry Mechanism** 
   - **Rollback Capability**

2. **Scalability**

3. **Flexibility**
   - **Customizable Configuration**
   - **Modular Design**

4. **Ease of Use**
   - **Simplified API**
   - **Logging and Debugging**

### Use Cases

- **Cluster Management:** Ideal for scenarios where you need to manage distributed systems or services across multiple nodes.
- **Data Consistency:** Ensures that operations on the cluster are performed consistently, even in the face of partial failures.
- **Operational Efficiency:** Automates the process of interacting with multiple nodes, reducing manual intervention and operational overhead.

### Additional Information

- **Configuration:** Ensure the `settings.py` file is correctly configured with parameters such as `MAX_RETRIES`, `DELAY`, and HTTP methods. This allows you to tailor the module's behavior to suit your specific requirements.
- **Test Script:** To validate the functionality of the module, you can run the `test.py` script provided in the repository. This script includes test cases that simulate various scenarios to ensure the module operates as expected.
  ```bash
  python test.py
  ```
  Running `test.py` will help verify the correctness of the implementation and catch any potential issues before deployment.

### Future Enhancements

- **Enhanced Rollback Strategies:** Explore advanced rollback mechanisms to handle more complex failure scenarios.
- **Performance Optimization:** Investigate performance improvements for handling larger clusters or higher request volumes.
- **Extended API Support:** Consider adding support for additional API operations or integrating with other services.
- **Create a Separate Test Database**
- **Improve Object Creation and Deletion Handling**

## Author
This project was developed by Daniel Mursa. For more information please contact danielmursa99@gmail.com