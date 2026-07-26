from flask import Flask, render_template, request
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/studio")
def studio():
    return render_template("studio.html")

@app.route("/upload", methods=["POST"])
def upload():
    photo = request.files["room_photo"]
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], photo.filename)
    photo.save(save_path)
    return f"Photo uploaded successfully! Saved as {photo.filename}"
@app.route("/login")
def login():
    return render_template("login.html")
if __name__ == "__main__":
    app.run(debug=True)