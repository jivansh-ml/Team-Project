from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import get_db_connection
from datetime import date

app = Flask(__name__)
app.secret_key = 'smart_course_secret_key'

@app.route('/')
def index():
    if 'user_id' in session:
        if session['role'] == 'Student': return redirect(url_for('student_dashboard'))
        elif session['role'] == 'Instructor': return redirect(url_for('instructor_dashboard'))
        elif session['role'] == 'Admin': return redirect(url_for('admin_dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
    user = cursor.fetchone()
    
    if user:
        # Check if student has graduated
        if user['role'] == 'Student':
            cursor.execute("SELECT total_credits_completed FROM students WHERE student_id = %s", (user['user_id'],))
            student = cursor.fetchone()
            if student and student['total_credits_completed'] >= 140:
                flash("Your course duration is over (Graduated).")
                conn.close()
                return redirect(url_for('index'))

        session['user_id'] = user['user_id']
        session['role'] = user['role']
        conn.close()
        return redirect(url_for('index'))
    else:
        conn.close()
        flash("Invalid email or password")
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/student_dashboard')
def student_dashboard():
    if session.get('role') != 'Student': return redirect(url_for('index'))
    
    student_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 1. Fetch student profile
    cursor.execute("SELECT * FROM students WHERE student_id = %s", (student_id,))
    student = cursor.fetchone()
    
    # 2. Fetch current registrations + Risk
    query_registered = """
        SELECT r.registration_id, c.course_code, c.course_name, c.credits, r.status, m.risk_level
        FROM registrations r
        JOIN courses c ON r.course_id = c.course_id
        LEFT JOIN ml_risk_scores m ON r.student_id = m.student_id AND r.course_id = m.course_id
        WHERE r.student_id = %s AND r.status = 'Registered'
    """
    cursor.execute(query_registered, (student_id,))
    registered_courses = cursor.fetchall()
    
    # 3. Fetch available sections (courses they can take) + Risk
    query_available = """
        SELECT s.section_id, c.course_code, c.course_name, c.credits, s.schedule, m.risk_level
        FROM sections s
        JOIN courses c ON s.course_id = c.course_id
        LEFT JOIN ml_risk_scores m ON m.student_id = %s AND m.course_id = c.course_id
        WHERE c.dept_id = %s 
        AND s.semester = 'Fall 2026'
        AND c.course_id NOT IN (
            SELECT course_id FROM registrations WHERE student_id = %s AND status IN ('Completed', 'Registered')
        )
    """
    cursor.execute(query_available, (student_id, student['dept_id'], student_id))
    available_sections = cursor.fetchall()
    conn.close()
    
    return render_template('student_dashboard.html', 
                           student=student, 
                           courses=registered_courses,
                           available_sections=available_sections)

@app.route('/instructor_dashboard')
def instructor_dashboard():
    if session.get('role') != 'Instructor': return redirect(url_for('index'))
    
    instructor_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM instructors WHERE instructor_id = %s", (instructor_id,))
    instructor = cursor.fetchone()
    
    query = """
        SELECT s.section_id, c.course_code, c.course_name, s.semester, s.room_no, s.schedule
        FROM sections s
        JOIN courses c ON s.course_id = c.course_id
        WHERE s.instructor_id = %s AND s.semester = 'Fall 2026'
    """
    cursor.execute(query, (instructor_id,))
    sections = cursor.fetchall()
    
    for sec in sections:
        cursor.execute("""
            SELECT st.name, st.student_id, u.email
            FROM registrations r
            JOIN students st ON r.student_id = st.student_id
            JOIN users u ON st.student_id = u.user_id
            WHERE r.section_id = %s AND r.status = 'Registered'
        """, (sec['section_id'],))
        sec['students'] = cursor.fetchall()
        sec['enrolled_count'] = len(sec['students'])
        
    conn.close()
    
    return render_template('instructor_dashboard.html', instructor=instructor, sections=sections)

@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') != 'Admin': return redirect(url_for('index'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM departments")
    depts = cursor.fetchall()
    conn.close()
    
    return render_template('admin_dashboard.html', depts=depts)

@app.route('/admin_query', methods=['POST'])
def admin_query():
    if session.get('role') != 'Admin': return redirect(url_for('index'))
    
    query = request.form['sql_query'].strip()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(query)
        # If it's a SELECT query, fetch results
        if query.upper().startswith('SELECT') or query.upper().startswith('SHOW') or query.upper().startswith('DESC'):
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            message = f"Query returned {len(rows)} row(s)."
        else:
            conn.commit()
            columns = []
            rows = []
            message = f"Query executed successfully. Rows affected: {cursor.rowcount}"
    except Exception as e:
        columns = []
        rows = []
        message = f"Error: {e}"
    
    # Re-fetch departments for the dashboard
    cursor2 = conn.cursor(dictionary=True)
    cursor2.execute("SELECT * FROM departments")
    depts = cursor2.fetchall()
    conn.close()
    
    return render_template('admin_dashboard.html', depts=depts, 
                           columns=columns, rows=rows, message=message, last_query=query)

@app.route('/drop_course/<int:reg_id>', methods=['POST'])
def drop_course(reg_id):
    if session.get('role') != 'Student': return redirect(url_for('index'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    today = date.today().strftime('%Y-%m-%d')
    cursor.execute("UPDATE registrations SET status = 'Dropped', drop_date = %s WHERE registration_id = %s AND student_id = %s", (today, reg_id, session['user_id']))
    conn.commit()
    conn.close()
    flash("Course dropped successfully.")
    return redirect(url_for('student_dashboard'))

@app.route('/add_course', methods=['POST'])
def add_course():
    if session.get('role') != 'Student': return redirect(url_for('index'))
    
    section_id = request.form['section_id']
    student_id = session['user_id']
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT course_id, semester FROM sections WHERE section_id = %s", (section_id,))
    section = cursor.fetchone()
    
    if not section:
        flash("Invalid section ID.")
    else:
        cursor.execute("""
            SELECT SUM(c.credits) as total_credits
            FROM registrations r
            JOIN courses c ON r.course_id = c.course_id
            WHERE r.student_id = %s AND r.status = 'Registered' AND r.semester = 'Fall 2026'
        """, (student_id,))
        current_credits = cursor.fetchone()['total_credits'] or 0
        
        cursor.execute("SELECT credits FROM courses WHERE course_id = %s", (section['course_id'],))
        course_credits = cursor.fetchone()['credits']
        
        if current_credits + course_credits > 40:
            flash(f"Cannot register. Maximum 40 credits allowed per semester. You currently have {int(current_credits)} credits.")
        else:
            today = date.today().strftime('%Y-%m-%d')
            try:
                cursor.execute("""
                    INSERT INTO registrations (student_id, section_id, course_id, semester, status, registration_date)
                    VALUES (%s, %s, %s, %s, 'Registered', %s)
                """, (student_id, section_id, section['course_id'], section['semester'], today))
                conn.commit()
                flash("Successfully registered for course!")
            except Exception:
                flash("Error registering for course. You may already be registered.")
            
    conn.close()
    return redirect(url_for('student_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
