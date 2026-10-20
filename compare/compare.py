from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import json
import webbrowser

BASE_DIR = Path(__file__).resolve().parent
ORIGINAL_DIR = BASE_DIR / "original"
OUTPUT_DIR = BASE_DIR / "output"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}

ORIGINAL_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


class CompareHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/images.json":
            originals = {
                p.name.lower(): p.name
                for p in ORIGINAL_DIR.iterdir()
                if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
            }

            outputs = {
                p.name.lower(): p.name
                for p in OUTPUT_DIR.iterdir()
                if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
            }

            common = sorted(set(originals) & set(outputs))

            pairs = [
                {
                    "name": originals[name],
                    "original": f"original/{originals[name]}",
                    "output": f"output/{outputs[name]}",
                }
                for name in common
            ]

            data = json.dumps(pairs, ensure_ascii=False).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        return super().do_GET()


def main():
    host = "127.0.0.1"
    port = 8000

    print(f"Original: {ORIGINAL_DIR}")
    print(f"Output:   {OUTPUT_DIR}")
    print(f"Открываю: http://{host}:{port}")
    print("Для остановки нажми Ctrl+C")

    webbrowser.open(f"http://{host}:{port}")

    server = ThreadingHTTPServer((host, port), CompareHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()