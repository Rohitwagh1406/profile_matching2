from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
import google.generativeai as genai
import fitz
import boto3
from urllib.parse import urlparse
from botocore.exceptions import NoCredentialsError
import re
from flask_cors import CORS
# from utils import extract_name, extract_email, extract_mobile_number
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://app.rework.club"}})
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
# Constants
S3_BUCKET = 'sandbox-file-upload'
# PDF_KEY = os.getenv("PDF_KEY")
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
def extract_resume_skills(text):
    prompt = f"""
    **Resume Analysis:**
    The provided resume contains the following details:
    {text}
    Your task is to extract skills mentioned in the resume and organize them into a structured list.
    Ensure accuracy and completeness in the extracted information. You can use techniques like named entity recognition or keyword extraction for extraction.
    Return a list containing all skills. If no information is found, return an empty list.
    Example response structure:
    ["Python", "JavaScript", "Data Analysis", "Machine Learning", "PowerBI", "Excel", "Flask", "Project Management"]
    """
    response = get_gemini_response(prompt)
    # print(response)
    # skills_list = re.findall(r'\b[A-Za-z0-9]+\b', response)
    skills_list = re.findall(r'[A-Za-z0-9]+(?:\s+[A-Za-z0-9]+)*', response)
    unique_skills = list(set(skill for skill in skills_list))
    return unique_skills
def extract_resume_skills_two(text):
    prompt = f"""
    **Resume Analysis:**
    The provided resume contains the following details:
    {text}
    Your task is to extract skills mentioned in the resume and organize them into a structured list.
    Ensure accuracy and completeness in the extracted information. You can use techniques like named entity recognition or keyword extraction for extraction.
    Return a list containing all skills. If no information is found, return an empty list.
    Example response structure:
    ["Python", "JavaScript", "Data Analysis", "Machine Learning", "PowerBI", "Excel", "Flask", "Project Management"]
    """
    response = get_gemini_response(prompt)
    # print(response)
    # skills_list = re.findall(r'\b[A-Za-z0-9]+\b', response)
    skills_list = re.findall(r'[A-Za-z0-9]+(?:\s+[A-Za-z0-9]+)*', response)
    unique_skills = list(set(skill for skill in skills_list))
    return unique_skills
def evaluate_resume_skill_matching(resume_extracted_skills, resume_extracted_skills_two):
    # resume_keywords = set(resume_text.lower().split())
    # job_description_keywords = set(job_description.lower().split())
    # common_keywords = resume_extracted_skills & jd_extracted_skills
    common_skills = set(resume_extracted_skills) & set(resume_extracted_skills_two)
    return common_skills
def extract_jd_skills(text):
    prompt = f"""
    **Job Description Analysis:**
    The provided Job Description contains the following details:
    {text}
    Your task is to extract extract skills mentioned in the Job Description and organize them into a structured list.
    Ensure accuracy and completeness in the extracted information. You can use techniques like named entity recognition or keyword extraction for extraction.
    Return a list containing all extract skills. If no information is found, return an empty list.
    Example response structure:
    ["Python", "JavaScript", "Data Analysis", "Machine Learning", "PowerBI", "Excel", "Flask", "Project Management"]
    """
    response = get_gemini_response(prompt)
    # print(response)
    skills_list = re.findall(r'[A-Za-z0-9]+(?:\s+[A-Za-z0-9]+)*', response)
    # skills_list = re.findall(r'\b[A-Za-z0-9]+\b', response)
    unique_skills = list(set(skill for skill in skills_list))
    return unique_skills
def extract_jd_skills_two(text):
    prompt = f"""
    **Job Description Analysis:**

    The provided Job Description contains the following details:
    {text}
    Your task is to extract extract skills mentioned in the Job Description and organize them into a structured list.
    Ensure accuracy and completeness in the extracted information. You can use techniques like named entity recognition or keyword extraction for extraction.
    Return a list containing all extract skills. If no information is found, return an empty list.
    Example response structure:
    ["Python", "JavaScript", "Data Analysis", "Machine Learning", "PowerBI", "Excel", "Flask", "Project Management"]
    """
    response = get_gemini_response(prompt)
    # print(response)
    skills_list = re.findall(r'[A-Za-z0-9]+(?:\s+[A-Za-z0-9]+)*', response)
    # skills_list = re.findall(r'\b[A-Za-z0-9]+\b', response)
    unique_skills = list(set(skill for skill in skills_list))
    return unique_skills
