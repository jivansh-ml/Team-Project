# Smart Course Registration Management System with Predictive Analytics

A **DBMS-based course registration system** designed to manage university course registration while providing data-driven academic support through Machine Learning.

## Problem Statement

University course registration involves many students competing for limited seats while satisfying rules such as prerequisites, credit limits, course capacity, and timetable constraints. Poorly managed registration can lead to overbooking, duplicate registrations, rule violations, and inconsistent records. Managing full courses also requires a fair waitlist mechanism.

This project develops a **DBMS-based course registration system** that ensures reliable registration through transactions, constraints, concurrency control, and audit logging.

The system is further enhanced with Machine Learning to:
- Recommend relevant courses using historical student-course interactions.
- Identify students who may be academically at risk using historical academic and course-related data.

## Features

- Student, Instructor and Admin management
- Course and section management
- Course registration and dropping
- Prerequisite validation
- Credit-limit validation
- Course capacity management
- Timetable clash detection
- Waitlist management with automatic promotion
- Transaction-based registration
- Audit logging
- Course recommendation
- Academic-risk prediction

## Database Implementation

The DBMS forms the core of the system and handles:

- Relational database design and normalization
- Primary and foreign keys
- Integrity constraints
- Transactions and concurrency control
- Stored procedures
- Triggers
- Views
- Indexing and query optimization
- Registration and waitlist management
- Audit logging

## Machine Learning

### 1. Course Recommendation

The recommendation module uses historical student-course interactions and course-related information to recommend potentially relevant courses.

The proposed approach includes:

- Eligibility filtering
- Item-based collaborative filtering
- Content-based course features
- Popularity-based fallback
- Predicted grade estimation

### 2. Academic Risk Prediction

The academic-risk module aims to identify students who may be at risk based on information available from their academic and course-related history.

Potential features include:

- CGPA
- Previous grades
- Credit load
- Course-related information
- Student activity and assessment information

Possible models include:

- Logistic Regression
- Decision Tree

## Dataset

The project uses the **Open University Learning Analytics Dataset (OULAD)** for both Machine Learning modules.

The dataset contains student demographics, course registrations, assessment results, and Virtual Learning Environment (VLE) interaction data.

### Course Recommendation
Historical student-course registrations, interactions, course information, and academic performance are used to build the course recommendation system.

### Academic Risk Prediction
Student academic performance, assessment results, registration information, and learning activity are used to build the academic-risk prediction model.

**Dataset:** [OULAD - Kaggle](https://www.kaggle.com/datasets/anlgrbz/student-demographics-online-education-dataoulad)

## Tech Stack

```text
Database         : MySQL
Backend          : Python / REST API
Machine Learning : Python, Pandas, NumPy, Scikit-learn
Frontend         : Web-based interface
Version Control  : Git / GitHub