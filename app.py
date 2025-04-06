from flask import Flask, request, render_template, redirect, send_from_directory
import boto3
import uuid
from datetime import datetime
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Setup
region = 'eu-west-1'
dynamodb = boto3.resource('dynamodb', region_name=region)
table = dynamodb.Table('JobApplications')

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    response = table.scan()
    jobs = response.get('Items', [])
    return render_template('index.html', jobs=jobs)

@app.route('/add', methods=['POST'])
def add_job():
    company = request.form['company']
    role = request.form['role']
    status = request.form['status']
    date_applied = datetime.now().strftime('%Y-%m-%d')
    job_id = str(uuid.uuid4())

    # Save file locally
    file = request.files['resume']
    filename = secure_filename(f"{job_id}_{file.filename}")
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    file_url = f"/uploads/{filename}"  # Flask route

    # Save job to DynamoDB
    table.put_item(Item={
        'JobID': job_id,
        'Company': company,
        'Role': role,
        'Status': status,
        'DateApplied': date_applied,
        'ResumeURL': file_url
    })

    return redirect('/')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/delete/<job_id>', methods=['POST'])
def delete_job(job_id):
    table.delete_item(Key={'JobID': job_id})
    return redirect('/')

@app.route('/edit/<job_id>', methods=['POST'])
def edit_job(job_id):
    new_status = request.form['status']
    table.update_item(
        Key={'JobID': job_id},
        UpdateExpression="set #s = :val",
        ExpressionAttributeNames={'#s': 'Status'},
        ExpressionAttributeValues={':val': new_status}
    )
    return redirect('/')

# if __name__ == '__main__':
#     # Make sure uploads folder exists
#     if not os.path.exists(UPLOAD_FOLDER):
#         os.makedirs(UPLOAD_FOLDER)
        
#     app.run(host='0.0.0.0', port=8080, debug=True)

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)


