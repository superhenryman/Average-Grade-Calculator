import re
from flask import Flask, request, render_template
import os
try:
    from pypdf import PdfReader
except:
    os.system("pip install pypdf")
    from pypdf import PdfReader
app = Flask(__name__)
app.jinja_env.globals.update(zip=zip)


# Function to extract text from a PDF file
def extract_text_from_pdf(pdf_file):
    with open(pdf_file, 'rb') as f:
        reader = PdfReader(f)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return text


# Function to extract marks and calculate monthly averages
def extract_marks_and_calculate_avg(data):
    # Regular expression to capture the subject names and marks (we will ignore the first two columns)
    pattern = re.compile(
        r"([A-Za-z/ ]+)\s*(\d{2,3})\s*(\d{2,3})\s*(\d{2,3})\s*(\d{2,3})\s*(\d{2,3})\s*(\d{2,3})")

    subjects_data = []
    marks_data = []

    # Find all matches based on the pattern
    matches = re.findall(pattern, data)
    for match in matches:
        subject = match[0].strip()
        marks = list(map(int, match[3:7]))  # Only take the marks from the second, third, fourth, and final assessments
        subjects_data.append(subject)
        marks_data.append(marks)

    # Calculate the monthly averages (second month, third month, final, and first semester)
    monthly_averages = []
    for i in range(4):  # We have 4 months to calculate averages
        monthly_marks = [marks[i] for marks in marks_data]
        monthly_averages.append(sum(monthly_marks) / len(monthly_marks))
    monthly_averages[3] = monthly_averages[3] * 2.5 # better
    return subjects_data, marks_data, monthly_averages


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        if 'file' in request.files:
            file = request.files['file']

            # Ensure the uploaded file is a PDF
            if file.filename.endswith('.pdf'):
                # Save the file temporarily
                file.save("uploaded_file.pdf")

                # Extract text from the uploaded PDF
                text = extract_text_from_pdf("uploaded_file.pdf")

                # Extract marks and calculate averages
                subjects_data, marks_data, monthly_averages = extract_marks_and_calculate_avg(text)
                # Return the data to display in the result template
                os.remove("uploaded_file.pdf") # Delete Data.
                return render_template("result.html", subjects_data=subjects_data, marks_data=marks_data,
                                       monthly_averages=monthly_averages)
            else:
                return "Please upload a PDF file."

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
