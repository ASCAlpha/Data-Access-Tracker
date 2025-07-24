from datetime import datetime
from app import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

# User loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    """
    Represents a user in the system.
    Roles: 'trainee', 'support', 'admin'
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='trainee', nullable=False) # 'trainee', 'support', 'admin'

    # Relationships
    assignments = db.relationship('Assignment', backref='assignee', lazy='dynamic')
    answers = db.relationship('Answer', backref='responder', lazy='dynamic')

    def set_password(self, password):
        """Hashes the password and stores it."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks if the provided password matches the stored hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

class Course(db.Model):
    """
    Represents a course that can be assigned to trainees.
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    group_id = db.Column(db.String(64), nullable=True) # For grouping courses (e.g., 'Cybersecurity Basics')

    # Relationships
    assignments = db.relationship('Assignment', backref='course_assigned', lazy='dynamic')

    def __repr__(self):
        return f'<Course {self.title}>'

class Assessment(db.Model):
    """
    Represents an assessment that can be assigned to trainees.
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)

    # Relationships
    questions = db.relationship('Question', backref='assessment_parent', lazy='dynamic')
    assignments = db.relationship('Assignment', backref='assessment_assigned', lazy='dynamic')

    def __repr__(self):
        return f'<Assessment {self.title}>'

class Question(db.Model):
    """
    Represents a question within an assessment.
    Currently supports 'open_ended' type.
    """
    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessment.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), default='open_ended', nullable=False) # e.g., 'open_ended'

    # Relationships
    answers = db.relationship('Answer', backref='question_parent', lazy='dynamic')

    def __repr__(self):
        return f'<Question {self.id} for Assessment {self.assessment_id}>'

class Assignment(db.Model):
    """
    Represents an assignment of a course or assessment to a specific user.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessment.id'), nullable=True)
    assigned_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='not_started', nullable=False) # 'not_started', 'in_progress', 'completed'

    # Ensure only one of course_id or assessment_id is set
    __table_args__ = (
        db.CheckConstraint(
            '(course_id IS NOT NULL AND assessment_id IS NULL) OR '
            '(course_id IS NULL AND assessment_id IS NOT NULL)',
            name='check_course_or_assessment'
        ),
    )

    # Relationships
    progress_entries = db.relationship('Progress', backref='assignment_parent', lazy='dynamic')

    def __repr__(self):
        item_type = 'Course' if self.course_id else 'Assessment'
        item_id = self.course_id if self.course_id else self.assessment_id
        return f'<Assignment {self.id} for User {self.user_id} ({item_type} {item_id})>'

class Progress(db.Model):
    """
    Tracks the progress of an assignment.
    This could be expanded for more granular tracking (e.g., per module in a course).
    For now, it's tied to the overall assignment status.
    """
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False)
    status = db.Column(db.String(20), default='not_started', nullable=False) # 'not_started', 'in_progress', 'completed'
    completion_date = db.Column(db.DateTime, nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Progress for Assignment {self.assignment_id}: {self.status}>'

class Answer(db.Model):
    """
    Stores a trainee's answer to an open-ended question.
    """
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False) # Link to the specific assignment
    answer_text = db.Column(db.Text, nullable=False)
    submitted_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Answer by User {self.user_id} to Question {self.question_id}>'
