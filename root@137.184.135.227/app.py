from flask import Flask, render_template, request, jsonify, send_from_directory
import subprocess
import os
import re
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR", "/app/downloads")
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# Basic URL validation
def is_valid_url(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http(s) or ftp
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("url")

    if not url or not is_valid_url(url):
        logging.warning(f"Invalid URL: {url}")
        return jsonify({"error": "Invalid URL"}), 400

    try:
        # Determine the download tool
        if "youtube.com" in url or "youtu.be" in url:
            tool = "yt-dlp"
            command = [tool, "-P", DOWNLOAD_DIR, url]
        elif "instagram.com" in url:
            tool = "gallery-dl"
            command = [tool, "-o", f"{DOWNLOAD_DIR}/%(title)s.%(ext)s", url]
        elif "tiktok.com" in url:
            tool = "gallery-dl"
            command = [tool, "-o", f"{DOWNLOAD_DIR}/%(title)s.%(ext)s", url]
        else:
            logging.warning(f"No suitable downloader found for: {url}")
            return jsonify({"error": "No suitable downloader found for this URL"}), 400

        logging.info(f"Downloading with {tool}: {url}")
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            logging.error(f"Download failed: {stderr}")
            return jsonify({"error": f"Download failed: {stderr}"}), 500

        # Basic file name extraction (improve as needed)
        downloaded_files = [f for f in os.listdir(DOWNLOAD_DIR) if os.path.isfile(os.path.join(DOWNLOAD_DIR, f))]
        if downloaded_files:
            logging.info(f"Download successful. Files: {downloaded_files}")
            return jsonify({"message": "Download successful", "files": downloaded_files})
        else:
            logging.warning("Download successful, but no files were created")
            return jsonify({"error": "Download successful, but no files were created"}), 500

    except FileNotFoundError as e:
        logging.error(f"Error: {e}. Ensure {tool} is installed.")
        return jsonify({"error": f"Error: {e}. Ensure the download tool is installed."}), 500
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {str(e)}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

@app.route('/downloads/<filename>')
def serve_download(filename):
    try:
        return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
