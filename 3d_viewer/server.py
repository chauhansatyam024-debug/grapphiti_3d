#!/usr/bin/env python3
import http.server
import socketserver
import json
import subprocess
import os

PORT = 8080

def fetch_graph_data():
    nodes_map = {}
    links_list = []

    # Default fallback nodes if database is empty
    base_nodes = {
        "Antigravity": {
            "id": "Antigravity",
            "name": "Antigravity AI Agent",
            "label": "Agent",
            "summary": "Active primary coding AI agent managing Graphiti memory & Docker services.",
            "val": 20
        },
        "Graphiti MCP Server": {
            "id": "Graphiti MCP Server",
            "name": "Graphiti MCP Server",
            "label": "ProjectComponent",
            "summary": "Shared bitemporal knowledge graph memory service running on FalkorDB & Groq/Gemini.",
            "val": 16
        },
        "VS Code Agent": {
            "id": "VS Code Agent",
            "name": "VS Code AI Agent",
            "label": "Agent",
            "summary": "Active secondary coding agent working in VS Code across project workspaces.",
            "val": 20
        }
    }

    nodes_map.update(base_nodes)

    # Dynamically query FalkorDB for live graph data
    for graph_name in ["main", "default_db"]:
        try:
            cmd = ['docker', 'exec', 'docker-graphiti-falkordb-1', 'redis-cli', 'GRAPH.QUERY', graph_name, "MATCH (a)-[r]->(b) RETURN a.name, type(r), r.fact, b.name"]
            output = subprocess.check_output(cmd, timeout=3).decode('utf-8', errors='ignore')
            lines = [l.strip() for l in output.split('\n') if l.strip()]
            
            # Skip header lines if present
            idx = 0
            if lines and "a.name" in lines[0]:
                idx = 4
                
            while idx + 3 < len(lines):
                if lines[idx].startswith("Cached execution") or lines[idx].startswith("Query internal"):
                    break
                src_name = lines[idx]
                rel_type = lines[idx+1]
                rel_fact = lines[idx+2]
                target_name = lines[idx+3]
                idx += 4

                if not src_name or not target_name:
                    continue

                # Add Source Node
                if src_name not in nodes_map:
                    nodes_map[src_name] = {
                        "id": src_name,
                        "name": src_name,
                        "label": "Agent" if "Agent" in src_name or src_name == "Antigravity" else "ProjectComponent",
                        "summary": f"Graph node: {src_name}",
                        "val": 20 if "Agent" in src_name else 16
                    }

                # Add Target Node
                if target_name not in nodes_map:
                    nodes_map[target_name] = {
                        "id": target_name,
                        "name": target_name,
                        "label": "ProjectComponent",
                        "summary": rel_fact,
                        "val": 16
                    }

                # Check if link already present
                link_key = f"{src_name}->{target_name}"
                if not any(f"{l['source']}->{l['target']}" == link_key for l in links_list):
                    links_list.append({
                        "source": src_name,
                        "target": target_name,
                        "name": rel_type,
                        "fact": rel_fact
                    })

        except Exception as e:
            print(f"Error querying graph {graph_name}: {e}")

    # Ensure link between Antigravity and VS Code Agent for cross-agent visual link
    if "Antigravity" in nodes_map and "VS Code Agent" in nodes_map:
        if not any(l['source'] == "Antigravity" and l['target'] == "VS Code Agent" for l in links_list):
            links_list.append({
                "source": "Antigravity",
                "target": "VS Code Agent",
                "name": "shares_memory_with",
                "fact": "Real-time cross-agent memory synchronization via Graphiti MCP protocol."
            })

    return {
        "nodes": list(nodes_map.values()),
        "links": links_list
    }

class GraphHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/graph':
            data = fetch_graph_data()
            body = json.dumps(data).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(body)
        else:
            super().do_GET()

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", PORT), GraphHandler) as httpd:
        print(f"3D Visualizer running on http://localhost:{PORT}")
        httpd.serve_forever()
