import os
import PyPDF2
import google.generativeai as genai
import speech_recognition as sr
import pyttsx3
import cv2
from flask import *
from reportlab.pdfgen import canvas
from reportlab.lib.colors import gold,darkblue
from reportlab.lib.pagesizes import letter
from flask import send_file
from flask_mail import Mail, Message
from flask import flash
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import random
import smtplib
import datetime
import subprocess
import pymysql
pymysql.install_as_MySQLdb()
#from google import genai
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, flash, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
genai.configure(api_key="AQ.Ab8RN6KarkNbZETgXKY1MZatW4kjDlJcPC1RfHHaap-EMWGzjg")
app.secret_key = "secretkey"

UPLOAD_FOLDER = 'static/uploads'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# MYSQL CONFIG

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '1234'
app.config['MYSQL_DB'] = 'ai_interview_platform'
#app.config['MYSQL_PORT'] = 3306

mysql = MySQL(app)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'kupendrareddy124@gmail.com'
app.config['MAIL_PASSWORD'] = 'jjfm jfct ocns lcsl'

mail = Mail(app)
# HOME

@app.route('/')
def home():
    return render_template('index.html')

# REGISTER

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        hashed_password = generate_password_hash(password)

        cur = mysql.connection.cursor()

        cur.execute(
            "INSERT INTO users(name,email,password) VALUES(%s,%s,%s)",
            (name, email, hashed_password)
        )

        mysql.connection.commit()
        cur.close()

        flash("Registration Successful")
        return redirect('/login')

    return render_template('register.html')

# LOGIN

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()

        cur.execute(
            "SELECT * FROM users WHERE email=%s AND password=%s",
            (email, password)
        )

        user = cur.fetchone()

        if user:

            session['user'] = user[1]
            flash("Login Successful")

            return redirect('/dashboard')

        else:

            return render_template(
                'login.html',
                message="Wrong Password"
            )

    return render_template('login.html')
# FORGOT PASSWORD
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():

    if request.method == 'POST':

        email = request.form['email']

        cur = mysql.connection.cursor()

        cur.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )

        user = cur.fetchone()

        if user:

            otp = str(random.randint(100000,999999))

            session['reset_email'] = email
            session['reset_otp'] = otp

            sender_email = "kupendrareddy124@gmail.com"
            sender_password = "jjfm jfct ocns lcsl"

            msg = MIMEText(f"Your OTP Code is: {otp}")

            msg['Subject'] = "Password Reset OTP"
            msg['From'] = sender_email
            msg['To'] = email

            server = smtplib.SMTP('smtp.gmail.com',587)

            server.starttls()

            server.login(sender_email, sender_password)

            server.sendmail(
                sender_email,
                email,
                msg.as_string()
            )

            server.quit()

            return redirect('/verify_otp')

        else:

            return "Email not found"

    return render_template('forgot_password.html')
@app.route('/verify_otp', methods=['GET','POST'])
def verify_otp():

    if request.method == 'POST':

        entered_otp = request.form['otp']

        if entered_otp == session.get('reset_otp'):

            return redirect('/reset_password')

        else:

            return "Invalid OTP"

    return render_template('verify_otp.html')
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():

    # user opened page directly
    if 'reset_email' not in session:
        return redirect('/forgot_password')

    if request.method == 'POST':

        new_password = request.form['password']
        confirm_password = request.form['confirm_password']

        # password match check
        if new_password != confirm_password:

            return render_template(
                'reset_password.html',
                message="Passwords do not match"
            )

        email = session['reset_email']

        cur = mysql.connection.cursor()

        # update password
        cur.execute(
            "UPDATE users SET password=%s WHERE email=%s",
            (new_password, email)
        )

        mysql.connection.commit()

        # remove session
        session.pop('reset_email', None)

        return redirect('/login')

    return render_template('reset_password.html')


