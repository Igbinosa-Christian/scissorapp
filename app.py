from flask import Flask,render_template,request,redirect,flash,url_for
from flask_migrate import Migrate
from sqlalchemy import JSON, PickleType
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import LoginManager,login_user,logout_user,login_required,current_user,UserMixin
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
import string
from random import choices
import qrcode
import secrets
import requests
from ip2geotools.databases.noncommercial import DbIpCity
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from redis import Redis



# Defining base dir. of main.py
base_dir = os.path.dirname(os.path.realpath(__file__))


# Create a flask instance
application=Flask(__name__)

# Configure redis server
redis_client = Redis(host='red-chtkn45269vccp6lil8g', port=6379)


# Limiter instance
limiter = Limiter(
    get_remote_address,
    app=application,
    storage_uri="redis://red-chtkn45269vccp6lil8g:6379",
    storage_options={
        'connection_pool': redis_client.connection_pool
    }
)


# Database Configurations
application.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
# 'sqlite:///' + os.path.join(base_dir, 'db.sqlite3') For local database
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
application.config['SECRET_KEY']='d264032a74d1555a05942698'


# Config to store img to static
application.config.update(UPLOAD_PATH=os.path.join(base_dir, 'static'))


# Create an instance of sqlalchemy
db=SQLAlchemy(application)


# to allow us connect to the database to create and do migration in the shell
@application.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User
    }


# Initialize the app database
db.init_app(application)

# to allow easy update of database
migrate = Migrate(application, db)


#LoginManager Instance
login_manager=LoginManager(application) 


# Link Model
class Link(db.Model):
    id=db.Column(db.Integer(),primary_key=True)
    user=db.Column(db.String(150),nullable=False)
    originalUrl = db.Column(db.String(512))
    shortUrl = db.Column(db.String(512), unique=True)
    visits = db.Column(db.Integer, default=0)
    dateCreated = db.Column(db.DateTime, default=datetime.now)
    imgName = db.Column(db.String(50))
    visitLocations = db.relationship('VisitLocation', backref='link')


# VisitLocation Model
class VisitLocation(db.Model):
    id=db.Column(db.Integer(),primary_key=True)
    location = db.Column(db.String(150))
    link_id = db.Column(db.Integer, db.ForeignKey('link.id'))
    numberOfVisits = db.Column(db.Integer, default=0)


    

    def __repr__(self):
        return f"User {self.shortUrl}"
    


# Link Model
class User(db.Model,UserMixin):
    id=db.Column(db.Integer(),primary_key=True)
    username=db.Column(db.String(150),unique=True,nullable=False)
    email=db.Column(db.String(200),unique=True,nullable=False)
    password_hash=db.Column(db.Text(),nullable=False)
    

    def __repr__(self):
        return f"User {self.username}"



#LoginManager Instance
login_manager=LoginManager(application) 
login_manager.login_view='login'


# Create user loader to get users from database
@login_manager.user_loader
def user_loader(id):
    return User.query.get(int(id))



# Home page route
@application.route('/', methods = ['GET','POST'])
def index():
    
    return render_template('index.html')



# Signup Route
@application.route('/register', methods=['GET','POST'])
def register():
    
    if request.method == 'POST':
        username=request.form.get('username')
        email=request.form.get('email')
        password=request.form.get('password')
        con_Password=request.form.get('con_password')
        

        # To validate if a user already exists by username
        user_exists=User.query.filter_by(username=username).first()

        if user_exists:
            flash(f"User with Username {username} exists.", category='error')
            return redirect(url_for('register'))

        # To validate if a user already exists by email
        email_exists=User.query.filter_by(email=email).first()

        if email_exists:
            flash(f"User with email {email} exists", category='error')
            return redirect(url_for('register'))   

        # To confirm if passwords match 
        if password != con_Password:
            flash(f'Passwords do not match', category='error')
            return redirect(url_for('register')) 
        else:
            password_hash=generate_password_hash(password) # To hide password in hash in database
            new_user=User(
                email=email, password_hash=password_hash, username=username
            )   

            db.session.add(new_user)
            db.session.commit()

            flash("User Account Created", category='success') 
            return redirect(url_for('login'))
         

    return render_template('register.html')



# Login Route
@application.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username=request.form.get('username')
        password=request.form.get('password')
    

        user=User.query.filter_by(username=username).first()

        if not user:
            flash(f'User does not exist', category='error')
            return redirect(url_for('login'))

        if user and not check_password_hash(user.password_hash,password) :
            flash(f'Incorrect Password', category='error')
            return redirect(url_for('login'))


        if user and check_password_hash(user.password_hash,password):
            login_user(user)
            

            return redirect(url_for('dashboard'))

    return render_template('login.html')


