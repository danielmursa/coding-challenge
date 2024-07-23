import os
import logging
from sqlalchemy import UniqueConstraint
from logging import FileHandler
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, jsonify, request, abort
from utils import is_valid_data
from config import DockerConfig, LocalConfig


app = Flask(__name__)

# ENV
config_type = os.getenv("ENV", "local")
if config_type == "local":
    config = LocalConfig
else:
    config = DockerConfig

app.config["SQLALCHEMY_DATABASE_URI"] = config.SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Logger Config
file_handler = FileHandler(config.LOG_FILE)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
file_handler.setLevel(config.LOG_LEVEL)

app.logger.addHandler(file_handler)
app.logger.setLevel(config.LOG_LEVEL)


# Initialize SQLAlchemy and DB
db = SQLAlchemy(app)


class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    groupId = db.Column(db.String(255), nullable=False)
    nodeId = db.Column(db.String(255), nullable=False)

    __table_args__ = (
        UniqueConstraint("groupId", "nodeId", name="unique_group_node_id"),
    )

    def __repr__(self):
        return f"Group(groupId={self.groupId}, nodeId={self.nodeId})"

    def to_dict(self):
        return {
            "groupId": self.groupId,
            "nodeId": self.nodeId,
        }


# Create tables if they do not exist
with app.app_context():
    db.create_all()


@app.route("/")
def home_view():
    """
    Returns home page view

    Returns:
        dict:
    """

    context = {
        "SwisscomAPI": {
            "name": "SwisscomAPI",
            "version": "0.0.1",
            "port": config.CURRENT_PORT,
            "node_id": config.NODE_ID,
        },
    }
    return context


@app.route("/v1/groups", methods=["GET"])
def get_groups():
    """
    Retrieves and returns a list of groups associated with the current node

    Returns:
        Response:
    """
    groups = Group.query.filter_by(nodeId=config.NODE_ID).all()
    return jsonify(
        {"nodeId": config.NODE_ID, "groups": [group.to_dict() for group in groups]}
    )


@app.route("/v1/group/<groupId>/", methods=["GET"])
def get_group(groupId):
    """
    Retrieves and returns details of a specific group by ID

    Args:
        groupId (str):
    Returns:
        Response:
    """

    group = Group.query.filter_by(groupId=groupId, nodeId=config.NODE_ID).first()
    if not group:
        msg = "Not found"
        app.logger.error(f"GET /v1/group/{groupId} -{msg}")
        abort(404, description=msg)
    return jsonify(group.to_dict()), 200


@app.route("/v1/group/", methods=["POST"])
def create_group():
    """
    Creates a new group, a JSON object containing the group details. Must include 'groupId'

    Returns:
        Response:
    """
    data = request.json
    is_valid, error_message = is_valid_data(data)
    if not is_valid:
        app.logger.error(f"POST /v1/group/ - {error_message}")
        abort(400, description=error_message)
    groupId = data["groupId"]
    if Group.query.filter_by(groupId=groupId, nodeId=config.NODE_ID).first():
        msg = "Bad request. Perhaps the object exists."
        app.logger.error(f"POST /v1/group/ - {msg}")
        abort(400, description=msg)
    new_group = Group(groupId=groupId, nodeId=config.NODE_ID)
    db.session.add(new_group)
    db.session.commit()
    app.logger.info(f"Created group with groupId: {new_group.groupId}")
    return jsonify(new_group.to_dict()), 201


@app.route("/v1/group/", methods=["DELETE"])
def delete_group():
    """
    Delete a group with the specified groupId.

    Returns:
        Response:
    """
    data = request.json
    is_valid, error_message = is_valid_data(data)
    if not is_valid:
        app.logger.error(f"DELETE /v1/group/ - {error_message}")
        abort(400, description=error_message)
    groupId = data["groupId"]
    group = Group.query.filter_by(groupId=groupId, nodeId=config.NODE_ID).first()
    if not group:
        msg = "Not found"
        app.logger.error(f"DELETE /v1/group/ - {msg}")
        abort(404, description=msg)
    db.session.delete(group)
    db.session.commit()
    return "", 200


@app.route("/v1/groups/", methods=["DELETE"])
def delete_groups():
    """
    Delete all groups

    Returns:
        Response:
    """
    db.session.query(Group).filter_by(nodeId=config.NODE_ID).delete()
    db.session.commit()
    return "", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
