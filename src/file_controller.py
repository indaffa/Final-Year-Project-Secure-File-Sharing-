from flask import render_template, request, redirect, url_for, Response #pip install flask
from firebase_admin import credentials, initialize_app, storage #pip install firebase-admin
from google.cloud import storage as googleStorage
import os, glob, math
from login import app
from app import *
import boto3
from botocore.exceptions import NoCredentialsError
from datetime import datetime
from werkzeug.utils import secure_filename
import string, random
from sqlalchemy import desc
from reedsolo import RSCodec, ReedSolomonError
import concurrent.futures
import csv

# Initialize Firestore DB
cred = credentials.Certificate('key/firebase_key.json')
file_db = initialize_app(cred,{'storageBucket': 'test-1058f.appspot.com'}) # connecting to firebase

# validate Google Cloud
os.environ['GOOGLE_Application_Credentials'] = 'key/googlecloud_key.json'

# AWS
with open('key/awsrootkey.csv', mode='r') as csv_file:
    csv_reader = csv.reader(csv_file)
    data = next(csv_reader)
    data = next(csv_reader)
AWSACCESS_KEY=data[0]
AWSSECRET_KEY=data[1]
AWSBUCKET="fyp22s403"

#ReedSolomon
rsc = RSCodec()

ext = '.pdf'

def store_in_Firebase(name):
    bucket = storage.bucket()
    blob = bucket.blob(name)
    blob.upload_from_filename(name)

def store_in_Googlecloud(name):
    storage_Client = googleStorage.Client()
    my_bucket = storage_Client.get_bucket("testsimfyp")
    blob = my_bucket.blob(name)
    blob.upload_from_filename(name)

def store_in_AWS(name):
    s3 = boto3.client("s3", aws_access_key_id = AWSACCESS_KEY, aws_secret_access_key = AWSSECRET_KEY)
    try:
        s3.upload_file(name, AWSBUCKET, name)
        #with open(filename, "rb") as data:
        #    s3.upload_fileobj(data, BUCKET, filename)

    except FileNotFoundError:
        print("The file was not found")
    except NoCredentialsError:
        print("Credentials not available")

def splitfile(file, file_name, packet_size):
    with open(file, "rb") as output:
        filecount = 1
        data_size = -1
        try:
            while True:
                data = rsc.encode(output.read(packet_size))
                data_size = max(data_size, len(data))
                if not data:
                    break   # we're done
                with open(file_name+"{:02}".format(filecount), "wb") as packet:
                    packet.write(data)
                filecount += 1
        except Exception as e:
            print(e)
        
    os.remove(file) # delete the main zip file
    return data_size

def generateFileName():
    characters = string.ascii_letters + string.digits
    name = ''.join(random.choice(characters) for i in range(10))

    return name

@app.route('/showfiles')
def showfiles():
    dept = request.args.get('dept')
    files = File.query.filter_by(dept=dept).order_by(desc(File.last_modified)).all()
    return render_template('showfilesforDirector.html',files=files, dept=dept)

def store_file_01(code_name, number):
    code_name = code_name+number
    store_in_Firebase(code_name)   # store file 01 in firebase
    store_in_Googlecloud(code_name) # store file 01 in GoogleCloud
    os.remove(code_name) # delete the pdf file

def store_file_02(code_name, number):
    code_name = code_name+number
    store_in_Googlecloud(code_name)   # store file 02 in GoogleCloud
    store_in_AWS(code_name) # store file 02 in AWS
    os.remove(code_name) # delete the pdf file

def store_file_03(code_name, number):
    code_name = code_name+number
    store_in_AWS(code_name)   # store file 03 in AWS
    store_in_Firebase(code_name) # store file 03 in firebase
    os.remove(code_name) # delete the pdf file

