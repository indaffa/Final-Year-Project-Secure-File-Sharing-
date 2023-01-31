from app import *
from login import *
from flask import render_template, request

#admin page (user management)
@app.route('/admin/add_user', methods = ['GET','POST'])
def add_user():
    #query db for table User
    #user_list = User.query.order_by(User.id).all()
    if request.method == 'POST':
        add_username = request.form['username']
        add_pwd = request.form['password']
        add_dept = request.form['dept']
        add_role = request.form['role']

        add_msg = add_username + " Added"

        add_user = User(username=add_username,password=add_pwd,dept=add_dept,role=add_role)
        db.session.add(add_user)
        db.session.commit()

    user_list = User.query.order_by(User.id).all()
    department = Department.query.all()
    return render_template('admin_ui.html',user_list=user_list,action_msg=add_msg, department=department)

@app.route('/showDepartment')
def showDepartment():
    form = AddDepartment()
    department = Department.query.all()
    return render_template('showDepartment.html', department = department, form=form)

@app.route('/editDepartment', methods = ['GET', 'POST'])
def editDepartment():
    form = EditDepartment()
    if request.method == 'POST':
        id = request.args.get('id')
        new_dept = form.department_name.data
        Dept = Department.query.filter_by(id=id).first()
        Dept.dept = new_dept
        for row in User.query:  
            row.dept = new_dept
        db.session.commit()
        return redirect(url_for('showDepartment'))

    else:
        id = request.args.get('id')
        dept = request.args.get('name')
        return render_template('editDepartment.html', id=id, form=form, dept=dept)

@app.route('/addDepartment',methods = ['POST'])
def addDepartment():
    form = AddDepartment()
    if form.validate_on_submit():
        dept = form.department_name.data
        exists = db.session.query(db.exists().where(Department.dept == dept)).scalar()
        if exists:
            flash("Department already exist")
            return redirect(url_for('showDepartment'))
        else:
            newDept = Department(dept=dept)
            db.session.add(newDept)
            db.session.commit()
            return redirect(url_for('showDepartment'))
    
    else:
        return redirect(url_for('showDepartment'))

@app.route('/deleteDepartment')
def deleteDepartment():
    dept = request.args.get('name')
    exists = db.session.query(db.exists().where(User.dept == dept)).scalar()
    if exists:
        flash("Cannot delete when there is still staff members")
        return redirect(url_for('showDepartment'))
    else:
        Department.query.filter_by(dept=dept).delete()   # delete department in sql
        db.session.commit()
        return redirect(url_for('showDepartment'))


@app.route('/admin/edit_UI', methods = ['GET','POST'])
def edit_UI():
    if request.method == 'POST':
            edit_id = request.form['edit_user']
            user_cred = User.query.get(edit_id)
            department = Department.query.all()
    return render_template('edituser_ui.html',user=edit_id,user_cred=user_cred, department=department)

@app.route('/admin/edit_user', methods = ['GET','POST'])
def edit_user():
    if request.method == 'POST':
        edit_id = request.form['edit_id']
        user_cred = User.query.get(edit_id)

        user_cred.username = request.form['edit_username']
        user_cred.password = request.form['edit_password']
        user_cred.dept = request.form['edit_dept']
        user_cred.role = request.form['edit_role']
        db.session.commit()

        edit_msg = str("User ID " + edit_id + " Edited")

    user_list = User.query.order_by(User.id).all()
    department = Department.query.all()
    return render_template('admin_ui.html',user_list=user_list,action_msg=edit_msg,department=department)

@app.route('/admin/del_user', methods = ['GET','POST'])
def del_user():
    if request.method == 'POST':
            del_id = request.form['del_user']
            User.query.filter_by(id=del_id).delete()   # delete department in sql
            db.session.commit()
            # del_user = db.get_or_404(User, del_id)
            # db.session.delete(del_user)
            # db.session.commit()

            del_msg = str("User ID " + del_id + " Deleted")

    user_list = User.query.order_by(User.id).all()
    department = Department.query.all()
    return render_template('admin_ui.html',user_list=user_list,action_msg=del_msg,department=department)    
