from typing import Dict

from flask import Flask, abort, current_app, redirect, safe_join, send_file
from flask_compress import Compress
from google.cloud import storage
import tempfile

from google.cloud.exceptions import NotFound

from common.url_for import get_host

app = Flask(__name__)
if __name__ == "__main__":
    app.debug = True


def get_bucket(app_lookup: Dict[str, str]):
    if current_app.debug:
        return "website.buckets.cs61a.org"

    host = get_host()
    if ".pr." in host:
        pr, app, *_ = host.split(".")
        pr = int(pr)
        if app not in app_lookup:
            abort(404)
        return f"{app_lookup[app]}-pr{pr}.buckets.cs61a.org"
    else:
        app, *_ = host.split(".")
        if app not in app_lookup:
            abort(404)
        return f"{app_lookup[app]}.buckets.cs61a.org"


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>", methods=["GET"])
def get(path):
    filename = safe_join("/", path)[1:]
    client = storage.Client()
    bucket = client.get_bucket(
        get_bucket({"static-server": "website", "website": "website"})
    )
    try:
        if not filename:
            raise NotFound(filename)
        blob = bucket.blob(filename)
        if blob.exists() and path != filename:
            return redirect("/" + filename)
        with tempfile.NamedTemporaryFile() as temp:
            blob.download_to_filename(temp.name)
            return send_file(temp.name, attachment_filename=filename)
    except NotFound:
        if filename.endswith("index.html"):
            abort(404)
        else:
            if path and not path.endswith("/"):
                if bucket.blob(filename + "/" + "index.html").exists():
                    return redirect("/" + filename + "/", 301)
                else:
                    abort(404)
            return get(path + "index.html")


Compress(app)


if __name__ == "__main__":
    app.run(debug=True)