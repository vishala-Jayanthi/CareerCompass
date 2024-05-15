from flask import Flask, render_template, request, redirect, url_for, session,flash, jsonify
from flask import current_app as app, flash, redirect, render_template, session
from flask_mysqldb import MySQL
import pandas as pd
import pickle
import PyPDF2 as pdf
import MySQLdb.cursors
import re
import os
import google.generativeai as genai

app = Flask(__name__)

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = '1a2b3c4d5e6d7g8h9i10'

# Enter your database connection details below
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '' #Replace ******* with  your database password.
app.config['MYSQL_DB'] = 'F'

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "D:\pijson.json"

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Intialize MySQL
mysql = MySQL(app)

# http://localhost:5000/pythonlogin/ - this will be the login page, we need to use both GET and POST requests
@app.route('/pythonlogin/', methods=['GET', 'POST'])
def login():
# Output message if something goes wrong...
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
        # Fetch one record and return result
        account = cursor.fetchone()
                # If account exists in users table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            # Redirect to home page
            return redirect(url_for('home'))
        else:
            # Account doesnt exist or username/password incorrect
            flash("Incorrect username/password!", "danger")
    return render_template('auth/login.html',title="Login")

# http://localhost:5000/pythonlogin/register 
# This will be the registration page, we need to use both GET and POST requests
@app.route('/pythonlogin/register', methods=['GET', 'POST'])
def register():
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
                # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # cursor.execute('SELECT * FROM users WHERE username = %s', (username))
        cursor.execute( "SELECT * FROM users WHERE username LIKE %s", [username] )
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            flash("Account already exists!", "danger")
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash("Invalid email address!", "danger")
        elif not re.match(r'[A-Za-z0-9]+', username):
            flash("Username must contain only characters and numbers!", "danger")
        elif not username or not password or not email:
            flash("Incorrect username/password!", "danger")
        else:
        # Account doesnt exists and the form data is valid, now insert new account into users table
            cursor.execute('INSERT INTO users VALUES (NULL, %s, %s, %s)', (username,email, password))
            mysql.connection.commit()
            flash("You have successfully registered!", "success")
            return redirect(url_for('login'))

    elif request.method == 'POST':
        # Form is empty... (no POST data)
        flash("Please fill out the form!", "danger")
    # Show registration form with message (if any)
    return render_template('auth/register.html',title="Register")

# http://localhost:5000/pythinlogin/home 
# This will be the home page, only accessible for loggedin users

@app.route('/')
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return render_template('home/home.html', username=session['username'],title="Home")
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))    

@app.route('/profile')
def profile():
    if 'loggedin' in session:
        # Fetch the performance data for the logged-in user
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM student_performance WHERE username = %s ORDER BY created_at DESC', (session['username'],))
        student_performance = cursor.fetchall()
        
        return render_template('auth/profile.html', username=session['username'], title="Profile", student_performance=student_performance)
    else:
        flash("Please login to access this page!", "danger")
        return redirect(url_for('login')) 

@app.route('/logout')
def logout():
    # Check if user is logged in
    if 'loggedin' in session:
        # Clear the session
        session.clear()
        # Print logout message
        print("Logged out successfully")
    # Redirect to the login page
    return redirect(url_for('login'))

@app.route('/study_plan', methods=['GET', 'POST'])
def study_plan():
    model = genai.GenerativeModel('gemini-pro')
    result = None
    if request.method == 'POST':
        area_of_interest = request.form['area_of_interest']
        course = request.form['course']
        programme = request.form['programme']
        days = request.form['days']
        time = request.form['time']
        question = f"Design a personalized study schedule tailored for students enrolled in the {programme} program, with a specialization in {course}. This schedule will address the topic of {area_of_interest} on designated days {days} at {time}. Additionally, include recommendations for supplementary courses relevant to {area_of_interest}, providing links for further exploration."
        response = model.generate_content(question)
        result = response.text
    return render_template('home/study_plan.html', result=result)

@app.route('/discussion_forum', methods=['GET', 'POST'])
def discussion_forum():
    if 'loggedin' not in session:
        return redirect('/login')  
    cur = mysql.connection.cursor()  

    if request.method == 'POST':
        username = session['username']
        message = request.form['message']
        reply_to = request.form.get('reply_to')  
        if reply_to == '':
            reply_to = None
        if reply_to is not None:
            cur.execute("SELECT id FROM messages WHERE id = %s", (reply_to,))
            if cur.fetchone() is None:
                return "Error: The specified reply_to ID does not exist."
        cur.execute("""
            INSERT INTO messages (username, message, reply_to)
            VALUES (%s, %s, %s)
        """, (username, message, reply_to))
        mysql.connection.commit()
        
    
    cur.execute("SELECT * FROM messages  ORDER BY created_at DESC")
    messages = cur.fetchall()
    return render_template('home/discussion_forum.html', username=session['username'], messages=messages)

