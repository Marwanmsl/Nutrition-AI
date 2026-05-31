# Nutrition AI Pro

Nutrition AI Pro is an AI-powered web application that analyzes medical reports and blood test data to generate personalized nutrition guidance and weekly diet plans. The system uses Large Language Models through Ollama to provide nutrition-focused recommendations while avoiding medical diagnosis and clinical decision-making.

## Features

* Medical report analysis using AI
* PDF report upload and text extraction
* Blood test and health parameter analysis
* Personalized weekly nutrition timetable generation
* Kerala and Indian food-based meal recommendations
* Real-time AI response streaming
* Downloadable PDF nutrition reports
* Report history tracking
* Modern responsive user interface
* Offline AI processing using Ollama

## Technology Stack

Backend

* Python
* Flask
* Ollama
* PyMuPDF (fitz)
* ReportLab

Frontend

* HTML5
* CSS3
* JavaScript

AI Model

* Gemma 3
* Qwen 2.5 (fallback model support)

## How It Works

1. User enters blood test values or uploads a medical report PDF.
2. The system extracts and processes report data.
3. AI analyzes nutritional aspects of the report.
4. A structured health summary is generated.
5. Possible nutritional concerns are identified.
6. A weekly diet plan is created using locally available Indian foods.
7. Users can download the report as a professionally formatted PDF.

## Generated Report Sections

* Health Summary
* Possible Nutritional Issues
* Weekly Diet Plan
* Foods to Avoid
* Lifestyle Tips

## Key Design Principles

* No disease diagnosis
* No medical prescriptions
* Nutrition-focused recommendations only
* Practical and affordable meal plans
* Kerala and Indian dietary preferences
* Easy-to-follow nutrition guidance

## Installation

1. Clone the repository.

2. Install dependencies:
   pip install -r requirements.txt

3. Install Ollama and pull the required model:
   ollama pull gemma3:4b-cloud

4. Run the application:
   python app.py

5. Open:
   http://localhost:5000

## Future Enhancements

* User authentication
* Nutrition tracking dashboard
* Multi-language support
* Health trend visualization
* Advanced PDF report formatting
* Cloud deployment support

## Disclaimer

This application provides nutrition guidance only and is not intended to diagnose, treat, cure, or prevent any disease. Users should consult qualified healthcare professionals for medical advice.
