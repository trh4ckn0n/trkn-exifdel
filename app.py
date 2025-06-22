from flask import Flask, render_template, request, send_from_directory
from werkzeug.utils import secure_filename
from PIL import Image
import piexif
import os
import subprocess
import json

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
CLEANED_FOLDER = "cleaned"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CLEANED_FOLDER, exist_ok=True)

def get_image_exif(image_path):
    try:
        exif_dict = piexif.load(image_path)
        readable = {}
        for ifd in exif_dict:
            for tag in exif_dict[ifd]:
                try:
                    key = piexif.TAGS[ifd][tag]["name"]
                    val = exif_dict[ifd][tag]
                    readable[key] = str(val)
                except:
                    pass
        return readable
    except:
        return {}

def get_video_metadata(video_path):
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', video_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return json.loads(result.stdout)
    except:
        return {}

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["media"]
        if not file:
            return "Aucun fichier."

        filename = secure_filename(file.filename)
        ext = filename.split(".")[-1].lower()
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)

        cleaned_name = f"cleaned_{filename}"
        cleaned_path = os.path.join(CLEANED_FOLDER, cleaned_name)

        metadata = {}
        if ext in ["jpg", "jpeg", "png"]:
            metadata = get_image_exif(path)
            image = Image.open(path)
            if ext == "png":
                data = list(image.getdata())
                new_image = Image.new(image.mode, image.size)
                new_image.putdata(data)
                new_image.save(cleaned_path)
            else:
                image.save(cleaned_path, "jpeg", exif=b"")
        elif ext in ["mp4", "mov", "avi", "webm", "mkv"]:
            metadata = get_video_metadata(path)
            subprocess.run(["ffmpeg", "-i", path, "-map_metadata", "-1", "-c", "copy", cleaned_path])
        else:
            return "Format non supporté."

        return render_template("result.html", filename=cleaned_name, metadata=metadata)
    return render_template("index.html")

@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(CLEANED_FOLDER, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(Debug=False, host="0.0.0.0")
