import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from database import get_db_connection

import warnings
warnings.filterwarnings('ignore', category=UserWarning)

def train_and_predict():
    print("Step 1/5: Connecting to MySQL Database...")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    print("Step 2/5: Fetching and preparing data...")
    cursor.execute("SELECT * FROM registrations")
    registrations = pd.DataFrame(cursor.fetchall())

    cursor.execute("SELECT student_id, cgpa, total_credits_completed, dept_id FROM students")
    students = pd.DataFrame(cursor.fetchall())

    cursor.execute("SELECT course_id, credits, dept_id FROM courses")
    courses = pd.DataFrame(cursor.fetchall())

    cursor.execute("SELECT course_id, prerequisite_course_id FROM prerequisites")
    prerequisites = pd.DataFrame(cursor.fetchall())

    df = registrations.merge(students, on='student_id', how='left')
    df = df.merge(courses, on='course_id', how='left', suffixes=('_student', '_course'))

    grade_map = {'AA':10, 'AB':9, 'BB':8, 'BC':7, 'CC':6, 'CD':5, 'DD':4, 'FF':0, 'W':0}
    completed = df[df['status'] == 'Completed'].copy()
    completed['grade_value'] = completed['grade'].map(grade_map)
    course_difficulty = completed.groupby('course_id')['grade_value'].mean().reset_index()
    course_difficulty.columns = ['course_id', 'course_avg_grade']

    df = df.merge(course_difficulty, on='course_id', how='left')
    df['course_avg_grade'] = df['course_avg_grade'].fillna(7.0)

    completed_grades = completed[['student_id', 'course_id', 'grade_value']].copy()
    completed_grades.columns = ['student_id', 'prerequisite_course_id', 'prereq_grade']
    df = df.merge(prerequisites, on='course_id', how='left')
    df = df.merge(completed_grades, on=['student_id', 'prerequisite_course_id'], how='left')
    df['prereq_grade'] = df['prereq_grade'].fillna(7.0)

    df = df[df['status'] != 'Dropped']
    def grade_to_risk(grade):
        if grade in ('AA', 'AB', 'BB'): return 0
        elif grade in ('BC', 'CC'): return 1
        elif grade in ('CD', 'DD', 'FF'): return 2
        else: return -1
    df['risk_label'] = df['grade'].apply(grade_to_risk)

    df_train = df[(df['status'] == 'Completed') & (df['total_credits_completed'] > 0)]
    feature_cols = ['cgpa', 'total_credits_completed', 'credits', 'course_avg_grade', 'prereq_grade']
    x_train = df_train[feature_cols]
    y_train = df_train['risk_label']

    print("Step 3/5: Training Logistic Regression...")
    scaler = StandardScaler()
    x_train_scaled = scaler.fit_transform(x_train)
    log_model = LogisticRegression(max_iter=1000)
    log_model.fit(x_train_scaled, y_train)

    print("Step 4/5: Generating predictions...")
    active_students = students[students['total_credits_completed'] > 0].copy()
    active_students['key'] = 1
    courses['key'] = 1
    df_pred = active_students.merge(courses, on='key').drop('key', axis=1)
    df_pred = df_pred[df_pred['dept_id_x'] == df_pred['dept_id_y']].copy()

    completed_subset = completed[['student_id', 'course_id']].copy()
    completed_subset['is_completed'] = True
    df_pred = df_pred.merge(completed_subset, on=['student_id', 'course_id'], how='left')
    df_pred = df_pred[df_pred['is_completed'].isnull()].copy()

    df_pred = df_pred.merge(course_difficulty, on='course_id', how='left')
    df_pred['course_avg_grade'] = df_pred['course_avg_grade'].fillna(7.0)
    df_pred = df_pred.merge(prerequisites, on='course_id', how='left')
    df_pred = df_pred.merge(completed_grades, on=['student_id', 'prerequisite_course_id'], how='left')
    df_pred['prereq_grade'] = df_pred['prereq_grade'].fillna(7.0)

    x_pred = df_pred[feature_cols]
    x_pred_scaled = scaler.transform(x_pred)
    predictions = log_model.predict(x_pred_scaled)
    df_pred['predicted_risk'] = predictions
    risk_names = {0: 'Low Risk', 1: 'Medium Risk', 2: 'High Risk'}
    df_pred['risk_level'] = df_pred['predicted_risk'].map(risk_names)

    print("Step 5/5: Pushing predictions to MySQL...")
    final_output = df_pred[['student_id', 'course_id', 'risk_level']].copy()
    final_output = final_output.drop_duplicates(subset=['student_id', 'course_id'])

    # Create table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ml_risk_scores (
            student_id INT,
            course_id INT,
            risk_level ENUM('Low Risk', 'Medium Risk', 'High Risk') NOT NULL,
            PRIMARY KEY (student_id, course_id),
            FOREIGN KEY (student_id) REFERENCES students(student_id),
            FOREIGN KEY (course_id) REFERENCES courses(course_id)
        )
    """)
    cursor.execute("TRUNCATE TABLE ml_risk_scores")

    # Insert predictions using mysql.connector (no SQLAlchemy needed)
    insert_sql = "INSERT INTO ml_risk_scores (student_id, course_id, risk_level) VALUES (%s, %s, %s)"
    rows = list(final_output.itertuples(index=False, name=None))
    cursor.executemany(insert_sql, rows)
    conn.commit()

    cursor.close()
    conn.close()
    print(f"Done! Successfully updated {len(rows)} predictions in the database.")

if __name__ == "__main__":
    train_and_predict()