def evaluate_jd_skill_matching(jd_extracted_skills, jd_extracted_skills_two):
    # resume_keywords = set(resume_text.lower().split())
    # job_description_keywords = set(job_description.lower().split())
    # common_keywords = resume_extracted_skills & jd_extracted_skills
    common_skills = set(jd_extracted_skills) & set(jd_extracted_skills_two)
    return common_skills
def evaluate_matching(resume_skills_final, jd_skills_final):
    # resume_keywords = set(resume_text.lower().split())
    # job_description_keywords = set(job_description.lower().split())
    # common_keywords = resume_extracted_skills & jd_extracted_skills
    common_skills = set(resume_skills_final) & set(jd_skills_final)
    match_percentage = len(common_skills) / len(jd_skills_final) * 100 if jd_skills_final else 0
    missing_skills = list(set(jd_skills_final) - common_skills)
    return {
        "JD Match": f"{match_percentage:.2f}%",
        "MissingKeywords": missing_skills
    }
def get_pdf_data_from_s3(bucket_name, object_name):
    try:
        s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY,
                          aws_secret_access_key=AWS_SECRET_KEY,
                          region_name=AWS_REGION)
        temp_pdf_path = './temp_pdf_file.pdf'
        s3.download_file(bucket_name, object_name, temp_pdf_path)
        pdf_document = fitz.open(temp_pdf_path)
        text = ""
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text += page.get_text()
        return text
        pdf_document.close()     
    except NoCredentialsError:
        print("Credentials not available or incorrect.")
@app.route("/evaluate_resume", methods=["POST"])
def evaluate_resume():
    try:
        if 'pdf_file' in request.files:
            pdf_file = request.files['pdf_file']
            pdf_data = pdf_file.read()
            resume_text = get_text_from_pdf(pdf_data)
        else:
            return jsonify({"error": "No PDF file uploaded"}), 400
        PDF_KEY = request.form.get("pdf_key")
        job_description = get_pdf_data_from_s3(S3_BUCKET, PDF_KEY)
        resume_extracted_skills = extract_resume_skills(resume_text)
        print("resume skills:")
        print(resume_extracted_skills)
        resume_extracted_skills_two = extract_resume_skills_two(resume_text)
        print("resume skill two:")
        print(resume_extracted_skills_two)
        resume_skills_final = evaluate_resume_skill_matching(resume_extracted_skills, resume_extracted_skills_two)
        print("resume skill final:")
        print(resume_skills_final)
        jd_extracted_skills = extract_jd_skills(job_description)
        print("jd skills :") 
        print(jd_extracted_skills)
        jd_extracted_skills_two = extract_jd_skills_two(job_description)
        print("jd skills two :") 
        print(jd_extracted_skills_two)
        jd_skills_final = evaluate_jd_skill_matching(jd_extracted_skills, jd_extracted_skills_two)
        print("jd skills :") 
        print(jd_skills_final)
        
        input_text=f"""
        You are a highly skilled ATS (Applicant Tracking System) with extensive experience in evaluating resumes for various engineering fields, including but not limited to software engineering, data science, data analysis, big data engineering, and others. Your task is to meticulously evaluate the provided resume against the given job description. The job market is highly competitive, and your assistance in enhancing the resume is crucial.
        Please provide a detailed analysis with the following components:
        Overall Profile Summary: A concise overview of the candidate's background, emphasizing transferable skills and experiences that are most relevant to the job description (e.g., "The candidate possesses X years of experience in data analysis with a strong foundation in Python and machine learning. Their experience in building data pipelines and working on customer churn prediction projects demonstrates their ability to handle similar tasks required in this role").
        Data Sources:
        Resume:
        {resume_text}
        Job Description:
        {job_description}
        Your response should follow this format:
        {"summary text"}

        """
        # "Profile Summary": "Candidate has relevant experience and skills as per the job description."
        evaluation_result = evaluate_matching(resume_skills_final, jd_skills_final)
        response = get_gemini_response(input_text)
        
        # print("evaluation result:")
        # print(evaluation_result)
        # json_response = {
        #     "evaluation_result": evaluation_result,
        #     "Profile Summary": response
        #     }
        json_response = {
            "JD Match": evaluation_result["JD Match"],
            "MissingKeywords": evaluation_result["MissingKeywords"],
            "Profile Summary": response
        }
        return jsonify(json_response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
