"""Tiny in-memory stand-in for the GitHub contents API, for testing sync without a real token.

    python dev/mock_github.py            # http://localhost:8787, repo test/japan-plan, token test-token

Point the app at it (browser console on http://localhost:8000):
    localStorage.setItem("njr-gh-api", "http://localhost:8787")
then connect with repo test/japan-plan and token test-token. Remove njr-gh-api to go back to GitHub.

Seeds plan.json from ../plan.json if present (gitignored), else a small sample.
Test helpers (no auth): GET /__file/<name>, POST /__file/<name> (replace a file as if another device saved it),
GET /__log (commit messages), POST /__offline/1|0 (drop every API request).
"""
import base64, hashlib, json, os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

REPO, TOKEN, PORT = "test/japan-plan", "test-token", 8787
HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLE = {"version": 1, "trip": "Sample trip", "days": [
    {"date": "2030-04-01", "city": "Tokyo", "title": "Arrive", "note": "", "stops": [
        {"id": "a1", "time": "15:00", "name": "Hotel", "cat": "stay", "lat": 35.6938, "lng": 139.7034, "note": ""},
        {"id": "a2", "time": "19:00", "name": "Omoide Yokocho", "cat": "food", "lat": 35.6931, "lng": 139.6995, "note": ""}]},
    {"date": "2030-04-02", "city": "Tokyo", "title": "Akihabara", "note": "", "stops": [
        {"id": "b1", "time": "11:00", "name": "Radio Kaikan", "cat": "anime", "lat": 35.6979, "lng": 139.7714, "note": ""}]}],
    "ideas": []}

seed = os.path.join(HERE, "..", "plan.json")
FILES = {"plan.json": open(seed, "rb").read() if os.path.exists(seed) else json.dumps(SAMPLE, indent=2).encode()}
LOG, STATE = [], {"offline": False}
blob_sha = lambda b: hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()


class H(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(self.command, self.path, flush=True)

    def reply(self, code, obj=None, raw=None, ctype="application/json"):
        body = raw if raw is not None else json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, Accept")
        self.send_header("Access-Control-Allow-Methods", "GET, PUT, POST, OPTIONS")
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def body(self):
        return self.rfile.read(int(self.headers.get("Content-Length") or 0))

    def api(self):
        """Returns the path inside the repo, or None after replying with an error / dropping the request."""
        if STATE["offline"]:
            self.close_connection = True
            return None
        prefix = "/repos/" + REPO
        if not self.path.startswith(prefix):
            return self.reply(404, {"message": "Not Found"})
        if self.headers.get("Authorization") != "Bearer " + TOKEN:
            return self.reply(401, {"message": "Bad credentials"})
        return self.path[len(prefix):].split("?")[0]

    def do_OPTIONS(self):
        self.reply(204, raw=b"")

    def do_GET(self):
        if self.path.startswith("/__file/"):
            name = self.path[8:]
            return self.reply(200, raw=FILES[name], ctype="text/plain") if name in FILES else self.reply(404, {})
        if self.path == "/__log":
            return self.reply(200, LOG)
        p = self.api()
        if p is None:
            return
        if p == "":
            return self.reply(200, {"full_name": REPO, "private": True})
        name = p[len("/contents/"):]
        if not p.startswith("/contents/") or name not in FILES:
            return self.reply(404, {"message": "Not Found"})
        b = FILES[name]
        self.reply(200, {"name": name, "path": name, "sha": blob_sha(b), "encoding": "base64", "content": base64.encodebytes(b).decode()})

    def do_PUT(self):
        p = self.api()
        if p is None:
            return
        name, req = p[len("/contents/"):], json.loads(self.body())
        cur = FILES.get(name)
        if cur is not None and "sha" not in req:
            return self.reply(422, {"message": 'Invalid request.\n\n"sha" wasn\'t supplied.'})
        if cur is not None and req["sha"] != blob_sha(cur):
            return self.reply(409, {"message": "%s does not match %s" % (name, req["sha"])})
        FILES[name] = base64.b64decode(req["content"])
        LOG.append(req["message"])
        self.reply(201 if cur is None else 200, {"content": {"name": name, "sha": blob_sha(FILES[name])}, "commit": {"message": req["message"]}})

    def do_POST(self):
        if self.path.startswith("/__file/"):
            FILES[self.path[8:]] = self.body()
            LOG.append("(out of band) " + self.path[8:])
            return self.reply(200, {"sha": blob_sha(FILES[self.path[8:]])})
        if self.path.startswith("/__offline/"):
            STATE["offline"] = self.path.endswith("1")
            return self.reply(200, STATE)
        self.reply(404, {})


if __name__ == "__main__":
    print("mock GitHub API on http://localhost:%d (repo %s, token %s)" % (PORT, REPO, TOKEN), flush=True)
    ThreadingHTTPServer(("localhost", PORT), H).serve_forever()
