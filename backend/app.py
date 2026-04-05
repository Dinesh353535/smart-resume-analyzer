import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import tempfile

from extractor import extract_text_from_pdf, extract_sections
from scorer import calculate_ats_score
from aws_helper import upload_to_s3

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

app = Flask(__name__)
CORS(app)

ALLOWED_EXTENSIONS = {"pdf"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "ResumeAI API is running!", "status": "ok"})


@app.route("/analyze", methods=["POST"])
def analyze():
    if "resume" not in request.files:
        return jsonify({"error": "No resume file uploaded"}), 400

    file = request.files["resume"]
    job_description = request.form.get("job_description", "")

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    try:
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        # Extract text and sections
        raw_text = extract_text_from_pdf(tmp_path)
        if not raw_text:
            return jsonify({"error": "Could not extract text from PDF"}), 400

        sections = extract_sections(raw_text)

        # Calculate ATS score
        result = calculate_ats_score(sections, job_description)

        # Upload to S3
        s3_result = upload_to_s3(tmp_path, file.filename)

        # Cleanup temp file
        os.unlink(tmp_path)

        return jsonify({
            "success": True,
            "filename": file.filename,
            "s3_uploaded": s3_result.get("success", False),
            "s3_url": s3_result.get("url", ""),
            "ats_score": result["total_score"],
            "breakdown": result["breakdown"],
            "matched_keywords": result["matched_keywords"],
            "missing_keywords": result["missing_keywords"],
            "total_keywords_found": result["total_keywords_found"],
            "total_keywords_possible": result["total_keywords_possible"],
            "jd_mode": result["jd_mode"]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/history", methods=["GET"])
def history():
    from aws_helper import list_uploaded_resumes
    result = list_uploaded_resumes()
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, port=5000)