from app import *
from flask import render_template, redirect, url_for, request
from sqlalchemy import desc

#use decorators to link the function to a url
@app.route('/')
def home():
    return render_template('home_ui.html')

@app.route('/logout', methods = ['GET'])
def logout():
    session.clear()
    return render_template('home_ui.html')

@app.route('/admin')
def admin():
    user_list = User.query.order_by(User.id).all()
    department = Department.query.all()
    return render_template('admin_ui.html',user_list=user_list, department=department)

@app.route('/staff', methods = ['GET'])
def staff():
    form = UploadFile()
    files = File.query.filter_by(dept=session['dept']).order_by(desc(File.last_modified)).all()

    con_stat = check_con() #check connection with clouds
    g_stat = con_stat[0]
    a_stat = con_stat[1]
    f_stat = con_stat[2]

    return render_template('staff_ui.html', files = files,g_stat = g_stat,a_stat = a_stat, f_stat = f_stat, form=form)

@app.route('/manager', methods = ['GET'])
def manager():
    form = UploadFile()
    files = File.query.filter_by(dept=session['dept']).order_by(desc(File.last_modified)).all()
    length = File.query.filter_by(dept='finance').count()
    return render_template('manager_ui.html', files = files, length = length, form=form)

@app.route('/director', methods = ['GET'])
def director():
    form = UploadFile()
    #department = Department.query.all()
    department = Department.query.filter(Department.dept !='admin', Department.dept != 'director').all()
    return render_template('director_ui.html', department = department, form=form)


@app.route('/login',methods=['GET','POST'])
def login():
    # db.session.query(File).delete()
    # db.session.commit()
    create_acc()
    create_dept()
    #query db for table User
    acc = User.query.order_by(User.id).all()

    error = None
    if request.method == 'POST':
        login_username = request.form['username']
        login_pwd = request.form['password']
        user = User.query.filter((User.username == login_username) & (User.password == login_pwd)).first()
       
        error = login_username + login_pwd

        if user != None:
            error = 'Login Accepted for'
            session['username'] = login_username
            session['dept'] = user.dept
            session['role'] = user.role

            if(user.role == 'admin'):
                return redirect(url_for('admin'))
            if(user.role == 'staff'):
                return redirect(url_for('staff'))
            if(user.role == 'manager'):
                return redirect(url_for('manager'))
            if(user.role == 'director'):
                return redirect(url_for('director'))
            
        else:
            error = 'Invalid Credentials. Please try again.'

    return render_template('login_ui.html', error=error,res=acc)

def create_dept():
    db.session.query(Department).delete()
    sales = Department(dept='sales')
    finance = Department(dept='finance')
    admin = Department(dept='admin')
    director = Department(dept='director')

    db.session.add(sales)
    db.session.add(finance)
    db.session.add(admin)
    db.session.add(director)
    db.session.commit()

def create_acc():
    db.session.query(User).delete()
    admin = User(username='admin',password='admin',dept='admin',role='admin')

    fin_man = User(username='finmanager',password='finman123',dept='finance',role='manager')
    sale_man = User(username='salemanager',password='saleman123',dept='sales',role='manager')

    fin_staff1 = User(username='finstaff1',password='fin123',dept='finance',role='staff')
    fin_staff2 = User(username='finstaff2',password='fin123',dept='finance',role='staff')

    sale_staff1 = User(username='salestaff1',password='sale123',dept='sales',role='staff')
    sale_staff2 = User(username='salestaff2',password='sale123',dept='sales',role='staff')

    director1=User(username='director1',password='director1',dept='director',role='director')

    db.session.add(admin)
    db.session.add(fin_man)
    db.session.add(sale_man)
    db.session.add(fin_staff1)
    db.session.add(fin_staff2)
    db.session.add(sale_staff1)
    db.session.add(sale_staff2)
    db.session.add(director1)
    db.session.commit()

def check_con():
    g_stat = "noconnect"
    a_stat = "noconnect"
    f_stat = "noconnect"

    #INSERT TRY CONNECTION CODE

    con_stat = [g_stat,a_stat,f_stat]
    return con_stat

    