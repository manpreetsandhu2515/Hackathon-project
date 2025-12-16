from flask import Flask, render_template, request
import pandas as pd
import os
from agents.main import clean_provider   # Gemini agent

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("file")

        if not file:
            return "No file uploaded", 400

        path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(path)

        df = pd.read_csv(path)
        results = []

        for _, row in df.iterrows():
            provider = row.to_dict()

            # Call Gemini-powered agent
            result = clean_provider(provider)

            results.append({
                **result.cleaned_data,
                "accuracy_score": result.accuracy_score,
                "issues": ", ".join(result.issues)
            })

        return render_template("results.html", results=results)

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
