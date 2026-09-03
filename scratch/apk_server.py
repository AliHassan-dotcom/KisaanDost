import http.server
import socketserver
import os

PORT = 8080
APK_PATH = r"D:\KisaanDost\mobile_app\build\app\outputs\flutter-apk\app-debug.apk"

class APKDownloadHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            html = f"""<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kisaan Dost - Mobile App Download</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #F4F8F1; color: #1B5E20; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }}
        .card {{ background: white; border-radius: 24px; padding: 32px; max-width: 400px; width: 100%; box-shadow: 0 10px 30px rgba(27,94,32,0.15); text-align: center; border: 1px solid #E0EFE0; }}
        .logo {{ font-size: 48px; margin-bottom: 12px; }}
        h1 {{ font-size: 24px; margin: 0 0 8px 0; color: #1B5E20; font-weight: 800; }}
        p {{ color: #555; font-size: 14px; margin-bottom: 24px; line-height: 1.5; }}
        .btn {{ display: inline-block; background: #2E7D32; color: white; text-decoration: none; padding: 16px 32px; border-radius: 14px; font-weight: bold; font-size: 16px; box-shadow: 0 4px 12px rgba(46,125,50,0.3); transition: transform 0.2s; }}
        .btn:active {{ transform: scale(0.98); }}
        .badge {{ background: #E8F5E9; color: #2E7D32; padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; display: inline-block; margin-bottom: 16px; }}
    </style>
</head>
<body>
    <div class="card">
        <div class="logo">🌾</div>
        <div class="badge">Version 2.0 • AI & Models Active</div>
        <h1>Kisaan Dost App</h1>
        <p>Aapka kisaan dashboard, live satellite telemetry, crop disease AI model, aur mandi rates is APK mein shamil hain.</p>
        <a href="/app-debug.apk" class="btn">📲 Download & Install APK</a>
    </div>
</body>
</html>"""
            self.wfile.write(html.encode("utf-8"))
        elif self.path == "/app-debug.apk":
            if os.path.exists(APK_PATH):
                self.send_response(200)
                self.send_header("Content-type", "application/vnd.android.package-archive")
                self.send_header("Content-Disposition", 'attachment; filename="KisaanDost.apk"')
                self.send_header("Content-Length", str(os.path.getsize(APK_PATH)))
                self.end_headers()
                with open(APK_PATH, "rb") as f:
                    while chunk := f.read(65536):
                        self.wfile.write(chunk)
            else:
                self.send_error(404, "APK not found")
        else:
            self.send_error(404, "Not Found")

if __name__ == "__main__":
    with socketserver.TCPServer(("0.0.0.0", PORT), APKDownloadHandler) as httpd:
        print(f"Serving APK at http://192.168.1.7:{PORT}")
        httpd.serve_forever()
