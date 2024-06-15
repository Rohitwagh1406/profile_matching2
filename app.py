from flask import Flask, request, jsonify
import os
import json
from dotenv import load_dotenv
import google.generativeai as genai
import requests
import fitz
import boto3
from urllib.parse import urlparse
from botocore.exceptions import NoCredentialsError
from flask_cors import CORS
# from utils import extract_name, extract_email, extract_mobile_number

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://app.rework.club"}})
load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Constants
S3_BUCKET = 'sandbox-file-upload'
PDF_KEY = os.getenv("PDF_KEY")
# AWS credentials
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
AWS_REGION = os.getenv("AWS_REGION")

def get_text_from_pdf(pdf_data):
    pdf_document = fitz.open(stream=pdf_data, filetype="pdf")
    text = ""
    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        text += page.get_text()
    return text

def get_gemini_response(input):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(input)
    return response.text

def get_pdf_data_from_s3(bucket_name, object_name):
    try:
        # Create an S3 client
        s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY,
                          aws_secret_access_key=AWS_SECRET_KEY,
                          region_name=AWS_REGION)
        
        # Download the PDF file from S3 bucket to a local temporary file
        temp_pdf_path = './temp_pdf_file.pdf'  # Local path in current directory
        s3.download_file(bucket_name, object_name, temp_pdf_path)
        
        # Extract text from the downloaded PDF
        pdf_document = fitz.open(temp_pdf_path)
        text = ""
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text += page.get_text()
        
        # Print the extracted text
        print("Extracted text from the PDF:")
        return text
        
        # Clean up: Delete the temporary PDF file
        pdf_document.close()
        # Uncomment the line below if you want to delete the temporary file after extraction.
        # os.remove(temp_pdf_path)
        
    except NoCredentialsError:
        print("Credentials not available or incorrect.")

@app.route("/evaluate_resume", methods=["POST"])
def evaluate_resume():
    try:
        # Check if PDF file is uploaded
        if 'pdf_file' in request.files:
            pdf_file = request.files['pdf_file']
            pdf_data = pdf_file.read()
            resume_text = get_text_from_pdf(pdf_data)
        else:
            return jsonify({"error": "No PDF file uploaded"}), 400


        job_description = get_pdf_data_from_s3(S3_BUCKET, PDF_KEY)

        input_text = f"""
        You are a highly skilled ATS (Applicant Tracking System) with extensive experience in evaluating resumes for various engineering fields, including but not limited to software engineering, data science, data analysis, big data engineering, and others. Your task is to meticulously evaluate the provided resume against the given job description. The job market is highly competitive, and your assistance in enhancing the resume is crucial.
        Please provide a detailed analysis with the following components: Percentage Match: Indicate the overall match percentage between the resume and the job description. Consider the relevance and frequency of keywords, the alignment of skills and experience, and the presence of required qualifications.Missing Keywords: Identify any critical keywords that are absent from the resume but present in the job description. These could include specific technical skills, tools, methodologies, certifications, and job-specific terminology.Profile Summary: Offer a concise summary of the candidate's profile based on the resume content. Highlight key qualifications, experience, skills, and any notable achievements that are relevant to the job description.
        Ensure your evaluation takes into account the following sections of the resume and job description:
        Resume: Profile summary, work experience, education, skills, certifications, and any additional relevant sections.
        Job Description: Required qualifications, preferred qualifications, job responsibilities, technical skills, and any additional relevant sections.
        Here are the documents for review:
        Resume:
        {resume_text}
        Job Description:
        {job_description}
        I expect the response in one single string with the following structure:
        {{"JD Match":"%","MissingKeywords":[],"Profile Summary":""}}
        """
        response = get_gemini_response(input_text)

        # Parse the response string into a dictionary
        response_dict = json.loads(response)

        return jsonify(response_dict)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
