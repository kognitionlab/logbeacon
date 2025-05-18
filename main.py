import argparse
import socket
import os
import sys
import shutil
from src.handlers.podman_handler import PodmanLogHandler
from src.handlers.docker_handler import DockerLogHandler
from src.server.http_server import ThreadedHTTPServer

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "src"))
sys.path.insert(0, project_root)


def check_dependencies():
    podman_installed = shutil.which("podman") is not None
    docker_installed = shutil.which("docker") is not None

    if not podman_installed and not docker_installed:
        print("Error: Neither Podman nor Docker is installed.")
        print("Please install at least one of them to use this tool.")
        sys.exit(1)

def get_network_interfaces(port):
    """Display available network interfaces to connect to the server"""
    try:
        import netifaces
        print("Available network interfaces:")
        for interface in netifaces.interfaces():
            try:
                addresses = netifaces.ifaddresses(interface).get(netifaces.AF_INET, [])
                for address_info in addresses:
                    ip = address_info.get('addr')
                    if ip:
                        print(f" - {interface}: http://{ip}:{port}/")
            except:
                pass
    except ImportError:
        print("For better network interface detection, install netifaces:")
        print("pip install netifaces")
        try:
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            print(f" - Local:   http://localhost:{port}/")
            print(f" - Network: http://{ip_address}:{port}/")
        except:
            print(f"Server running on all interfaces at port {port}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Container Log Viewer (Podman/Docker)")
    parser.add_argument("--backend", choices=["podman", "docker"], default="podman",
                        help="Choose backend: 'podman' or 'docker'")
    parser.add_argument("--port", type=int, default=5000, help="Port to run the server on")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server to")

    args = parser.parse_args()
    check_dependencies()
    handler_class = PodmanLogHandler if args.backend == "podman" else DockerLogHandler
    server_address = (args.host, args.port)

    print(f"🐋 Initializing LogBeacon")
    print(f"🚀 Server starting on port {args.port}...")

    try:
        httpd = ThreadedHTTPServer(server_address, handler_class)
        get_network_interfaces(args.port)
        print("🌐 If you can't connect, check your firewall settings for port", args.port)
        print("ℹ️ Press Ctrl+C to stop the server")
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("⛔ Server stopped by user")
    except Exception as e:
        print(f"🚫 Error starting server: {e}")