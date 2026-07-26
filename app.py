from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "NS Interior Studio AI is running!"

if __name__ == "__main__":
    app.run(debug=True)