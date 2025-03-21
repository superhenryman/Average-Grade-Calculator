import re
from flask import Flask, request, render_template
import os
import psycopg2
from io import BytesIO
try:
    from pypdf import PdfReader
except:
    os.system("pip install pypdf")
    from pypdf import PdfReader

app = Flask(__name__)
app.jinja_env.globals.update(zip=zip)


# Function to extract text from a PDF file
def extract_text_from_pdf(file_data):
    with BytesIO(file_data) as f:
        reader = PdfReader(f)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return text


# Function to extract marks and calculate monthly averages
def extract_marks_and_calculate_avg(data):
    pattern = re.compile(
        r"([A-Za-z/ ]+)\s*(\d{2,3})\s*(\d{2,3})\s*(\d{2,3})\s*(\d{2,3})\s*(\d{2,3})\s*(\d{2,3})")

    subjects_data = []
    marks_data = []

    matches = re.findall(pattern, data)
    for match in matches:
        subject = match[0].strip()
        marks = list(map(int, match[3:7]))  # Only take the marks from the second, third, fourth, and final assessments
        subjects_data.append(subject)
        marks_data.append(marks)

    monthly_averages = []
    for i in range(4):  # We have 4 months to calculate averages
        monthly_marks = [marks[i] for marks in marks_data]
        monthly_averages.append(sum(monthly_marks) / len(monthly_marks))
    monthly_averages[3] = monthly_averages[3] * 2.5  # Adjust the final month's average for your formula
    return subjects_data, marks_data, monthly_averages


# Function to save the PDF to the database
def save_pdf_to_db(file_data, file_name, ip):
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS uploaded_files(id SERIAL PRIMARY KEY, ip_addr TEXT NOT NULL, file_name VARCHAR(255), file_data BYTEA)")
    conn.commit()
    cursor.close()
    conn.close()

    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO uploaded_files (file_name, file_data, ip_addr) VALUES (%s, %s, %s)",(file_name, file_data, ip,))
    conn.commit()
    cursor.close()
    conn.close()


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        if 'file' in request.files:
            ip = request.remote_addr  # Fix the typo here
            file = request.files['file']

            # Ensure the uploaded file is a PDF
            if file.filename.endswith('.pdf'):
                # Save the file data temporarily
                file_data = file.read()

                # Save the PDF file to the database
                save_pdf_to_db(file_data, file.filename, ip)

                # Extract text from the uploaded PDF
                text = extract_text_from_pdf(file_data)  # Pass file data here
                
                # Extract marks and calculate averages
                subjects_data, marks_data, monthly_averages = extract_marks_and_calculate_avg(text)

                # Return the data to display in the result template
                return render_template("result.html", subjects_data=subjects_data, marks_data=marks_data,
                                       monthly_averages=monthly_averages)
            else:
                return "Please upload a PDF file."

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
