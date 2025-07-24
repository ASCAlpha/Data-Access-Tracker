from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
from sqlalchemy import or_

# Import configurations and models/forms
from config import Config
from models import db, User, Course, Assessment, Question, Assignment, Progress, Answer, load_user
from forms import RegistrationForm, LoginForm, CourseForm, AssessmentForm, QuestionForm, AssignItemsForm, AnswerForm, SearchQuestionsForm

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' # Redirect to login page if not authenticated
login_manager.init_app(app)

# Create database tables if they don't exist
with app.app_context():
    db.create_all()

# --- Role-based Access Control Decorators ---
def role_required(role):
    """
    Decorator to restrict access to routes based on user role.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('login', next=request.url))
            if current_user.role != role:
                flash(f'You do not have permission to access this page. Required role: {role.capitalize()}', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator for admin-only access."""
    return role_required('admin')(f)

def support_or_admin_required(f):
    """Decorator for support or admin access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        if current_user.role not in ['support', 'admin']:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# --- Routes ---

@app.route('/')
@app.route('/index')
def index():
    """Home page."""
    return render_template('index.html', title='Welcome')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, role=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
        login_user(user)
        next_page = request.args.get('next')
        return redirect(next_page or url_for('dashboard'))
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
@login_required
def logout():
    """Logs out the current user."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard, redirects based on role."""
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif current_user.role == 'trainee':
        return redirect(url_for('trainee_assignments'))
    elif current_user.role == 'support':
        return redirect(url_for('view_all_trainee_progress'))
    return render_template('dashboard.html', title='Dashboard') # Fallback dashboard