# Route to logout
@login_required
@application.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

def generate_short_link():
        characters = string.digits + string.ascii_letters
        shortUrl = ''.join(choices(characters, k=5))

        link = Link.query.filter_by(shortUrl=shortUrl).first()

        if link:
            return generate_short_link()
        else:
            return shortUrl


# Dashboard page route
@login_required
@application.route('/dashboard', methods=['GET', 'POST'])
@limiter.limit('10 per day')
def dashboard():

    originalUrl = ""
    shortUrl = ""
    imgName = ""
    imgLocation = ""

    if request.method == 'POST':
        originalUrl = request.form.get('originalUrl')
        customAlias = request.form.get('customAlias')

        # Decide on custom or random short url
        if customAlias == "":
            shortUrl = generate_short_link()
        else:
            shortUrl = f"{current_user.username}.{customAlias}"


        
        checkLink = Link.query.filter_by(shortUrl=shortUrl).filter_by(user=current_user.username).first()
        if checkLink:
            flash(f"Custom Url {shortUrl} already exists.", category='error')
            return redirect(url_for('dashboard'))


        # Check if Url has been shortened by user
        alreadyShortened = Link.query.filter_by(originalUrl=originalUrl).filter_by(user=current_user.username).first()
        if alreadyShortened:
            originalUrl = alreadyShortened.originalUrl
            shortUrl = alreadyShortened.shortUrl
            imgName = alreadyShortened.imgName

        else:
            imgName = f"{secrets.token_hex(8)}.png" 
            imgLocation = f"{application.config['UPLOAD_PATH']}/{imgName}"

            fullShortUrl = f"scissorapp.onrender.com/{shortUrl}"

            myQrCode = qrcode.make(fullShortUrl)
            myQrCode.save(imgLocation)

            link = Link(
            user=current_user.username,
            originalUrl=originalUrl,
            shortUrl = shortUrl,
            imgName = imgName
            )

            originalUrl = link.originalUrl
            shortUrl = link.shortUrl
            imgName = link.imgName


            db.session.add(link)
            db.session.commit()
     
    
    return render_template('dashboard.html', originalUrl=originalUrl, shortUrl=shortUrl, imgName=imgName, imgLocation=imgLocation)


# Get ip address
def get_visitor_ip():
    response = requests.get('https://api.ipify.org?format=json')
    if response.status_code == 200:
        json_data = response.json()
        visitor_ip = json_data['ip']
        return visitor_ip
    else:
        print('Error:', response.status_code)
        return None


# Get location with ip address using ip2geotools
def printDetails(ip):
    res = DbIpCity.get(ip, api_key="free")
    return f"{res.city}, {res.country}"
    


# Route to direct short url to original
@application.route('/<shortUrl>')
def redirect_to_url(shortUrl):
    ip = get_visitor_ip()
    location = printDetails(ip)
    

    link = Link.query.filter_by(shortUrl=shortUrl).first_or_404()

    visitBefore = VisitLocation.query.filter_by(location=location).filter_by(link_id=link.id).first()

    if visitBefore:
        visitBefore.numberOfVisits = visitBefore.numberOfVisits + 1
        db.session.commit()

    else:
        newVisit = VisitLocation(
            location=location,
            link_id=link.id,
            numberOfVisits=1
        )

        db.session.add(newVisit)
        db.session.commit()

        
    link.visits = link.visits + 1
    db.session.commit()


    return redirect(link.originalUrl) 


# Route to view user link history
@login_required
@application.route('/history/<string:user>')
def history(user):
    
    links = Link.query.filter_by(user=user).all()


    return render_template('history.html', links=links)


# Route to view link analytics
@login_required
@application.route('/analytics/<int:id>/', methods=['GET'])
def analytics(id):
    
    link = Link.query.get_or_404(id)

    imgName = link.imgName

    visitData = VisitLocation.query.filter_by(link_id=id).all()



    return render_template('analytics.html', link=link, imgName=imgName, visitData=visitData)




# Route to delete link
@login_required
@application.route('/delete/<int:id>/', methods=['GET'])
def delete(id):
    linkToDelete=Link.query.get_or_404(id)

    linkVisitStat = VisitLocation.query.get_or_404(id)
    
    # To confirm that current user owns the link before deleting
    if current_user.username == linkToDelete.user:

        db.session.delete(linkToDelete)
        db.session.commit()   

        db.session.delete(linkVisitStat)
        db.session.commit() 

        flash("LINK DELETED", category='error')
        return redirect(url_for('dashboard'))

    else:
        flash("CANNOT DELETE ANOTHER USER'S LINK", category='error') 
        return redirect(url_for('dashboard'))

    


if __name__ == "__main__":
    application.run(debug=True)
