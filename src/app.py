from flask import Flask, session, flash

from flask import render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

from flask_wtf import FlaskForm   #pip install Flask-WTF
from wtforms import StringField,SubmitField
from flask_wtf.file import FileField,FileRequired,FileAllowed
from wtforms.validators import DataRequired

# create the application object
app = Flask(__name__)
app.secret_key = "SECRET_KEY" # create a session
app.config['MAX_CONTENT_LENGTH'] = 16* 1024 * 1024   # set the maximum file size to 16 mb
app.config['UPLOAD_EXTENSIONS'] = ['.pdf']    # restrict the file type to only pdf

#name of database
db_name = 'database.db'

#config SQL database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+ db_name #connect app to db
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db = SQLAlchemy(app) #create db instance
db.init_app(app)

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(20), nullable = False)
    password = db.Column(db.String(80), nullable = False)
    dept = db.Column(db.String(20),nullable = False)
    role = db.Column(db.String(20), nullable = False)

    def __repr__(self):
        return '%r %r %r %r %r' %(self.id,self.username,self.password,self.dept,self.role)


class File(db.Model):
    id = db.Column(db.Integer , primary_key=True)
    name = db.Column(db.String(200), nullable = False)
    owner = db.Column(db.String(200), nullable = False)
    code_name = db.Column(db.String(200), nullable = False)
    packet_size = db.Column(db.Integer, nullable = False)
    dept = db.Column(db.String(200), nullable = False)
    date_created = db.Column(db.String(200), nullable = False)
    last_modified = db.Column(db.String(200), nullable = False)

    def __repr__(self):
        return '<File name: %r>' %self.name

class Department(db.Model):
    id = db.Column(db.Integer , primary_key=True)
    dept = db.Column(db.String(200), nullable = False)

class UploadFile(FlaskForm):
    file_name = StringField(label=('Filename:'), 
        validators=[DataRequired()]
    )
    upload = FileField('File', validators=[FileRequired(),FileAllowed(['pdf'],'Invalid File Type. Must be .pdf')])

    submit = SubmitField(label=('Upload'))

class AddDepartment(FlaskForm):
    department_name = StringField(label=('Department:'), 
        validators=[DataRequired()]
    )

    submit = SubmitField(label=('Add'))


class EditDepartment(FlaskForm):
    department_name = StringField(label=('Department:'), 
        validators=[DataRequired()]
    )

    submit = SubmitField(label=('Edit'))