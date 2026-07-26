from flask import Flask, render_template, request
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    photo = request.files["room_photo"]
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], photo.filename)
    photo.save(save_path)
    return f"Photo uploaded successfully! Saved as {photo.filename}"

if __name__ == "__main__":
    app.run(debug=True)