@app.route('/file_upload', methods = ['POST'])
def upload():
    form = UploadFile()
    if form.validate_on_submit():
        file_name = form.file_name.data
        basename = secure_filename(form.upload.data.filename)
        form.upload.data.save(basename)  # save the file to server to be split
        packet_size = math.ceil(os.stat(basename).st_size / 3)  # get the size of one partitioned file
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        code_name = generateFileName()

        try:
            packet_size = splitfile(basename, code_name, packet_size)   # split the file
            new_file = File(name=file_name,code_name=code_name,owner=session['username'],packet_size=packet_size,dept=session['dept'],date_created=dt_string,last_modified=dt_string)
            db.session.add(new_file)     # store metadeta of file in sql
            db.session.commit()

            with concurrent.futures.ThreadPoolExecutor() as executor: # upload to cloud in parallel
                task_1 = executor.submit(store_file_01,code_name,"01")
                task_2 = executor.submit(store_file_02,code_name,"02")
                task_3 = executor.submit(store_file_03,code_name,"03")

                task_1.result()
                task_2.result()
                task_3.result()
            
            # store_file_01(code_name, "01")
            # store_file_02(code_name, "02")
            # store_file_03(code_name, "03")
        
            if session['role'] == 'manager':
                return redirect(url_for('manager'))
            elif session['role'] == 'staff':
                return redirect(url_for('staff'))
                #return redirect('/staff')
        except Exception as e:
            return e
            #return 'There was an issue adding your task'
    else:
        flash(form.upload.errors)
        if session['role'] == 'manager':
            return redirect(url_for('manager'))
        elif session['role'] == 'staff':
            return redirect(url_for('staff'))
   

@app.route('/edit', methods = ['GET','POST'])
def edit():  
    code_name = request.args.get('name')
    form = UploadFile()
    if request.method == 'POST':
        if form.validate_on_submit():
            code_name = request.args.get('name')
            file_name = form.file_name.data
            basename = secure_filename(form.upload.data.filename)
            form.upload.data.save(basename)  # save the file to server to be split
            now = datetime.now()
            dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
            packet_size = math.ceil(os.stat(basename).st_size / 3)  # get the size of one packet
            file = File.query.filter_by(code_name=code_name).first()
            file.name = file_name
            file.last_modified = dt_string
            #file.packet_size = packet_size
            #db.session.commit()

            try:
                packet_size = splitfile(basename, code_name, packet_size)   # split the file
                file.packet_size = packet_size
                db.session.commit()
                store_file_01(code_name, "01")
                store_file_02(code_name, "02")
                store_file_03(code_name, "03")
    
                if session['role'] == 'manager':
                    return redirect(url_for('manager'))
                elif session['role'] == 'staff':
                    return redirect(url_for('staff'))
                #return redirect('/staff')
            except Exception as e:
                return e
                #return 'There was an issue adding your task
        else:
            flash(form.upload.errors)
            file = File.query.filter_by(code_name=code_name).first()
            return render_template('editFile_ui.html', file = file, form=form)

    elif request.method == 'GET':
        file = File.query.filter_by(code_name=code_name).first()
        return render_template('editFile_ui.html', file = file, form=form)

def download_from_Firebase(name):
    bucket = storage.bucket()
    blob = bucket.blob(name)
    blob.download_to_filename(name)

def download_from_GoogleCloud(name):
    storage_Client = googleStorage.Client()
    my_bucket = storage_Client.get_bucket("testsimfyp")
    blob = my_bucket.blob(name)
    with open(name, 'wb') as f:
        storage_Client.download_blob_to_file(blob, f)

def download_from_AWS(name):
    s3 = boto3.client("s3", aws_access_key_id = AWSACCESS_KEY, aws_secret_access_key = AWSSECRET_KEY)
    try:
        s3.download_file(AWSBUCKET, name, name)
        #with open(filename, "wb") as data:
        #    s3.download_fileobj(BUCKET, filename, data)
    except NoCredentialsError:
        print("Credentials not available")

def reconstruct_file(filename, packet_size):
    for i in range(1,4):
        with open("{}{:02}".format(filename, i), "rb") as packet:
            col=packet.read(packet_size)

            with open("{}.pdf".format(filename), "ab+") as mainpackage:
                mainpackage.write(rsc.decode(col)[0])