@app.route('/student_performance', methods=['GET', 'POST'])
def student_performance():
    if request.method == 'POST':
        if 'loggedin' in session:
            if all(key in request.form for key in ['hours_studied', 'previous_scores', 'extracurricular_activities', 'sleep_hours', 'sample_question_papers_practiced']):
                # Extract form data
                hours_studied = int(request.form['hours_studied'])
                previous_scores = int(request.form['previous_scores'])
                extracurricular_activities = request.form['extracurricular_activities']
                sleep_hours = int(request.form['sleep_hours'])
                sample_question_papers_practiced = int(request.form['sample_question_papers_practiced'])
                
                
                # Load the trained model from the pickle file
                with open("student_performance_model.pkl", "rb") as f:
                    model = pickle.load(f)
                # Function to predict performance index
                def predict_performance(hours_studied, previous_scores, extracurricular_activities, sleep_hours,
                                        sample_question_papers_practiced):
                    # Convert extracurricular_activities to numerical value
                    extracurricular_activities_numeric = 1 if extracurricular_activities == 'Yes' else 0

                    input_data = pd.DataFrame({
                        'Hours Studied': [hours_studied],
                        'Previous Scores': [previous_scores],
                        'Extracurricular Activities': [extracurricular_activities_numeric],
                        'Sleep Hours': [sleep_hours],
                        'Sample Question Papers Practiced': [sample_question_papers_practiced]
                    })
                    prediction = model.predict(input_data)

                    if prediction < 50:
                        return "Need To Improve Performance"
                    elif prediction < 80:
                        return "Average Performance"
                    else:
                        return "High Performance"
                # Predict performance index
                performance_category = predict_performance(hours_studied, previous_scores, extracurricular_activities, sleep_hours, sample_question_papers_practiced)
                # Save data to the database
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('INSERT INTO  student_performance(username, hours_studied, previous_scores, extracurricular_activities, sleep_hours, sample_question_papers_practiced, performance_category,created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())',
                               (session['username'],hours_studied, previous_scores, extracurricular_activities, sleep_hours, sample_question_papers_practiced, performance_category))
                mysql.connection.commit()
                return render_template('home/student_performance.html', username=session['username'],
                                       title="Student Performance", performance_category=performance_category)
            else:
                flash("Please fill out all the fields!", "danger")
        else:
            flash("Please login to access this page!", "danger")
            return redirect(url_for('login'))

    # Render the template without performance result on initial GET request
    return render_template('home/student_performance.html', username=session['username'], title="Student Performance")

# Load the model and the vectorizer for resume category prediction
model = pickle.load(open('resume_category_classifier.pkl', 'rb'))
vectorizer = pickle.load(open('count_vectorizer.pkl', 'rb'))
job_labels = {
    0: 'Software Developer',
    1: 'Arts',
    2: 'Automation Testing',
    3: 'Blockchain',
    4: 'Business Analyst',
    5: 'Civil Engineer',
    6: 'Data Science',
    7: 'Database',
    8: 'DevOps Engineer',
    9: 'DotNet Developer',
    10: 'ETL Developer',
    11: 'Electrical Engineering',
    12: 'HR',
    13: 'Hadoop',
    14: 'Health and fitness',
    15: 'Java Developer',
    16: 'Mechanical Engineer',
    17: 'Network Security Engineer',
    18: 'Operations Manager',
    19: 'PMO',
    20: 'Python Developer',
    21: 'SAP Developer',
    22: 'Sales',
    23: 'Testing',
    24: 'Web Designing'
    # Add more job labels here
    # Add other job labels here
}

# Function to extract text from a PDF file for resume category prediction
def extract_text_from_pdf(file):
    pdf_reader = pdf.PdfReader(file)
    text = ''
    for page_num in range(len(pdf_reader.pages)):
        page_obj = pdf_reader.pages[page_num]
        text += page_obj.extract_text()
    return text

# Function to process text for resume category prediction
def process_text(raw_text):
    processed_text = vectorizer.transform([raw_text])
    return processed_text

@app.route('/resume_analysis', methods=['GET', 'POST'])
def resume_analysis():
    predicted_category = None
    if request.method == 'POST':
        file = request.files['file']
        if file:
            raw_text = extract_text_from_pdf(file)
            new_resume_features = process_text(raw_text)

            if new_resume_features is not None:
                result = model.predict(new_resume_features.toarray())[0]
                predicted_category = job_labels.get(result, "Unknown")
            else:
                return "Failed to process the text. Please try again."
    return render_template('home/resume_analysis.html', predicted_category=predicted_category, title="Resume Analysis")

# Prompt Template for Gemini model
input_prompt = """
Hey Act Like a skilled or very experienced ATS (Application Tracking System)
with a deep understanding of tech field, software engineering, data science, data analyst, Machine Learning,
Web Developer and big data engineer. Your task is to evaluate the resume based on the given job description.
You must consider the job market is very competitive and you should provide 
best assistance for improving the resumes. Assign the percentage Matching based 
on JD and the missing keywords with high accuracy and recommendations to improve resume.
resume: {text}
description: {jd}

I want the response in one single string having the structure
{{"JD Match": "%", "MissingKeywords": [], "Profile Summary": "", "Recommendations": ""}}
"""

# Function to generate response using Gemini model
def get_gemini_response(input_text, jd):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(input_text.format(text=jd, jd=jd))
    return response.text

@app.route('/resume_match', methods=['GET', 'POST'])
def resume_match():
    if request.method == 'POST':
        jd = request.form['job_description']
        uploaded_file = request.files['resume']

        if uploaded_file.filename != '':
            text = extract_text_from_pdf(uploaded_file)
            response = get_gemini_response(input_prompt, jd)
            return render_template('home/resume_match.html', response=response)
        else:
            return render_template('home/resume_match.html', message="Please upload a resume.")

    return render_template('home/resume_match.html', response=None)

if __name__ =='__main__':
	app.run(debug=True)
