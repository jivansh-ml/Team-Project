from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import get_db_connection

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


if __name__ == '__main__':
    app.run(debug=True)
