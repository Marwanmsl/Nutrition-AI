from flask import Flask, render_template, request, jsonify, Response, send_file
import ollama
import subprocess
import time
import requests
import fitz
import io
import re
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from flask import send_file, request, jsonify
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)


app = Flask(__name__)

history = []


# =========================
# CLEAN TEXT (FIXED)
# =========================
def clean_text(text):
    text = re.sub(r"[#*_`>]", "", text)
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

# =========================
# START OLLAMA
# =========================
def start_ollama():
    try:
        requests.get("http://127.0.0.1:11434")
    except:
        subprocess.Popen(["ollama", "serve"],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
        time.sleep(5)


def ensure_model():
    try:
        ollama.chat(model="gemma3:4b-cloud",
                    messages=[{"role": "user", "content": "hi"}])
    except:
        subprocess.run(["ollama", "pull", "qwen2.5:7b"])


# =========================
# PDF TEXT EXTRACTION
# =========================
def extract_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text


# =========================
# PROMPT
# =========================
def build_prompt(data):

    return f"""
You are a professional nutrition assistant.

Analyze this medical report:

{data}

STRICT RULES:
-No diagnosis
-No medical claims beyond nutrition guidance
-No markdown symbols
-No stars (*)
-No bullet points
-No special characters formatting
-Use clean plain text only
-Do not add extra sections beyond the required format
-Create a weekly nutrition timetable
-Keep meals realistic, affordable, and practical for daily home cooking
-ONLY use locally available foods commonly found in India, especially Kerala region
-Use simple ingredients available in local markets and homes
-Prefer traditional Indian meals over foreign or processed foods
-Avoid imported, expensive, or uncommon ingredients unless absolutely necessary

You MUST include foods such as:
Rice, chapati, wheat roti, dosa, idli, puttu, upma, oats, ragi, milk, curd, buttermilk, eggs, chicken, fish, mutton, dal, lentils, chickpeas, green gram, coconut, coconut oil, vegetables like spinach, cabbage, carrot, beans, beetroot, ladies finger, tomato, onion, potato, cucumber, and fruits like banana, apple, orange, papaya, watermelon, pineapple, mango (seasonal), guava

Meals must reflect:
Balanced nutrition
Local Kerala/Indian food habits
Simple cooking methods like boiling, steaming, light frying, curry style cooking

FORMAT EXACTLY LIKE THIS:

Health Summary

Possible Nutritional Issues

Weekly Diet Plan

Monday
Breakfast:
Lunch:
Dinner:
Snacks:

Tuesday
Breakfast:
Lunch:
Dinner:
Snacks:

Wednesday
Breakfast:
Lunch:
Dinner:
Snacks:

Thursday
Breakfast:
Lunch:
Dinner:
Snacks:

Friday
Breakfast:
Lunch:
Dinner:
Snacks:

Saturday
Breakfast:
Lunch:
Dinner:
Snacks:

Foods to Avoid

Lifestyle Tips

"""


# =========================
# HOME
# =========================
@app.route("/")
def home():
    return render_template("index.html")


# =========================
# STREAM GENERATION (FIXED SPACING)
# =========================
@app.route("/generate", methods=["POST"])
def generate():
    user_input = request.form.get("prompt", "")
    prompt = build_prompt(user_input)

    def stream():
        full_text = ""

        response = ollama.chat(
            model="gemma3:4b-cloud",
            messages=[
                {"role": "system", "content": """
                You are a clinical nutrition decision-support assistant.

                Rules:
                - Do NOT diagnose diseases
                - Do NOT claim to be a doctor
                - Use evidence-based nutrition guidelines
                - Be cautious and conservative
                - If unsure, say "consult a qualified healthcare professional"
                - Structure output clearly for medical readability
                - Avoid hallucinated medical claims
                """},
                {"role": "user", "content": prompt}
            ],
            stream=True,
            options={"temperature": 0.3}
        )

        for chunk in response:
            if chunk.get("message"):
                text = chunk["message"]["content"]

                # 🔥 FIX 1: prevent word sticking
                if full_text and not full_text.endswith((" ", "\n")) and not text.startswith((" ", "\n")):
                    full_text += " "

                full_text += text

                yield text

        full_text = clean_text(full_text)

        history.append({
            "input": user_input,
            "output": full_text
        })

    return Response(stream(), content_type="text/plain")


# =========================
# PDF UPLOAD
# =========================
@app.route("/upload_pdf", methods=["POST"])
def upload_pdf():
    file = request.files["file"]
    text = extract_pdf(file)

    prompt = build_prompt(text)

    result = ollama.chat(
        model="gemma3:4b-cloud",
        messages=[
            {"role": "system", "content": "You are a medical nutrition expert."},
            {"role": "user", "content": prompt}
        ]
    )

    output = clean_text(result["message"]["content"])

    history.append({
        "input": "PDF REPORT",
        "output": output
    })

    return jsonify({"result": output})


# =========================
# SAFE PDF DOWNLOAD
# =========================
@app.route("/download_pdf", methods=["POST"])
def download_pdf():

    content = request.form.get("content", "")

    if not content or len(content.strip()) < 10:
        return jsonify({"error": "No content"}), 400

    # =========================
    # CLEAN TEXT
    # =========================
    content = re.sub(r"[#*_`>]", "", content)

    # =========================
    # PDF BUFFER
    # =========================
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        rightMargin=25,
        leftMargin=25,
        topMargin=25,
        bottomMargin=18
    )

    styles = getSampleStyleSheet()

    story = []

    # =========================
    # TITLE
    # =========================
    title = Paragraph(
        "<font size=18><b>Weekly Nutrition Report</b></font>",
        styles["Title"]
    )

    story.append(title)
    story.append(Spacer(1, 20))

    # =========================
    # EXTRACT GENERAL SECTIONS
    # =========================
    sections = {
        "Health Summary": "",
        "Possible Nutritional Issues": "",
        "Foods to Avoid": "",
        "Lifestyle Tips": ""
    }

    # =========================
    # WEEKLY PLAN
    # =========================
    weekly_plan = {
        "Monday": {"Breakfast": "", "Lunch": "", "Dinner": "", "Snacks": ""},
        "Tuesday": {"Breakfast": "", "Lunch": "", "Dinner": "", "Snacks": ""},
        "Wednesday": {"Breakfast": "", "Lunch": "", "Dinner": "", "Snacks": ""},
        "Thursday": {"Breakfast": "", "Lunch": "", "Dinner": "", "Snacks": ""},
        "Friday": {"Breakfast": "", "Lunch": "", "Dinner": "", "Snacks": ""},
        "Saturday": {"Breakfast": "", "Lunch": "", "Dinner": "", "Snacks": ""}
    }

    lines = content.split("\n")

    current_section = None
    current_day = None
    current_meal = None

    days = list(weekly_plan.keys())

    meals = ["Breakfast", "Lunch", "Dinner", "Snacks"]

    # =========================
    # PARSE CONTENT
    # =========================
    for line in lines:

        line = line.strip()

        if not line:
            continue

        # SECTION CHECK
        matched_section = False

        for sec in sections.keys():

            if sec.lower() == line.lower():

                current_section = sec
                current_day = None
                current_meal = None

                matched_section = True
                break

        if matched_section:
            continue

        # DAY CHECK
        if line in days:
            current_day = line
            current_section = None
            continue

        # MEAL CHECK
        for meal in meals:

            if line.startswith(meal + ":"):

                current_meal = meal

                value = line.replace(meal + ":", "").strip()

                if current_day:
                    weekly_plan[current_day][meal] += value

                break

        else:

            # CONTINUE MEAL CONTENT
            if current_day and current_meal:
                weekly_plan[current_day][current_meal] += " " + line

            elif current_section:
                sections[current_section] += line + "<br/>"

    # =========================
    # GENERAL SECTIONS TABLE
    # =========================
    general_data = [["Section", "Details"]]

    for section, details in sections.items():

        if details.strip():

            general_data.append([
                Paragraph(f"<b>{section}</b>", styles["BodyText"]),
                Paragraph(details, styles["BodyText"])
            ])

    general_table = Table(
        general_data,
        colWidths=[180, 320]
    )

    general_table.setStyle(TableStyle([

        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),

        ('GRID', (0, 0), (-1, -1), 1, colors.black),

        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),

        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),

        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),

        ('VALIGN', (0, 0), (-1, -1), 'TOP')

    ]))

    story.append(general_table)

    story.append(Spacer(1, 25))

    # =========================
    # WEEKLY PLAN TITLE
    # =========================
    plan_title = Paragraph(
        "<font size=16><b>Weekly Diet Plan</b></font>",
        styles["Heading2"]
    )

    story.append(plan_title)
    story.append(Spacer(1, 15))

    # =========================
    # WEEKLY TABLE
    # =========================
    weekly_data = [[
        "Day",
        "Breakfast",
        "Lunch",
        "Dinner",
        "Snacks"
    ]]

    for day, meals_data in weekly_plan.items():

        weekly_data.append([

            Paragraph(f"<b>{day}</b>", styles["BodyText"]),

            Paragraph(meals_data["Breakfast"], styles["BodyText"]),

            Paragraph(meals_data["Lunch"], styles["BodyText"]),

            Paragraph(meals_data["Dinner"], styles["BodyText"]),

            Paragraph(meals_data["Snacks"], styles["BodyText"])

        ])

    weekly_table = Table(
        weekly_data,
        colWidths=[70, 110, 110, 110, 110]
    )

    weekly_table.setStyle(TableStyle([

        # HEADER
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#166534")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),

        # GRID
        ('GRID', (0, 0), (-1, -1), 1, colors.black),

        # FONT
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),

        # ALIGN
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),

        # PADDING
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),

        # BODY COLOR
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige)

    ]))

    story.append(weekly_table)

    # =========================
    # BUILD PDF
    # =========================
    doc.build(story)

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="weekly_nutrition_plan.pdf",
        mimetype="application/pdf"
    )
# =========================
# HISTORY
# =========================
@app.route("/history")
def get_history():
    return jsonify(history)


if __name__ == "__main__":
    start_ollama()
    ensure_model()
    app.run(debug=True)