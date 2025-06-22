from flask import Flask, render_template, request, send_from_directory
import os
import subprocess
import json
from werkzeug.utils import secure_filename
import re

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
CLEANED_FOLDER = 'cleaned'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CLEANED_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def clean_metadata(input_path, output_path):
    subprocess.run([
        "ffmpeg", "-i", input_path,
        "-map_metadata", "-1", "-c", "copy",
        output_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def extract_metadata(file_path):
    result = subprocess.run([
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", file_path
    ], capture_output=True, text=True)
    return json.loads(result.stdout)


def extract_gps(metadata):
    tags = metadata.get('format', {}).get('tags', {})
    gps_data = {}

    loc = tags.get("location") or tags.get("com.apple.quicktime.location.ISO6709")
    if loc:
        match = re.match(r'([+-]\d+\.\d+)([+-]\d+\.\d+)', loc)
        if match:
            lat = float(match.group(1))
            lon = float(match.group(2))
            gps_data['latitude'] = lat
            gps_data['longitude'] = lon
            gps_data['link'] = f"https://www.google.com/maps?q={lat},{lon}"
    return gps_data if gps_data else None


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        files = request.files.getlist("file")
        results = []

        for file in files:
            if file.filename == "":
                continue
            filename = secure_filename(file.filename)
            upload_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(upload_path)

            cleaned_filename = f"cleaned_{filename}"
            cleaned_path = os.path.join(CLEANED_FOLDER, cleaned_filename)

            clean_metadata(upload_path, cleaned_path)
            metadata = extract_metadata(upload_path)
            gps_info = extract_gps(metadata)

            results.append({
                'original_filename': filename,
                'cleaned_filename': cleaned_filename,
                'metadata': metadata,
                'gps': gps_info
            })

        return render_template("result.html", results=results)

    return render_template("index.html")


@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(CLEANED_FOLDER, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0")
