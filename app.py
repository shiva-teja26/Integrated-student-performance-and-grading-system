from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://flaskuser:yourpassword@localhost/student_performance'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=True)
    student = db.relationship('Student', backref='user', uselist=False)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    roll = db.Column(db.Integer, unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    marks = db.relationship("Mark", backref="student", lazy=True, cascade="all, delete-orphan")

class Semester(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey('semester.id'), nullable=False)
    semester = db.relationship('Semester', backref=db.backref('subjects', lazy=True))

class Mark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey('semester.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    marks = db.Column(db.Integer, nullable=False)
    subject = db.relationship('Subject', backref='marks')
    semester = db.relationship('Semester', backref='marks')
    
class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.Text, nullable=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def init_db():
    db.create_all()
    semesters = ['1-1', '1-2', '2-1', '2-2', '3-1', '3-2', '4-1', '4-2']
    for sem in semesters:
        if not Semester.query.filter_by(code=sem).first():
            db.session.add(Semester(code=sem))
    db.session.commit()

def calculate_student_data(student):
    """Calculate comprehensive student performance data"""
    semesters, sgpas = {}, {}
    total_marks = total_subjects = 0
    
    for mark in student.marks:
        subject = mark.subject
        semester_code = subject.semester.code
        if semester_code not in semesters:
            semesters[semester_code] = {}
        semesters[semester_code][subject.name] = mark.marks

    for sem_code, subjects in semesters.items():
        if subjects:
            sgpa = sum(subjects.values()) / len(subjects)
            sgpas[sem_code] = round(sgpa, 2)
            total_marks += sum(subjects.values())
            total_subjects += len(subjects)

    backlogs = sum(1 for mark in student.marks if mark.marks < 40)
    
    return {
        "id": student.id, "name": student.name, "roll": student.roll,
        "gender": student.gender, "semesters": semesters, "sgpas": sgpas,
        "cgpa": round(total_marks / total_subjects, 2) if total_subjects else 0.0,
        "backlogs": backlogs
    }

def find_student_by_user(username, user_id=None):
    """Find student by username or user relationship"""
    if user_id and current_user.student_id:
        return Student.query.get(current_user.student_id)
    try:
        return Student.query.filter_by(roll=int(username)).first()
    except ValueError:
        return Student.query.filter(Student.name.ilike(f"%{username}%")).first()

def get_grade(mark):
    try:
        mark = float(mark)
        if mark >= 90: return 'A+'
        elif mark >= 80: return 'A'
        elif mark >= 70: return 'B+'
        elif mark >= 60: return 'B'
        elif mark >= 50: return 'C'
        elif mark >= 40: return 'D'
        else: return 'F'
    except (ValueError, TypeError):
        return 'N/A'

app.jinja_env.globals.update(get_grade=get_grade)

# Helper function for authorization
def check_permission(roles):
    return current_user.role in roles

# Helper function to validate role access
def validate_role_access(requested_role, user_role):
    """Validate if user can access the requested portal"""
    role_mapping = {
        'admin': ['admin'],
        'faculty': ['teacher'],
        'student': ['student']
    }
    
    allowed_roles = role_mapping.get(requested_role, [])
    return user_role in allowed_roles

# Routes
@app.route("/")
def select_role():
    return render_template("role_selection.html")

@app.route("/home")
@login_required
def home():
    """Redirect to appropriate dashboard based on role"""
    if current_user.role == "teacher":
        return redirect(url_for("teacher_dashboard"))
    elif current_user.role == "student":
        return redirect(url_for("student_dashboard"))
    else:
        return redirect(url_for("dashboard"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username, password, role = request.form["username"], request.form["password"], request.form["role"]
        
        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
        else:
            hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
            new_user = User(username=username, password=hashed_password, role=role)
            
            if role == "student":
                student = find_student_by_user(username)
                if student:
                    new_user.student_id = student.id
            
            db.session.add(new_user)
            db.session.commit()
            flash("Signup successful!", "success")
            return redirect(url_for("login"))
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        requested_portal = request.form.get("role", "student")  # The portal they're trying to access
        
        user = User.query.filter_by(username=username).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            # Validate if user's role matches the portal they're trying to access
            if not validate_role_access(requested_portal, user.role):
                # Create role-specific error messages
                if requested_portal == "admin":
                    flash("Access denied. Only administrators can access the admin portal.", "danger")
                elif requested_portal == "faculty":
                    flash("Access denied. Only faculty members can access the faculty portal.", "danger")
                elif requested_portal == "student":
                    flash("Access denied. Only students can access the student portal.", "danger")
                else:
                    flash("Access denied. Invalid portal selection.", "danger")
                
                # Redirect back to login with the same role parameter
                return redirect(url_for("login", role=requested_portal))
            
            # If validation passes, log in the user
            login_user(user)
            session.update({"username": user.username, "role": user.role})
            return redirect(url_for("home"))
        else:
            flash("Invalid username or password.", "danger")
    
    # GET request - show the form
    role = request.args.get("role", "student").lower()
    # Validate the role parameter
    valid_roles = ["admin", "faculty", "student"]
    if role not in valid_roles:
        role = "student"
    
    return render_template("login.html", role=role)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("login"))

@app.route("/student_dashboard")
@login_required
def student_dashboard():
    """Dedicated route for student dashboard"""
    if current_user.role != "student":
        flash("Access denied. Students only.", "danger")
        return redirect(url_for("dashboard"))
    
    # Find the student record linked to this user
    student = None
    if current_user.student_id:
        student = Student.query.get(current_user.student_id)
    else:
        # Try to find by username (assuming username is roll number)
        try:
            student = Student.query.filter_by(roll=int(current_user.username)).first()
            if student:
                # Link the student to user account
                current_user.student_id = student.id
                db.session.commit()
        except ValueError:
            # Username is not a roll number, try by name
            student = Student.query.filter(Student.name.ilike(f"%{current_user.username}%")).first()
            if student:
                current_user.student_id = student.id
                db.session.commit()
    
    if not student:
        flash("No student record found. Please contact administrator to link your account.", "warning")
        return render_template('student_dashboard.html', 
                             student=None, 
                             username=current_user.username, 
                             role=current_user.role, 
                             graph_url=None)
    
    # Calculate student data
    student_data = calculate_student_data(student)
    all_marks = [mark.marks for mark in student.marks]
    
    # Calculate performance statistics
    if all_marks:
        student_data['performance_stats'] = {
            'highest_mark': max(all_marks),
            'lowest_mark': min(all_marks),
            'average_mark': round(sum(all_marks) / len(all_marks), 2),
            'total_subjects': len(all_marks),
            'subjects_passed': len([mark for mark in all_marks if mark >= 40]),
            'subjects_failed': sum(1 for mark in all_marks if mark < 40)
        }
        
        # Generate performance chart
        try:
            subjects = [f"{mark.subject.name}" for mark in student.marks]
            marks = [mark.marks for mark in student.marks]
            semesters = [mark.subject.semester.code for mark in student.marks]
            
            plt.figure(figsize=(12, 8))
            
            # Color bars based on pass/fail
            colors = ['#10B981' if mark >= 40 else '#EF4444' for mark in marks]
            bars = plt.bar(range(len(subjects)), marks, color=colors)
            
            plt.title(f"{student.name}'s Performance Overview (Roll: {student.roll})", 
                     fontsize=16, fontweight='bold', pad=20)
            plt.xlabel('Subjects', fontweight='bold')
            plt.ylabel('Marks', fontweight='bold')
            
            # Create labels with semester info
            labels = [f"{subj}\n(Sem {sem})" for subj, sem in zip(subjects, semesters)]
            plt.xticks(range(len(subjects)), labels, rotation=45, ha='right')
            
            # Add value labels on bars
            for i, bar in enumerate(bars):
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + 1,
                        f'{marks[i]}', ha='center', va='bottom', fontweight='bold')
            
            plt.axhline(y=40, color='red', linestyle='--', alpha=0.7, label='Passing Mark (40)')
            plt.grid(axis='y', alpha=0.3)
            plt.tight_layout()
            plt.legend()
            
            img = io.BytesIO()
            plt.savefig(img, format='png', dpi=300, bbox_inches='tight')
            img.seek(0)
            graph_url = base64.b64encode(img.getvalue()).decode()
            plt.close()
            
        except Exception as e:
            print(f"Error generating chart: {e}")
            graph_url = None
    else:
        student_data['performance_stats'] = {
            'highest_mark': 0,
            'lowest_mark': 0,
            'average_mark': 0,
            'total_subjects': 0,
            'subjects_passed': 0,
            'subjects_failed': 0
        }
        graph_url = None
    
    return render_template('student_dashboard.html', 
                          student=student_data, 
                          username=current_user.username, 
                          role=current_user.role, 
                          graph_url=graph_url)

@app.route("/teacher_dashboard")
@login_required
def teacher_dashboard():
    if not check_permission(["teacher"]):
        flash("Access denied. Teachers only.", "danger")
        return redirect(url_for("dashboard"))
    
    students = Student.query.order_by(Student.roll.asc()).all()
    student_records = [calculate_student_data(s) for s in students]
    
    return render_template('teacher_dashboard.html', students=student_records, 
                         username=current_user.username, role=current_user.role)

@app.route("/dashboard")
@login_required
def dashboard():
    """General dashboard - redirects to role-specific dashboards"""
    if current_user.role == "teacher":
        return redirect(url_for("teacher_dashboard"))
    elif current_user.role == "student":
        return redirect(url_for("student_dashboard"))
    else:
        # Admin dashboard
        students = Student.query.order_by(Student.roll.asc()).all()
        student_records = [calculate_student_data(s) for s in students]
        
        return render_template('dashboard.html', 
                             students=student_records, 
                             role=current_user.role, 
                             username=current_user.username)

@app.route("/add_student", methods=["GET", "POST"])
@login_required
def add_student():
    if not check_permission(["admin", "teacher"]):
        flash("Access denied. Insufficient permissions.", "danger")
        return redirect(url_for("dashboard"))
    
    if request.method == "POST":
        name = request.form.get('name')
        roll = request.form.get('roll')
        gender = request.form.get('gender')
        semester_code = request.form.get('semester')

        # Validate required fields
        if not all([name, roll, gender, semester_code]):
            flash("All fields are required.", "danger")
            return redirect(url_for('add_student'))

        # Check if student with this roll number already exists
        if Student.query.filter_by(roll=roll).first():
            flash("Student with this roll number already exists.", "danger")
            return redirect(url_for('add_student'))

        try:
            # Create new student
            student = Student(name=name, roll=int(roll), gender=gender)
            db.session.add(student)
            db.session.flush()  # Get the student ID

            # Get or create semester
            semester_obj = Semester.query.filter_by(code=semester_code).first()
            if not semester_obj:
                semester_obj = Semester(code=semester_code)
                db.session.add(semester_obj)
                db.session.flush()

            # Get subjects and marks from form
            subject_names = request.form.getlist('subjects[]')
            marks_list = request.form.getlist('marks[]')

            # Process each subject and mark
            for subject_name, mark_value in zip(subject_names, marks_list):
                if subject_name.strip() and mark_value.strip():  # Skip empty entries
                    try:
                        mark_int = int(mark_value)
                        if 0 <= mark_int <= 100:  # Validate mark range
                            
                            # Get or create subject
                            subject = Subject.query.filter_by(
                                name=subject_name.strip(), 
                                semester_id=semester_obj.id
                            ).first()
                            
                            if not subject:
                                subject = Subject(
                                    name=subject_name.strip(), 
                                    semester_id=semester_obj.id
                                )
                                db.session.add(subject)
                                db.session.flush()
                            
                            # Add mark
                            mark_entry = Mark(
                                student_id=student.id,
                                subject_id=subject.id,
                                semester_id=semester_obj.id,
                                marks=mark_int
                            )
                            db.session.add(mark_entry)
                        else:
                            flash(f"Invalid mark value for {subject_name}. Marks should be between 0-100.", "warning")
                    except ValueError:
                        flash(f"Invalid mark value for {subject_name}. Please enter a valid number.", "warning")
                        continue

            # Link existing user account if exists
            user = User.query.filter_by(username=str(roll), role="student").first()
            if user:
                user.student_id = student.id

            db.session.commit()
            flash(f"Student '{name}' added successfully with Roll Number {roll}.", "success")
            return redirect(url_for("teacher_dashboard" if current_user.role == "teacher" else "dashboard"))
            
        except ValueError as ve:
            db.session.rollback()
            flash("Invalid roll number format.", "danger")
            return redirect(url_for('add_student'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding student: {str(e)}", "danger")
            return redirect(url_for('add_student'))

    # GET request - show the form
    semesters = Semester.query.all()
    return render_template("add_student.html", 
                          subjects_by_sem={sem.code: sem.subjects for sem in semesters},
                          username=current_user.username, 
                          role=current_user.role)

@app.route('/edit_student/<int:roll>', methods=['GET', 'POST'])
@login_required
def edit_student(roll):
    if not check_permission(["admin", "teacher"]):
        flash("Access denied. Insufficient permissions.", "danger")
        return redirect(url_for("dashboard"))
    
    student = Student.query.filter_by(roll=roll).first_or_404()

    if request.method == 'POST':
        try:
            student.name = request.form['name']
            new_roll = int(request.form['roll'])
            
            existing_student = Student.query.filter_by(roll=new_roll).first()
            if existing_student and existing_student.id != student.id:
                flash("A student with this roll number already exists.", "danger")
                return redirect(url_for('edit_student', roll=roll))
            
            student.roll = new_roll
            student.gender = request.form['gender']
            
            Mark.query.filter_by(student_id=student.id).delete()

            # Process dynamic subjects and marks
            for key in request.form:
                if key.startswith('dynamic_subjects[') and key.endswith('][]'):
                    start, end = key.find('[') + 1, key.find(']')
                    sem_code = key[start:end]
                    
                    subjects = request.form.getlist(f'dynamic_subjects[{sem_code}][]')
                    marks = request.form.getlist(f'dynamic_marks[{sem_code}][]')

                    for subject_name, mark in zip(subjects, marks):
                        if subject_name and mark:
                            try:
                                mark_value = int(mark)
                                
                                semester_obj = Semester.query.filter_by(code=sem_code).first()
                                if not semester_obj:
                                    semester_obj = Semester(code=sem_code)
                                    db.session.add(semester_obj)
                                    db.session.flush()

                                subject = Subject.query.filter_by(
                                    name=subject_name, 
                                    semester_id=semester_obj.id
                                ).first()
                                if not subject:
                                    subject = Subject(name=subject_name, semester_id=semester_obj.id)
                                    db.session.add(subject)
                                    db.session.flush()

                                db.session.add(Mark(
                                    student_id=student.id, 
                                    subject_id=subject.id,
                                    semester_id=subject.semester_id, 
                                    marks=mark_value
                                ))
                            except ValueError:
                                continue

            db.session.commit()
            flash(f"Student {student.name} updated successfully.", "success")
            return redirect(url_for("teacher_dashboard" if current_user.role == "teacher" else "dashboard"))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating student: {str(e)}", "danger")

    semesters = {}
    for mark in student.marks:
        semester_code = mark.subject.semester.code
        if semester_code not in semesters:
            semesters[semester_code] = {}
        semesters[semester_code][mark.subject.name] = mark.marks

    return render_template('edit_student.html', student=student, semesters=semesters, 
                         username=current_user.username, role=current_user.role)

@app.route('/delete_student/<int:roll>')
@login_required
def delete_student(roll):
    if not check_permission(["admin", "teacher"]):
        flash("Access denied. Insufficient permissions.", "danger")
        return redirect(url_for("dashboard"))
    
    student = Student.query.filter_by(roll=roll).first()
    if student:
        try:
            user = User.query.filter_by(student_id=student.id).first()
            if user:
                user.student_id = None
            
            db.session.delete(student)
            db.session.commit()
            flash(f"Student {student.name} (Roll: {roll}) deleted successfully.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error deleting student: {str(e)}", "danger")
    else:
        flash("Student not found.", "danger")
    
    return redirect(url_for("teacher_dashboard" if current_user.role == "teacher" else "dashboard"))

@app.route("/performance_visualization", methods=["GET", "POST"])
@login_required
def performance_visualization():
    graph_url = student_name = None

    if request.method == "POST":
        roll = request.form["roll"]
        student = Student.query.filter_by(roll=roll).first()
        if student:
            student_name = student.name
            marks = db.session.query(Subject.name, Mark.marks).join(Mark).filter(Mark.student_id == student.id).all()
            if marks:
                subjects, scores = zip(*marks)
                plt.figure(figsize=(10, 6))
                bars = plt.bar(subjects, scores, color="skyblue")
                plt.title(f"{student_name}'s Performance (Roll: {roll})", fontsize=14, fontweight='bold')
                plt.ylabel("Marks")
                plt.xlabel("Subjects")
                plt.xticks(rotation=45, ha='right')
                
                for bar in bars:
                    height = bar.get_height()
                    plt.text(bar.get_x() + bar.get_width()/2., height + 1,
                            f'{int(height)}', ha='center', va='bottom')
                
                plt.axhline(y=40, color='red', linestyle='--', alpha=0.7, label='Passing Mark (40)')
                plt.legend()
                plt.tight_layout()
                
                img = io.BytesIO()
                plt.savefig(img, format='png', dpi=300, bbox_inches='tight')
                img.seek(0)
                graph_url = base64.b64encode(img.getvalue()).decode()
                plt.close()
        else:
            flash("Student not found.", "danger")

    return render_template("performance_visualization.html", graph_url=graph_url, student=student_name,
                         username=current_user.username, role=current_user.role)

# Update the student_performance route to redirect to student_dashboard
@app.route("/student_performance")
@login_required
def student_performance():
    """Redirect to student dashboard"""
    if current_user.role != "student":
        flash("Access denied. Students only.", "danger")
        return redirect(url_for("dashboard"))
    
    return redirect(url_for("student_dashboard"))

@app.route("/link_account", methods=["GET", "POST"])
@login_required
def link_account():
    if request.method == "POST" and current_user.role == "student":
        roll = request.form.get("roll")
        if roll:
            try:
                student = Student.query.filter_by(roll=int(roll)).first()
                if student:
                    current_user.student_id = student.id
                    db.session.commit()
                    flash(f"Successfully linked to student ID: {roll}", "success")
                    return redirect(url_for("dashboard"))
                else:
                    flash("No student found with that roll number.", "danger")
            except ValueError:
                flash("Invalid roll number format.", "danger")
    
    return render_template("link_account.html", username=current_user.username, role=current_user.role)

@app.route("/exams", methods=["GET", "POST"])
@login_required
def exams():
    if request.method == "POST" and check_permission(["admin", "teacher"]):
        subject = request.form["subject"]
        date_str = request.form["date"]
        description = request.form.get("description", "")
        
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            db.session.add(Exam(subject=subject, date=date_obj, description=description))
            db.session.commit()
            flash("Exam added successfully", "success")
        except ValueError:
            flash("Invalid date format", "danger")
        except Exception as e:
            flash(f"Error adding exam: {str(e)}", "danger")
        
        return redirect(url_for("exams"))
    
    return render_template("exams.html", exams=Exam.query.order_by(Exam.date).all(), 
                         role=current_user.role, username=current_user.username)

# API endpoints
@app.route('/api/student/<int:roll>')
@login_required
def get_student_data(roll):
    if not check_permission(["admin", "teacher"]):
        return jsonify({"error": "Access denied"}), 403
    
    student = Student.query.filter_by(roll=roll).first()
    if not student:
        return jsonify({"error": "Student not found"}), 404
    
    return jsonify(calculate_student_data(student))

@app.route('/api/students')
@login_required
def get_all_students():
    if not check_permission(["admin", "teacher"]):
        return jsonify({"error": "Access denied"}), 403
    
    students = Student.query.order_by(Student.roll.asc()).all()
    return jsonify([calculate_student_data(s) for s in students])

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=True)