UPLOAD_FOLDER = 'static/uploads'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/upload_profile', methods=['POST'])
def upload_profile():

    if 'user' not in session:
        return redirect('/login')

    file = request.files['profile_pic']

    if file:

        filename = secure_filename(file.filename)

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        file.save(filepath)

        cur = mysql.connection.cursor()

        cur.execute(
            "UPDATE users SET profile_pic=%s WHERE name=%s",
            (filename, session['user'])
        )

        mysql.connection.commit()

        cur.close()
        flash("Profile Picture Updated Successfully")

    return redirect('/dashboard')
@app.route('/dashboard')
def dashboard():

    if 'user' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute(
        "SELECT name, email, ats_score, profile_pic FROM users WHERE name=%s",
        (session['user'],)
    )

    user = cur.fetchone()

    # default values
    username = user[0]
    email = user[1]
    ats_score = user[2] if user[2] else 0
    profile_pic = user[3]

    # default profile image
    if not profile_pic:
        profile_pic = "default.png"

    # score history
    cur.execute(
        "SELECT score FROM quiz_scores WHERE username=%s",
        (session['user'],)
    )

    scores_data = cur.fetchall()

    scores = []

    for s in scores_data:
        scores.append(s[0])

    return render_template(

        'dashboard.html',

        username=username,
        email=email,
        ats_score=ats_score,
        profile_pic=profile_pic,
        scores=scores

    )
@app.route('/certificate')
def certificate():

    if 'user' not in session:
        return redirect('/login')

    username = session['user']

    pdf_name = f"{username}_certificate.pdf"

    c = canvas.Canvas(pdf_name, pagesize=letter)

    width, height = letter

    # Border
    c.setStrokeColor(gold)
    c.setLineWidth(8)
    c.rect(30, 30, width-60, height-60)

    # Title
    c.setFillColor(darkblue)
    c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(width/2, 700,
                        "Certificate of Completion")

    # Subtitle
    c.setFont("Helvetica", 18)
    c.drawCentredString(width/2, 640,
                        "This certificate is proudly awarded to")

    # Username
    c.setFillColor(gold)
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(width/2, 580, username)

    # Course Name
    c.setFillColor(darkblue)
    c.setFont("Helvetica", 18)
    c.drawCentredString(width/2, 520,
                        "For successfully completing")

    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width/2, 470,
                        "AI Interview Platform")

    # Date
    today = datetime.date.today()

    c.setFont("Helvetica", 14)
    c.drawString(80, 120,
                 f"Date: {today}")

    # Signature
    c.setFont("Helvetica-Bold", 16)
    c.drawString(420, 120,
                 "Director")

    c.line(400, 140, 520, 140)

    c.save()

    return send_file(pdf_name,
                     as_attachment=True)