def delete_in_AWS(name):
    s3 = boto3.client("s3", aws_access_key_id = AWSACCESS_KEY, aws_secret_access_key = AWSSECRET_KEY)
    s3.delete_object(Bucket = AWSBUCKET, Key = name)

def delete_in_Firebase(name):
    bucket = storage.bucket()
    blob = bucket.blob(name)
    blob.delete()

def delete_in_GoogleCloud(name):
    storage_Client = googleStorage.Client()
    my_bucket = storage_Client.get_bucket("testsimfyp")
    blob = my_bucket.blob(name)
    blob.delete()

def delete_file_01(code_name, number):
    code_name = code_name+number
    delete_in_Firebase(code_name)   # delete file 01 in firebase
    delete_in_GoogleCloud(code_name) # delete file 01 in GoogleCloud

def delete_file_02(code_name, number):
    code_name = code_name+number
    delete_in_GoogleCloud(code_name)   # delete file 02 in GoogleCloud
    delete_in_AWS(code_name) # delete file 02 in AWS

def delete_file_03(code_name, number):
    code_name = code_name+number
    delete_in_AWS(code_name)   # delete file 03 in AWS
    delete_in_Firebase(code_name) # delete file 03 in firebase

@app.route("/delete")
def delete():
    code_name = request.args.get('name')
    File.query.filter_by(code_name=code_name).delete()   # delete file metada in sql
    db.session.commit()
    delete_file_01(code_name,"01")
    delete_file_02(code_name,"02")
    delete_file_03(code_name,"03")

    if session['role'] == 'manager':
        return redirect(url_for('manager'))
    elif session['role'] == 'staff':
        return redirect(url_for('staff'))
    #return redirect('/staff')
 
def download_file_01(code_name, number, packet_size):
    code_name = code_name+number
    download_from_Firebase(code_name)
    try:
        with open(code_name, "rb") as packet:
            col=packet.read(packet_size)
            rsc.decode(col)[0] # check the file for corruption. if exception is thrown, download from another cloud
    except ReedSolomonError:
        download_from_GoogleCloud(code_name)

def download_file_02(code_name, number, packet_size):
    code_name = code_name+number
    download_from_GoogleCloud(code_name)
    try:
        with open(code_name, "rb") as packet:
            col=packet.read(packet_size)
            rsc.decode(col)[0] # check the file for corruption. if exception is thrown, download from another cloud
    except ReedSolomonError:
        download_from_AWS(code_name)

def download_file_03(code_name, number, packet_size):
    code_name = code_name+number
    download_from_AWS(code_name)
    try:
        with open(code_name, "rb") as packet:
            col=packet.read(packet_size)
            rsc.decode(col)[0] # check the file for corruption. if exception is thrown, download from another cloud
    except ReedSolomonError:
        download_from_Firebase(code_name)
    

@app.route('/view', methods = ['GET','POST'])
def view():
  if request.method == "POST":
        code_name = request.form['name']
        packet_size = int(request.form['packetsize'])

        with concurrent.futures.ThreadPoolExecutor() as executor:   # download from cloud in parallel
            task_1 = executor.submit(download_file_01,code_name,"01", packet_size)
            task_2 = executor.submit(download_file_02,code_name,"02", packet_size)
            task_3 = executor.submit(download_file_03,code_name,"03", packet_size)

            task_1.result()
            task_2.result()
            task_3.result()
    

        # download_file_01(code_name, "01", packet_size)
        # download_file_02(code_name, "02", packet_size)
        # download_file_03(code_name, "03", packet_size)

        reconstruct_file(code_name, packet_size)  # reconstruct the file
        
        for files in glob.glob(code_name+"0*"):
            os.remove(files)  # delete the 3 files from server after reconstructin
        
        with open((code_name+".pdf"), 'rb') as f:
            data = f.readlines()   # store the actual file in memory to send to client
        os.remove(code_name+".pdf")   # delete the actual file
        
        code_name = code_name+ext
        
        return Response(data, headers={  # send file in memory to client. afer sending, memory is discarded 
            'Content-Type': 'application/pdf',
            'Content-Disposition': 'inline; filename=%s;' % code_name
        })



