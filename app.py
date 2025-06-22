from flask import Flask, render_template, request, send_from_directory
from werkzeug.utils import secure_filename
from PIL import Image
import piexif
import os
import subprocess

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
CLEANED_FOLDER = "cleaned"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CLEANED_FOLDER, exist_ok=True)

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

        if ext in ["jpg", "jpeg"]:
            image = Image.open(path)
            image.save(cleaned_path, "jpeg", exif=b"")
        elif ext in ["png"]:
            image = Image.open(path)
            data = list(image.getdata())
            image_no_exif = Image.new(image.mode, image.size)
            image_no_exif.putdata(data)
            image_no_exif.save(cleaned_path)
        elif ext in ["mp4", "mov", "avi", "webm", "mkv"]:
            # Remove metadata with ffmpeg
            subprocess.run(["ffmpeg", "-i", path, "-map_metadata", "-1", "-c", "copy", cleaned_path])
        else:
            return "Format non supporté."

        return render_template("result.html", filename=cleaned_name)
    return render_template("index.html")

@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(CLEANED_FOLDER, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0")
