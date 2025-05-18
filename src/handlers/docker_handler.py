from urllib.parse import parse_qs, urlparse, unquote
import http.server
import os
import subprocess
import json
import datetime

class DockerLogHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)

        if path == "/" or path == "":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.send_cors_headers()
            self.end_headers()

            assets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))
            index_file = os.path.join(assets_dir, "index.html")
            
            try:
                with open(index_file, 'r', encoding='utf-8') as file:
                    html_content = file.read()
                    self.wfile.write(html_content.encode('utf-8'))
            except FileNotFoundError:
                self.wfile.write(b"<h1>404 - HTML File Not Found</h1>")
                return

        elif path == "/api/containers":
            self.send_containers_list()
        elif path.startswith("/api/logs/"):
            container_id = unquote(path.replace("/api/logs/", ""))
            since = query_params.get('since', [None])[0]
            self.send_container_logs(container_id, since)
        elif path.startswith("/assets/"):
            file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", path.lstrip("/")))
            if os.path.isfile(file_path):
                self.send_response(200)
                if file_path.endswith(".png"):
                    self.send_header("Content-Type", "image/png")
                elif file_path.endswith(".ico"):
                    self.send_header("Content-Type", "image/x-icon")
                else:
                    self.send_header("Content-Type", "application/octet-stream")
                self.send_cors_headers()
                self.end_headers()
                with open(file_path, "rb") as f:
                    self.wfile.write(f.read())
        else:
            self.send_response(404)
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(b"404 Not Found")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()
    
    def send_cors_headers(self):
        """Helper method to send CORS headers"""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def send_containers_list(self):
        try:
            proc = subprocess.run(
                ["docker", "ps", "--format", "{{.ID}}\t{{.Names}}"],
                capture_output=True,
                text=True
            )

            if proc.returncode != 0:
                self.send_response(500)
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(f"Error: {proc.stderr}".encode())
                return

            containers = []
            lines = proc.stdout.strip().split('\n')

            for line in lines:
                parts = line.split('\t', 1)  # Split into ID and name correctly
                if len(parts) >= 2:
                    containers.append({"id": parts[0], "name": parts[1]})


            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(containers).encode())
        except Exception as e:
            self.send_response(500)
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(f"Error: {str(e)}".encode())

    def send_container_logs(self, container_id, since=None):
        try:
            cmd = ["docker", "logs", container_id]  
            if since:
                try:
                    since_timestamp = int(since) / 1000
                    time_obj = datetime.datetime.utcfromtimestamp(since_timestamp)  # UTC fixed
                    formatted_time = time_obj.strftime('%Y-%m-%dT%H:%M:%S')
                    cmd.extend(["--since", formatted_time])
                except (ValueError, TypeError):
                    cmd.extend(["--tail", "10"])

            proc = subprocess.run(cmd, capture_output=True, text=True)

            if proc.returncode != 0:
                self.send_response(404)
                self.send_cors_headers()
                self.end_headers()
                error_msg = f"Error: Could not fetch logs for container '{container_id}'\n{proc.stderr}"
                self.wfile.write(error_msg.encode())
                return

            self.send_response(200)
            self.send_header("Content-type", "text/plain; charset=utf-8")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(proc.stdout.encode())
        except Exception as e:
            self.send_response(500)
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(f"Error: {str(e)}".encode())
