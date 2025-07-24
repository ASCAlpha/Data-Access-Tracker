from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, SelectMultipleField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from wtforms.widgets import ListWidget, CheckboxInput
from models import User, Course, Assessment, Question

class RegistrationForm(FlaskForm):
    """
    Form for user registration.
    """
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    role = SelectField('Role', choices=[('trainee', 'Trainee'), ('support', 'Support'), ('admin', 'Admin')],
                       validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_username(self, username):
        """Custom validator to ensure username is unique."""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        """Custom validator to ensure email is unique."""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered. Please use a different email.')

class LoginForm(FlaskForm):
    """
    Form for user login.
    """
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class CourseForm(FlaskForm):
    """
    Form for creating and editing courses.
    """
    title = StringField('Course Title', validators=[DataRequired(), Length(max=128)])
    description = TextAreaField('Description')
    group_id = StringField('Course Group (Optional, e.g., "Cybersecurity Basics")', validators=[Length(max=64)])
    submit = SubmitField('Save Course')

class AssessmentForm(FlaskForm):
    """
    Form for creating and editing assessments.
    """
    title = StringField('Assessment Title', validators=[DataRequired(), Length(max=128)])
    description = TextAreaField('Description')
    submit = SubmitField('Save Assessment')

class QuestionForm(FlaskForm):
    """
    Form for adding questions to an assessment.
    """
    question_text = TextAreaField('Question Text', validators=[DataRequired()])
    # In a real app, you'd have more question types, but for now, it's open-ended
    question_type = SelectField('Question Type', choices=[('open_ended', 'Open-Ended')], validators=[DataRequired()])
    submit = SubmitField('Add Question')

class MultiCheckboxField(SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.
    Iterating the field will yield a very similar interface to a SelectMultipleField.
    """
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()

class AssignItemsForm(FlaskForm):
    """
    Form for assigning courses/assessments to trainees.
    """
    # Dynamically populated choices in the route
    trainees = MultiCheckboxField('Select Trainees', coerce=int, validators=[DataRequired()])
    courses = SelectField('Select Course (Optional)', coerce=int, choices=[(0, '--- Select a Course ---')])
    assessments = SelectField('Select Assessment (Optional)', coerce=int, choices=[(0, '--- Select an Assessment ---')])
    submit = SubmitField('Assign')

    def validate(self):
        """Custom validation to ensure either a course or an assessment is selected."""
        if not super().validate():
            return False
        
        course_selected = self.courses.data and self.courses.data != 0
        assessment_selected = self.assessments.data and self.assessments.data != 0

        if not (course_selected or assessment_selected):
            self.courses.errors.append('Please select either a course or an assessment.')
            self.assessments.errors.append('Please select either a course or an assessment.')
            return False
        
        if (course_selected and assessment_selected):
            self.courses.errors.append('You can only assign a course OR an assessment at a time, not both.')
            self.assessments.errors.append('You can only assign a course OR an assessment at a time, not both.')
            return False
        
        return True

class AnswerForm(FlaskForm):
    """
    Form for a trainee to submit an answer to an open-ended question.
    """
    answer_text = TextAreaField('Your Answer', validators=[DataRequired()])
    submit = SubmitField('Submit Answer')

class SearchQuestionsForm(FlaskForm):
    """
    Form for searching open-ended questions.
    """
    search_query = StringField('Search Question Text', validators=[DataRequired()])
    submit = SubmitField('Search')