@app.route('/send_certificate')
def send_certificate():

    if 'user' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    # GET USER EMAIL
    cur.execute(
        "SELECT email FROM users WHERE name=%s",
        (session['user'],)
    )

    user_data = cur.fetchone()

    if user_data:

        user_email = user_data[0]

        # PDF NAME
        pdf_name = "AI_Interview_Certificate.pdf"

        # CREATE PDF
        c = canvas.Canvas(
            pdf_name,
            pagesize=letter
        )

        width, height = letter


        # OUTER BORDER
        c.setStrokeColor(gold)

        c.setLineWidth(10)

        c.rect(
            30,
            30,
            width-60,
            height-60
        )


        # INNER BORDER
        c.setStrokeColor(darkblue)

        c.setLineWidth(3)

        c.rect(
            50,
            50,
            width-100,
            height-100
        )


        # TITLE
        c.setFillColor(gold)

        c.setFont(
            "Helvetica-Bold",
            34
        )

        c.drawCentredString(
            width/2,
            700,
            "CERTIFICATE"
        )

        c.setFont(
            "Helvetica-Bold",
            20
        )

        c.drawCentredString(
            width/2,
            660,
            "OF ACHIEVEMENT"
        )


        # PRESENTED TEXT
        c.setFillColor(darkblue)

        c.setFont(
            "Helvetica",
            18
        )

        c.drawCentredString(
            width/2,
            590,
            "THIS CERTIFICATE IS PROUDLY PRESENTED TO"
        )


        # USER NAME
        c.setFillColor(gold)

        c.setFont(
            "Helvetica-Bold",
            30
        )

        c.drawCentredString(
            width/2,
            530,
            session['user']
        )


        # DESCRIPTION
        c.setFillColor(darkblue)

        c.setFont(
            "Helvetica",
            18
        )

        c.drawCentredString(
            width/2,
            470,
            "For Successfully Completing"
        )

        c.setFont(
            "Helvetica-Bold",
            24
        )

        c.drawCentredString(
            width/2,
            430,
            "AI Interview Platform"
        )


        # FOOTER MESSAGE
        c.setFont(
            "Helvetica-Oblique",
            16
        )

        c.drawCentredString(
            width/2,
            360,
            "Keep Learning • Keep Growing • Keep Achieving"
        )


        # DATE
        today = datetime.date.today()

        c.setFont(
            "Helvetica",
            14
        )

        c.drawString(
            80,
            140,
            f"Date: {today}"
        )


        # SIGNATURE LINE
        c.line(
            420,
            160,
            540,
            160
        )

        c.setFont(
            "Helvetica-Bold",
            16
        )

        c.drawString(
            445,
            140,
            "Director"
        )

        c.save()


        # SEND EMAIL
        msg = Message(
            'AI Interview Platform Certificate',
            sender='yourgmail@gmail.com',
            recipients=[user_email]
        )

        msg.body = f'''
Hello {session['user']},

Congratulations!

You successfully completed the AI Interview Platform.

Keep learning and growing.

AI Interview Platform
'''


        # ATTACH PDF
        with open(pdf_name, "rb") as f:

            msg.attach(
                pdf_name,
                "application/pdf",
                f.read()
            )


        # SEND MAIL
        mail.send(msg)

        cur.close()

        return "Professional Certificate Sent Successfully"


    return "User Email Not Found"
# =========================
# RESUME UPLOAD + ATS SCORE
# =========================

@app.route('/upload_resume', methods=['GET', 'POST'])
def upload_resume():

    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':

        file = request.files['resume']

        if file:

            filename = secure_filename(file.filename)

            filepath = os.path.join(
                app.config['UPLOAD_FOLDER'],
                filename
            )

            file.save(filepath)

            # =====================
            # READ PDF
            # =====================

            text = ""

            if filename.endswith('.pdf'):

                pdf = open(filepath, 'rb')

                reader = PyPDF2.PdfReader(pdf)

                for page in reader.pages:
                    text += page.extract_text()

                pdf.close()

            # =====================
            # ATS KEYWORDS
            # =====================

            keywords = [
                'python',
                'java',
                'sql',
                'html',
                'css',
                'flask',
                'ai',
                'machine learning'
            ]

            score = 0

            text = text.lower()

            for word in keywords:

                if word in text:
                    score += 10

            if score > 100:
                score = 100

            # =====================
            # SAVE TO DATABASE
            # =====================

            cur = mysql.connection.cursor()

            cur.execute(
                """
                UPDATE users
                SET resume=%s,
                    ats_score=%s
                WHERE name=%s
                """,
                (
                    filename,
                    score,
                    session['user']
                )
            )

            mysql.connection.commit()

            cur.close()

            flash(f"Resume Uploaded! ATS Score: {score}")

            return redirect('/dashboard')

    return render_template('upload_resume.html')
quiz_questions = [

    {
        "question": "Python is?",
        "options": [
            "Programming Language",
            "Database",
            "Browser",
            "Operating System"
        ],
        "answer": "Programming Language"
    },

    {
        "question": "HTML stands for?",
        "options": [
            "HyperText Markup Language",
            "HighText Machine Language",
            "Home Tool Markup Language",
            "Hyperlinks Text Mark"
        ],
        "answer": "HyperText Markup Language"
    },

    {
        "question": "CSS is used for?",
        "options": [
            "Styling",
            "Database",
            "Backend",
            "Server"
        ],
        "answer": "Styling"
    }

]


