import http.client
import random
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
import threading


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    parent = None

    def do_GET(self):
        args = parse_qs(urlparse(self.path).query, keep_blank_values=True)

        if "error" in args:
            http_status = http.client.BAD_REQUEST
            http_body = f"error: {args['error'][0]}\nerror description: {args['error_description'][0]}"
        else:
            http_status = http.client.OK
            emoji = random.choice(["🎉", "👍", "👍🏿", "🥳", "🎈"])
            http_body = f"""<html>
               <h1 style="font-size: large">{emoji}</h1>
               <p>Congratulations! Your authentication succeeded.</p>"""
            if not hasattr(self.parent, "path"):
                auth_code = args.get("code")
                self.parent.auth_code = auth_code[0]
                self.parent.path = self.path
        self.send_response(http_status)
        self.send_header("Content-Type", "text/html; charset=utf-8")

        self.end_headers()
        self.wfile.write(http_body.encode("utf-8"))

        threading.Thread(target=self.server.shutdown).start()

    def log_message(self, fmt, *args):
        pass


class CallbackServer:
    def get_auth(self, port=8000):
        OAuthCallbackHandler.parent = self
        httpd = HTTPServer(('localhost', port), OAuthCallbackHandler)
        httpd.timeout = 30
        httpd.serve_forever()
        return self.path


if __name__ == "__main__":
    cs = CallbackServer()
