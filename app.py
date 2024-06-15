from flask import Flask, request, jsonify
import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

app = Flask(__name__)

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_gemini_response(input):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(input)
    return response.text

@app.route("/evaluate_resume", methods=["POST"])
def evaluate_resume():
    resume_text = request.form.get('resume_text')
    job_description = request.form.get('job_description')
    
    input = f"""
    Hey, act like a skilled or very experienced ATS (Application Tracking System) 
    with a deep understanding of the tech field, specifically in software engineering, 
    data science, data analysis, and big data engineering. Your task is to thoroughly evaluate 
    the provided resume in comparison to the given job description. Keep in mind that 
    the job market is highly competitive, and your assistance in enhancing the resumes 
    is crucial. Provide a percentage match based on the job description and identify any 
    missing keywords with high accuracy. Please analyze the following documents:
    
    Resume:
    {resume_text}
    
    Job Description:
    {job_description}

    I expect the response in one single string with the following structure:
    {{"JD Match":"%","MissingKeywords:[]","Profile Summary":""}}
    """
    response = get_gemini_response(input)

    # Parse the response string into a dictionary
    response_dict = json.loads(response)

    return jsonify(response_dict)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