@app.route('/quiz', methods=['GET', 'POST'])
def quiz():

    cur = mysql.connection.cursor()

    if request.method == 'POST':

        score = 0

        for q in quiz_questions:

            selected = request.form.get(q['question'])

            if selected == q['answer']:
                score += 1

        # SAVE SCORE
        cur.execute(
            "INSERT INTO scores(username, score) VALUES(%s,%s)",
            (session['user'], score)
        )

        mysql.connection.commit()

        # GET EMAIL
        cur.execute(
            "SELECT email FROM users WHERE name=%s",
            (session['user'],)
        )

        email_data = cur.fetchone()

        if email_data:

            user_email = email_data[0]

            msg = Message(
                'Quiz Result - AI Interview Platform',
                sender='kupendrareddy124@gmail.com',
                recipients=[user_email]
            )

            msg.body = f'''
Hello {session['user']},

Your quiz completed successfully.

Your Score: {score}

Thank You
AI Interview Platform
'''

            mail.send(msg)

        return render_template(
            'quiz_result.html',
            score=score
        )

    return render_template(
        'quiz.html',
        questions=quiz_questions
    )

@app.route('/compiler')
def compiler():

    return render_template('compiler.html')


@app.route('/run_code', methods=['POST'])
def run_code():

    code = request.form['code']

    language = request.form['language']

    output = ""

    try:

        # PYTHON

        if language == "python":

            with open("temp.py", "w") as file:

                file.write(code)

            result = subprocess.run(

                ["python", "temp.py"],

                capture_output=True,

                text=True

            )

            output = result.stdout

            if result.stderr:

                output = result.stderr


        # C++

        elif language == "cpp":

            with open("temp.cpp", "w") as file:

                file.write(code)

            compile_result = subprocess.run(

                ["g++", "temp.cpp", "-o", "temp"],

                capture_output=True,

                text=True

            )

            if compile_result.stderr:

                output = compile_result.stderr

            else:

                run_result = subprocess.run(

                    ["temp.exe"],

                    capture_output=True,

                    text=True

                )

                output = run_result.stdout


        # JAVA

        elif language == "java":

            with open("Main.java", "w") as file:

                file.write(code)

            compile_java = subprocess.run(

                ["javac", "Main.java"],

                capture_output=True,

                text=True

            )

            if compile_java.stderr:

                output = compile_java.stderr

            else:

                run_java = subprocess.run(

                    ["java", "Main"],

                    capture_output=True,

                    text=True

                )

                output = run_java.stdout

    except Exception as e:

        output = str(e)

    return output
@app.route('/score_history')
def score_history():

    if 'user' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    # Interview History

    cur.execute(
        """
        SELECT score, created_at
        FROM interview_results
        WHERE username=%s
        ORDER BY created_at DESC
        """,
        (session['user'],)
    )

    interview_history = cur.fetchall()

    # Quiz History

    cur.execute(
        """
        SELECT score, created_at
        FROM quiz_results
        WHERE username=%s
        ORDER BY created_at DESC
        """,
        (session['user'],)
    )

    quiz_history = cur.fetchall()

    cur.close()

    return render_template(
        'score_history.html',
        interview_history=interview_history,
        quiz_history=quiz_history
    )

# INTERVIEW QUESTIONS

questions = [
    {
        "question": "What is Python?",
        "answer": "programming language"
    },
    {
        "question": "HTML stands for?",
        "answer": "hypertext markup language"
    },
    {
        "question": "CSS is used for?",
        "answer": "styling"
    }
]

# INTERVIEW PAGE