@app.route('/admin_dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard with quick links for management."""
    total_users = User.query.count()
    total_courses = Course.query.count()
    total_assessments = Assessment.query.count()
    return render_template('admin_dashboard.html',
                           title='Admin Dashboard',
                           total_users=total_users,
                           total_courses=total_courses,
                           total_assessments=total_assessments)

@app.route('/create_course', methods=['GET', 'POST'])
@admin_required
def create_course():
    """Admin route to create a new course."""
    form = CourseForm()
    if form.validate_on_submit():
        course = Course(title=form.title.data, description=form.description.data, group_id=form.group_id.data or None)
        db.session.add(course)
        db.session.commit()
        flash(f'Course "{course.title}" created successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('create_course.html', title='Create Course', form=form)

@app.route('/create_assessment', methods=['GET', 'POST'])
@admin_required
def create_assessment():
    """Admin route to create a new assessment."""
    form = AssessmentForm()
    if form.validate_on_submit():
        assessment = Assessment(title=form.title.data, description=form.description.data)
        db.session.add(assessment)
        db.session.commit()
        flash(f'Assessment "{assessment.title}" created successfully! Now add questions.', 'success')
        return redirect(url_for('add_question_to_assessment', assessment_id=assessment.id))
    return render_template('create_assessment.html', title='Create Assessment', form=form)

@app.route('/assessment/<int:assessment_id>/add_question', methods=['GET', 'POST'])
@admin_required
def add_question_to_assessment(assessment_id):
    """Admin route to add questions to an existing assessment."""
    assessment = Assessment.query.get_or_404(assessment_id)
    form = QuestionForm()
    if form.validate_on_submit():
        question = Question(assessment_id=assessment.id,
                            question_text=form.question_text.data,
                            question_type=form.question_type.data)
        db.session.add(question)
        db.session.commit()
        flash('Question added successfully!', 'success')
        # Allow adding more questions or returning to dashboard
        if 'add_another' in request.form: # Check if 'Add Another' button was clicked
            return redirect(url_for('add_question_to_assessment', assessment_id=assessment.id))
        else:
            return redirect(url_for('admin_dashboard'))
    
    # Display existing questions for the assessment
    questions = Question.query.filter_by(assessment_id=assessment.id).all()
    return render_template('add_question.html', title=f'Add Questions to {assessment.title}',
                           form=form, assessment=assessment, questions=questions)

@app.route('/assign_items', methods=['GET', 'POST'])
@admin_required
def assign_items():
    """Admin route to assign courses or assessments to trainees."""
    form = AssignItemsForm()
    
    # Populate choices for trainees, courses, and assessments
    form.trainees.choices = [(u.id, u.username) for u in User.query.filter_by(role='trainee').order_by(User.username).all()]
    form.courses.choices = [(0, '--- Select a Course ---')] + [(c.id, c.title) for c in Course.query.order_by(Course.title).all()]
    form.assessments.choices = [(0, '--- Select an Assessment ---')] + [(a.id, a.title) for a in Assessment.query.order_by(Assessment.title).all()]

    if form.validate_on_submit():
        selected_trainee_ids = form.trainees.data
        selected_course_id = form.courses.data if form.courses.data != 0 else None
        selected_assessment_id = form.assessments.data if form.assessments.data != 0 else None

        if not selected_trainee_ids:
            flash('Please select at least one trainee.', 'danger')
            return redirect(url_for('assign_items'))

        assigned_count = 0
        for trainee_id in selected_trainee_ids:
            if selected_course_id:
                assignment = Assignment(user_id=trainee_id, course_id=selected_course_id)
                db.session.add(assignment)
                assigned_count += 1
            elif selected_assessment_id:
                assignment = Assignment(user_id=trainee_id, assessment_id=selected_assessment_id)
                db.session.add(assignment)
                assigned_count += 1
        
        db.session.commit()
        flash(f'{assigned_count} assignments created successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('assign_items.html', title='Assign Courses/Assessments', form=form)

@app.route('/trainee_assignments')
@role_required('trainee')
def trainee_assignments():
    """Trainee's view of their assigned courses and assessments."""
    # Fetch assignments for the current user
    assignments = Assignment.query.filter_by(user_id=current_user.id).all()
    
    # Prepare data to display
    assigned_items = []
    for assignment in assignments:
        item = None
        item_type = ''
        if assignment.course_id:
            item = Course.query.get(assignment.course_id)
            item_type = 'Course'
        elif assignment.assessment_id:
            item = Assessment.query.get(assignment.assessment_id)
            item_type = 'Assessment'
        
        if item:
            assigned_items.append({
                'assignment_id': assignment.id,
                'item_type': item_type,
                'title': item.title,
                'description': item.description,
                'status': assignment.status,
                'assigned_date': assignment.assigned_date,
                'due_date': assignment.due_date
            })

    return render_template('trainee_assignments.html', title='My Assignments', assigned_items=assigned_items)

@app.route('/complete_assessment/<int:assignment_id>', methods=['GET', 'POST'])
@role_required('trainee')
def complete_assessment(assignment_id):
    """Trainee route to complete an assessment."""
    assignment = Assignment.query.get_or_404(assignment_id)

    # Ensure this assignment belongs to the current user and is an assessment
    if assignment.user_id != current_user.id or not assignment.assessment_id:
        flash('Invalid assignment or not an assessment.', 'danger')
        return redirect(url_for('trainee_assignments'))

    assessment = Assessment.query.get_or_404(assignment.assessment_id)
    questions = Question.query.filter_by(assessment_id=assessment.id).all()

    # Create a list of forms for each question
    # This approach assumes all questions are open-ended for now.
    # For different question types, you'd need more complex form handling.
    forms = []
    for question in questions:
        form = AnswerForm(prefix=f'q_{question.id}') # Use prefix to distinguish forms
        # Pre-populate if an answer already exists
        existing_answer = Answer.query.filter_by(
            question_id=question.id,
            user_id=current_user.id,
            assignment_id=assignment.id
        ).first()
        if existing_answer:
            form.answer_text.data = existing_answer.answer_text
        forms.append({'question': question, 'form': form})

    if request.method == 'POST':
        all_forms_valid = True
        for item in forms:
            form = item['form']
            question = item['question']
            if form.validate_on_submit():
                # Update existing answer or create new one
                existing_answer = Answer.query.filter_by(
                    question_id=question.id,
                    user_id=current_user.id,
                    assignment_id=assignment.id
                ).first()
                if existing_answer:
                    existing_answer.answer_text = form.answer_text.data
                    existing_answer.submitted_date = datetime.utcnow()
                else:
                    answer = Answer(
                        question_id=question.id,
                        user_id=current_user.id,
                        assignment_id=assignment.id,
                        answer_text=form.answer_text.data
                    )
                    db.session.add(answer)
            else:
                all_forms_valid = False
                # Flash errors for invalid forms
                for field, errors in form.errors.items():
                    for error in errors:
                        flash(f'Error for question "{question.question_text}": {error}', 'danger')

        if all_forms_valid:
            # Mark assignment as completed if all questions are answered
            assignment.status = 'completed'
            # Also update the Progress entry if it exists, or create one
            progress = Progress.query.filter_by(assignment_id=assignment.id).first()
            if progress:
                progress.status = 'completed'
                progress.completion_date = datetime.utcnow()
            else:
                new_progress = Progress(assignment_id=assignment.id, status='completed', completion_date=datetime.utcnow())
                db.session.add(new_progress)

            db.session.commit()
            flash('Assessment submitted successfully!', 'success')
            return redirect(url_for('trainee_assignments'))
        else:
            db.session.rollback() # Rollback if any form failed validation
            flash('Please correct the errors in your answers.', 'danger')

    return render_template('complete_assessment.html',
                           title=f'Complete Assessment: {assessment.title}',
                           assignment=assignment,
                           assessment=assessment,
                           forms=forms)

@app.route('/view_all_trainee_progress')
@support_or_admin_required
def view_all_trainee_progress():
    """Support/Admin route to view progress of all trainees."""
    trainees = User.query.filter_by(role='trainee').order_by(User.username).all()
    
    trainee_data = []
    for trainee in trainees:
        assignments = Assignment.query.filter_by(user_id=trainee.id).all()
        
        assigned_items_summary = []
        for assignment in assignments:
            item_title = 'N/A'
            item_type = ''
            if assignment.course_id:
                item = Course.query.get(assignment.course_id)
                item_title = item.title if item else 'Deleted Course'
                item_type = 'Course'
            elif assignment.assessment_id:
                item = Assessment.query.get(assignment.assessment_id)
                item_title = item.title if item else 'Deleted Assessment'
                item_type = 'Assessment'
            
            assigned_items_summary.append({
                'assignment_id': assignment.id,
                'item_type': item_type,
                'title': item_title,
                'status': assignment.status,
                'assigned_date': assignment.assigned_date.strftime('%Y-%m-%d'),
                'due_date': assignment.due_date.strftime('%Y-%m-%d') if assignment.due_date else 'N/A'
            })
        
        trainee_data.append({
            'user': trainee,
            'assignments': assigned_items_summary
        })

    return render_template('view_progress.html', title='Trainee Progress Overview', trainee_data=trainee_data)

@app.route('/view_trainee_details/<int:user_id>')
@support_or_admin_required
def view_trainee_details(user_id):
    """Support/Admin route to view detailed progress for a specific trainee."""
    trainee = User.query.get_or_404(user_id)
    if trainee.role != 'trainee':
        flash('User is not a trainee.', 'danger')
        return redirect(url_for('view_all_trainee_progress'))

    assignments = Assignment.query.filter_by(user_id=trainee.id).all()
    
    detailed_assignments = []
    for assignment in assignments:
        item_title = 'N/A'
        item_type = ''
        questions_and_answers = []
        
        if assignment.course_id:
            item = Course.query.get(assignment.course_id)
            item_title = item.title if item else 'Deleted Course'
            item_type = 'Course'
        elif assignment.assessment_id:
            item = Assessment.query.get(assignment.assessment_id)
            item_title = item.title if item else 'Deleted Assessment'
            item_type = 'Assessment'
            
            # Fetch answers for this assessment if it's completed
            if assignment.status == 'completed':
                questions = Question.query.filter_by(assessment_id=assignment.assessment_id).all()
                for question in questions:
                    answer = Answer.query.filter_by(
                        question_id=question.id,
                        user_id=trainee.id,
                        assignment_id=assignment.id
                    ).first()
                    questions_and_answers.append({
                        'question_text': question.question_text,
                        'answer_text': answer.answer_text if answer else 'No answer submitted yet.',
                        'submitted_date': answer.submitted_date.strftime('%Y-%m-%d %H:%M') if answer else 'N/A'
                    })

        detailed_assignments.append({
            'assignment_id': assignment.id,
            'item_type': item_type,
            'title': item_title,
            'status': assignment.status,
            'assigned_date': assignment.assigned_date.strftime('%Y-%m-%d'),
            'due_date': assignment.due_date.strftime('%Y-%m-%d') if assignment.due_date else 'N/A',
            'questions_and_answers': questions_and_answers # Only relevant for assessments
        })

    return render_template('view_trainee_details.html',
                           title=f'Progress for {trainee.username}',
                           trainee=trainee,
                           detailed_assignments=detailed_assignments)

@app.route('/search_questions', methods=['GET', 'POST'])
@admin_required # Or support_or_admin_required depending on who can search
def search_questions():
    """Admin route to search open-ended questions."""
    form = SearchQuestionsForm()
    results = []
    if form.validate_on_submit():
        search_query = f"%{form.search_query.data}%"
        # Search only open-ended questions for now
        results = Question.query.filter(
            Question.question_type == 'open_ended',
            Question.question_text.ilike(search_query)
        ).all()
        if not results:
            flash('No questions found matching your search.', 'info')
    return render_template('search_questions.html', title='Search Questions', form=form, results=results)


# --- Error Handlers (Optional but good practice) ---
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback() # Rollback any pending database changes
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)
