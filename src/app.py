from flask import Flask, render_template, request, jsonify
import uuid
import docker

app = Flask(__name__)

# Initialize Docker client
client = docker.from_env()

# List of sample SPPs (each SPP is a simple Docker image for the sake of this POC)
spps = [
    {"id": 1, "name": "Hello World App", "image": "hello-world"},
]


@app.route("/")
def index():
    # Fetch all containers, not just the running ones
    all_containers = client.containers.list(all=True)

    running_spps = [
        {"name": container.name, "id": container.short_id}
        for container in all_containers
        if any(spp["image"] in container.image.tags[0] for spp in spps)
    ]
    return render_template("index.html", spps=spps, running_spps=running_spps)


@app.route("/run/<int:spp_id>", methods=["POST"])
def run_spp(spp_id):
    spp = next((spp for spp in spps if spp["id"] == spp_id), None)
    if not spp:
        return jsonify({"error": "SPP not found"}), 404

    try:
        # Sanitize the spp name and append a unique UUID to make sure it's unique
        sanitized_name = "".join(
            e for e in spp["name"] if e.isalnum() or e in ["_", "-"]
        ).lower()
        unique_name = f"{sanitized_name}-{str(uuid.uuid4())[:8]}"

        container = client.containers.run(spp["image"], name=unique_name, detach=True)
        return jsonify(
            {
                "message": f"SPP {spp['name']} is running in container ID {container.short_id}"
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/logs/<container_id>")
def get_logs(container_id):
    try:
        container = client.containers.get(container_id)
        logs = container.logs().decode("utf-8")
        return jsonify({"container_id": container_id, "logs": logs})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