@app.route('/interview', methods=['GET', 'POST'])
def interview():

    if 'user' not in session:
        return redirect('/login')

    questions = [

        {"question":"Tell me about yourself"},

        {"question":"What is Python?"},

        {"question":"Explain OOPs concepts"}

    ]

    if request.method == 'POST':

        score = 0

        # ANSWER CHECK

        for i in range(len(questions)):

            answer = request.form.get(f'answer{i}')

            if answer and len(answer) > 3:
                score += 10

        # GET USER EMAIL

        cur = mysql.connection.cursor()

        cur.execute(
            "SELECT email FROM users WHERE name=%s",
            (session['user'],)
        )

        email_data = cur.fetchone()

        email = email_data[0]

        # SAVE SCORE

        cur.execute(
            "INSERT INTO scores(username, score) VALUES(%s,%s)",
            (session['user'], score)
        )

        mysql.connection.commit()

        # SEND EMAIL

        msg = Message(

            'Interview Participation',

            sender='kupendrareddy124@gmail.com',

            recipients=[email]

        )

        msg.body = f'''
Hello {session['user']},

Thank you for participating in the AI Mock Interview.

Your Score: {score}

Keep practicing and improve your skills.

AI Interview Platform
'''

        mail.send(msg)

        cur.close()

        return render_template(
            'result.html',
            score=score
        )

    return render_template(
        'interview.html',
        questions=questions
    )
@app.route('/ai_questions', methods=['GET', 'POST'])
def ai_questions():

    questions = []

    if request.method == 'POST':

        skill = request.form['skill']

        try:

            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"Generate 5 interview questions for {skill}"
            )

            questions = response.text.split('\n')

        except Exception as e:

            questions = [str(e)]

    return render_template(
        'ai_questions.html',
        questions=questions
    )
# SCORE HISTORY

@app.route('/history')
def history():

    if 'user' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute(
        """
        SELECT score, created_at
        FROM interview_results
        WHERE username=%s
        """,
        (session['user'],)
    )

    results = cur.fetchall()

    cur.close()

    return render_template(
        'history.html',
        results=results
    )
# =========================
# LEADERBOARD
# =========================

@app.route('/leaderboard')
def leaderboard():

    cur = mysql.connection.cursor()

    # TOP QUIZ SCORES

    cur.execute(
        """
        SELECT username, score
        FROM quiz_results
        ORDER BY score DESC
        LIMIT 10
        """
    )

    quiz_leaders = cur.fetchall()

    # TOP INTERVIEW SCORES

    cur.execute(
        """
        SELECT username, score
        FROM interview_results
        ORDER BY score DESC
        LIMIT 10
        """
    )

    interview_leaders = cur.fetchall()

    cur.close()

    return render_template(
        'leaderboard.html',
        quiz_leaders=quiz_leaders,
        interview_leaders=interview_leaders
    )
@app.route('/resume_analyzer', methods=['GET','POST'])
def resume_analyzer():

    if 'user' not in session:
        return redirect('/login')

    result = ""

    score = 0

    if request.method == 'POST':

        file = request.files['resume']

        filepath = os.path.join(
            'static/resumes',
            file.filename
        )

        file.save(filepath)

        import PyPDF2

        text = ""

        with open(filepath, 'rb') as pdf_file:

            reader = PyPDF2.PdfReader(pdf_file)

            for page in reader.pages:

                text += page.extract_text()

        skills = [
            "python",
            "java",
            "sql",
            "html",
            "css",
            "flask",
            "machine learning"
        ]

        found_skills = []

        for skill in skills:

            if skill.lower() in text.lower():

                found_skills.append(skill)

        score = len(found_skills) * 10

        missing = []

        for skill in skills:

            if skill not in found_skills:

                missing.append(skill)

        result = f"""

        ATS Score: {score}/100

        Found Skills:
        {', '.join(found_skills)}

        Missing Skills:
        {', '.join(missing)}

        Tips:
        Add more technical skills and projects.
        """

    return render_template(
        'resume_analyzer.html',
        result=result
    )
