--  DATABASE: course_registration

CREATE DATABASE IF NOT EXISTS course_registration;
USE course_registration;

-- 1. departments
CREATE TABLE departments (
    dept_id INT PRIMARY KEY,
    dept_name VARCHAR(100) NOT NULL
);

-- 2. semesters
CREATE TABLE semesters (
    semester_id INT PRIMARY KEY,
    semester_name VARCHAR(20) NOT NULL UNIQUE,
    start_date DATE,
    end_date DATE,
    registration_open DATE,
    registration_close DATE,
    max_credits_allowed INT DEFAULT 44
);

-- 3. courses
CREATE TABLE courses (
    course_id INT PRIMARY KEY,
    course_code VARCHAR(10) NOT NULL UNIQUE,
    course_name VARCHAR(100) NOT NULL,
    credits INT NOT NULL,
    dept_id INT,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

-- 4. prerequisites
CREATE TABLE prerequisites (
    course_id INT,
    prerequisite_course_id INT,
    min_grade VARCHAR(2) DEFAULT 'DD',
    PRIMARY KEY (course_id, prerequisite_course_id),
    FOREIGN KEY (course_id) REFERENCES courses(course_id),
    FOREIGN KEY (prerequisite_course_id) REFERENCES courses(course_id)
);

-- 5. users
CREATE TABLE users (
    user_id INT PRIMARY KEY,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('Admin', 'Instructor', 'Student') NOT NULL,
    created_at DATE
);

-- 6. students (student_id references users)
CREATE TABLE students (
    student_id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    dept_id INT,
    phone VARCHAR(15),
    cgpa DECIMAL(4,2) DEFAULT 0.00,
    total_credits_completed INT DEFAULT 0,
    FOREIGN KEY (student_id) REFERENCES users(user_id),
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

-- 7. instructors (instructor_id references users)
CREATE TABLE instructors (
    instructor_id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    dept_id INT,
    specialization VARCHAR(100),
    FOREIGN KEY (instructor_id) REFERENCES users(user_id),
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

-- 8. sections
CREATE TABLE sections (
    section_id INT PRIMARY KEY,
    course_id INT,
    instructor_id INT,
    semester VARCHAR(20) NOT NULL,
    room_no VARCHAR(20),
    schedule VARCHAR(50),
    enrolled_count INT DEFAULT 0,
    FOREIGN KEY (course_id) REFERENCES courses(course_id),
    FOREIGN KEY (instructor_id) REFERENCES instructors(instructor_id)
);

-- 9. registrations

CREATE TABLE registrations (
    registration_id INT PRIMARY KEY,
    student_id INT,
    section_id INT,
    course_id INT,
    semester VARCHAR(20) NOT NULL,
    status ENUM('Registered', 'Completed', 'Dropped') NOT NULL,
    grade VARCHAR(2),
    registration_date DATE,
    drop_date VARCHAR(20),  
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (section_id) REFERENCES sections(section_id),
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);


-- 10. waitlist
CREATE TABLE waitlist (
    waitlist_id INT PRIMARY KEY,
    student_id INT,
    section_id INT,
    position INT,
    added_date DATE,
    status VARCHAR(20) DEFAULT 'Waiting',
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (section_id) REFERENCES sections(section_id)
);

-- 11. ml_risk_scores (stores ML predictions)
CREATE TABLE ml_risk_scores (
    score_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    course_id INT,
    semester VARCHAR(20),
    risk_level ENUM('Low Risk', 'Medium Risk', 'High Risk') NOT NULL,
    predicted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);