@app.route('/hr_interview')
def hr_interview():

    if 'user' not in session:
        return redirect('/login')

    return render_template('hr_interview.html')
@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():

    answer = ""

    if request.method == 'POST':

        question = request.form['question']

        try:

            model = genai.GenerativeModel('gemini-2.0-flash')

            response = model.generate_content(question)

            answer = response.text

        except Exception as e:

            answer = str(e)

    return render_template(
        'chatbot.html',
        answer=answer
    )
# LOGOUT

@app.route('/logout')
def logout():

    session.pop('user', None)

    flash("Logged Out Successfully")

    return redirect('/login')
@app.route('/webcam')
def webcam():

    cap = cv2.VideoCapture(0)

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades +
        'haarcascade_frontalface_default.xml'
    )

    while True:

        success, frame = cap.read()

        if not success:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = face_cascade.detectMultiScale(
            gray,
            1.3,
            5
        )

        # FACE DETECTION

        if len(faces) == 0:

            cv2.putText(
                frame,
                "No Face Detected",
                (20,50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0,0,255),
                2
            )

        elif len(faces) > 1:

            cv2.putText(
                frame,
                "Multiple Persons Detected",
                (20,50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0,0,255),
                2
            )

        else:

            cv2.putText(
                frame,
                "Face Detected",
                (20,50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0,255,0),
                2
            )

        for (x,y,w,h) in faces:

            cv2.rectangle(
                frame,
                (x,y),
                (x+w,y+h),
                (255,0,0),
                2
            )

        cv2.imshow(
            "AI Interview Monitoring",
            frame
        )

        if cv2.waitKey(1) == 27:
            break

    cap.release()

    cv2.destroyAllWindows()

    return "Webcam Monitoring Closed"
@app.route('/voice_interview')
def voice_interview():

    if 'user' not in session:
        return redirect('/login')

    return render_template('voice_interview.html')
# =========================
# ADMIN LOGIN
# =========================

@app.route('/admin', methods=['GET', 'POST'])
def admin():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        if username == "admin" and password == "admin123":

            session['admin'] = True

            flash("Admin Login Successful")

            return redirect('/admin_dashboard')

        else:

            flash("Invalid Admin Credentials")

    return render_template('admin_login.html')

# =========================
# ADMIN DASHBOARD
# =========================

@app.route('/admin_dashboard')
def admin_dashboard():

    if 'admin' not in session:
        return redirect('/admin')

    cur = mysql.connection.cursor()

    # USERS

    cur.execute(
        """
        SELECT id, name, email
        FROM users
        """
    )

    users = cur.fetchall()

    # INTERVIEW RESULTS

    cur.execute(
        """
        SELECT username, score, created_at
        FROM interview_results
        ORDER BY created_at DESC
        """
    )

    interview_results = cur.fetchall()

    # QUIZ RESULTS

    cur.execute(
        """
        SELECT username, score, created_at
        FROM quiz_results
        ORDER BY created_at DESC
        """
    )

    quiz_results = cur.fetchall()

    cur.close()

    return render_template(
        'admin_dashboard.html',
        users=users,
        interview_results=interview_results,
        quiz_results=quiz_results
    )

# =========================
# DELETE USER
# =========================

@app.route('/delete_user/<int:id>')
def delete_user(id):

    if 'admin' not in session:
        return redirect('/admin')

    cur = mysql.connection.cursor()

    cur.execute(
        "DELETE FROM users WHERE id=%s",
        (id,)
    )

    mysql.connection.commit()

    cur.close()

    flash("User Deleted Successfully")

    return redirect('/admin_dashboard')

# =========================
# ADMIN LOGOUT
# =========================

@app.route('/admin_logout')
def admin_logout():

    session.pop('admin', None)

    flash("Admin Logged Out")

    return redirect('/admin')

# RUN

if __name__ == '__main__':
    app.run(debug=True)

