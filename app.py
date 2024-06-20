import numpy as np
from flask import Flask, request, render_template, redirect, session, url_for, jsonify, flash
import matplotlib.pyplot as plt
import matplotlib
import pyodbc
import uuid
from datetime import datetime


matplotlib.use('Agg')  # Use a non-GUI backend

app = Flask(__name__)
app.secret_key = 'secret_key'

def get_db_connection():
    s = 'DESKTOP-QO0JIAJ\\SQLEXPRESS' 
    d = 'Ujsurvey'
    u = 'Jabulani' 
    p = 'Jabulani@12345' 
    cstr = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={s};DATABASE={d};UID={u};PWD={p}'
    conn = pyodbc.connect(cstr)
    return conn  # Ensure the connection object is returned


@app.route('/')
def index():
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return render_template('login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        account_type = request.form['userstype']
        password = request.form['password']
        
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute('SELECT Survey_ID, Password, AccountType, Active FROM [Ujsurvey].[dbo].[Login] WHERE Username = ?', (username,))
        user = cursor.fetchone()
        connection.close()

        if user:
            if user[3] == 0:  # Check if the account is deactivated
                error_message = "Your account has been deactivated."
                return render_template('login.html', error=error_message)
            elif user[1] == password and user[2] == account_type:
                session['username'] = username
                session['survey_id'] = user[0]
                session['new_guid'] = generate_random_code()  # Generate a new GUID

                questions, total_questions, total_pages = get_unique_survey_id(session['survey_id'])
                
                if account_type == "Administrator":
                    return redirect(url_for('dashboardAdministrator'))
                else:
                    return render_template('userAccount.html', questions=questions, survey_id=session['survey_id'], page=1, total_questions=total_questions, total_pages=total_pages)
            else:
                error_message = "Invalid credentials. Please make sure to enter the correct username, password, and account type."
                return render_template('login.html', error=error_message)
        else:
            error_message = "Invalid credentials. Please make sure to enter the correct username, password, and account type."
            return render_template('login.html', error=error_message)

    return render_template('login.html')




# Function definition to get survey questions per survey id
def get_unique_survey_id(survey_id, page=1, per_page=6):
    offset = (page - 1) * per_page

    connection = get_db_connection()
    if connection is None:
        return [], 0, 1
    
    cursor = connection.cursor()
    
    # Fetch the total number of questions
    cursor.execute('SELECT COUNT(*) FROM [Ujsurvey].[dbo].[Questions] WHERE Survey_ID = ?', (survey_id,))
    total_questions = cursor.fetchone()[0]
    
    cursor.execute('SELECT Question_Index, Question_Text, Question_Type FROM [Ujsurvey].[dbo].[Questions] WHERE Survey_ID = ? ORDER BY Question_Index OFFSET ? ROWS FETCH NEXT ? ROWS ONLY', (survey_id, offset, per_page))
    questions = cursor.fetchall()
    
    updated_questions = []
    for question in questions:
        question_index, question_text, question_type = question
        question_options = []
        if question_type in ['Dropdown', 'Tickbox']:
            cursor.execute('SELECT Question_Options FROM [Ujsurvey].[dbo].[QuestionOptions] WHERE Survey_ID = ? AND Question_ID = ?', (survey_id, question_index))
            options = cursor.fetchall()
            question_options = [opt[0] for opt in options]
        updated_questions.append((question_index, question_text, question_type, question_options))
    
    connection.close()
    
    total_pages = (total_questions + per_page - 1) // per_page
    return updated_questions, total_questions, total_pages




# Randomly generated GUID
def generate_random_code():
    # Generate a random UUID
    random_uuid = uuid.uuid4()
    # Convert the UUID to a string in the desired format
    code = str(random_uuid).upper()
    return code

# Generate and print the random code
print(generate_random_code())

# User account app route 
@app.route('/userAccount/<int:survey_id>')
def survey(survey_id):
    page = request.args.get('page', 1, type=int)
    questions, total_questions, total_pages = get_unique_survey_id(survey_id, page)
    new_guid = session.get('new_guid')
    return render_template('userAccount.html', questions=questions, survey_id=survey_id, page=page, total_questions=total_questions, total_pages=total_pages, new_guid=new_guid)



# Submitting user submitted answers into the respondent database
@app.route('/user_submission_feedback', methods=['POST'])
def userSubmissionFeedback():
    survey_id = session.get('survey_id')
    new_guid = session.get('new_guid')
    username = session.get('username')  # Retrieve the username from the session
    if not survey_id:
        flash('Survey ID not found in session', 'error')
        return redirect(url_for('index'))

    responses = []

    # Iterate over each question to collect responses
    for question in request.form:
        if question.startswith('q'):
            question_id = question[1:]  # Extract question ID from the form field name
            response = request.form[question]
            responses.append((survey_id, question_id, response, new_guid))

    connection = get_db_connection()
    cursor = connection.cursor()

    print("These are the responses: ", responses)

    # Insert responses into the database
    insert_query = '''
    INSERT INTO [Ujsurvey].[dbo].[Responses]
        ([Survey_ID], [Question_ID], [Response], [NewGUID])
    VALUES
        (?, ?, ?, ?)
    '''
    for response in responses:
        cursor.execute(insert_query, response)

    connection.commit()
    connection.close()

    flash(f'{username}, thanks for making out time in taking this survey . We appreciate You!', 'success')
    return render_template('feedbackresponseMessage.html', survey_id=survey_id)



# Administrator dashboard 

@app.route('/administrator', methods=['GET', 'POST'])
def dashboardAdministrator():
    connection = get_db_connection()
    if connection is None:
        return "Error connecting to the database", 500
    
    cursor = connection.cursor()
    
    # Pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 15  # Number of items per page
    
    offset = (page - 1) * per_page
    
    # Filtering parameter
    survey_id = request.form.get('survey_id') if request.method == 'POST' else request.args.get('survey_id')
    
    # Base query
    base_query = 'SELECT * FROM Respondent'
    count_query = 'SELECT COUNT(*) FROM Respondent'
    
    if survey_id:
        base_query += ' WHERE Survey_ID = ?'
        count_query += ' WHERE Survey_ID = ?'
    
    # Get total records
    if survey_id:
        cursor.execute(count_query, survey_id)
    else:
        cursor.execute(count_query)
    total_records = cursor.fetchone()[0]
    total_pages = (total_records + per_page - 1) // per_page
    
    # Fetch the records
    if survey_id:
        cursor.execute(f'{base_query} ORDER BY Survey_ID OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY', survey_id)
    else:
        cursor.execute(f'{base_query} ORDER BY Survey_ID OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY')
    admin = cursor.fetchall()
    connection.close()
    
    return render_template('administrator.html', admin=admin, page=page, total_pages=total_pages, survey_id=survey_id)


# Add questions 

@app.route('/add_question', methods=['GET', 'POST'])
def add_question():
    if request.method == 'POST':
        question_id = request.form['question_id']
        survey_id = request.form['survey_id']
        question_index = request.form['question_index']
        question_text = request.form['question_text']
        question_type = request.form['question_type']
        question_options = request.form['question_options']
        next_question_index = request.form['next_question_index']

        connection = get_db_connection()
        cursor = connection.cursor()
        
        insert_query = '''
        INSERT INTO [Ujsurvey].[dbo].[Questions]
            ([Question_ID], [Survey_ID], [Question_Index], [Question_Text], [Question_Type], [Question_Options], [Next_QuestionIndex])
        VALUES
            (?, ?, ?, ?, ?, ?, ?)
        '''
        
        cursor.execute(insert_query, (question_id, survey_id, question_index, question_text, question_type, question_options, next_question_index))
        connection.commit()
        connection.close()
        
        return redirect(url_for('administrator'))  # Ensure this endpoint exists
    
    return render_template('add_question.html')


# add new user account
@app.route('/add_new_user', methods=['GET', 'POST'])
def add_new_user_account():
    page = request.args.get('page', 1, type=int)
    total_pages = 1  # Set the total_pages variable, update if pagination is needed
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        user_account_type = request.form['userstype']
        survey_id = request.form['survey_id']
        user_status = int(request.form['userStatus'])  # Ensure this is converted to int

        if password != confirm_password:
            return render_template('administrator.html', error='Passwords do not match', page=page, total_pages=total_pages)

        connection = get_db_connection()
        cursor = connection.cursor()

        # Check if the username already exists
        cursor.execute('SELECT COUNT(*) FROM [Ujsurvey].[dbo].[Login] WHERE Username = ?', (username,))
        if cursor.fetchone()[0] > 0:
            connection.close()
            return render_template('administrator.html', error='Username exists', page=page, total_pages=total_pages)

        # If no conflict, insert the new user
        insert_query = '''
        INSERT INTO [Ujsurvey].[dbo].[Login]
            ([Survey_ID], [Username], [Password], [Active], [AccountType])
        VALUES
            (?, ?, ?, ?, ?)
        '''
        
        cursor.execute(insert_query, (survey_id, username, password, user_status, user_account_type))
        connection.commit()
        connection.close()
        
        flash('User created successfully!')
        return redirect(url_for('dashboardAdministrator', page=page))  
    
    return render_template('administrator.html', page=page, total_pages=total_pages)


# Change password 
@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    Password_error = None  # Initialize Password_error
    page = request.args.get('page', 1, type=int)
    total_pages = 1  # Set the total_pages variable, update if pagination is needed

    if request.method == 'POST':
        username = request.form['username']
        oldpassword = request.form['oldpassword']
        newpassword = request.form['newpassword']
        survey_id = request.form['survey_id']

        connection = get_db_connection()
        cursor = connection.cursor()

        # Check if the username and survey_id exist and fetch the current password
        cursor.execute('SELECT Password FROM [Ujsurvey].[dbo].[Login] WHERE Username = ? AND Survey_ID = ?', (username, survey_id))
        user = cursor.fetchone()
        
        if not user:
            Password_error = "User not found for the provided username and survey ID"
        elif oldpassword == newpassword:
            Password_error = "New password is the same as the old password"
        elif user[0] != oldpassword:
            Password_error = "Incorrect old password for the username and survey ID"
        else:
            # Update the password
            cursor.execute('UPDATE [Ujsurvey].[dbo].[Login] SET Password = ? WHERE Username = ? AND Survey_ID = ?', (newpassword, username, survey_id))
            connection.commit()
            Password_error = "Password updated successfully"
        
        connection.close()

    return render_template('administrator.html', Password_error=Password_error, page=page, total_pages=total_pages)



# Activate /  deactivate a user account 
@app.route('/activate_deactivate_a_user', methods=['GET', 'POST'])
def activateOrDeactivate():
    Password_error = None  # Initialize Password_error
    page = request.args.get('page', 1, type=int)
    total_pages = 1  # Set the total_pages variable, update if pagination is needed

    if request.method == 'POST':
        survey_id = request.form['survey_id']
        username = request.form['username']
        userStatus = int(request.form['userStatus'])  # Ensure this is converted to int

        connection = get_db_connection()
        cursor = connection.cursor()

        # Check if the username and survey_id exist
        cursor.execute('SELECT Active FROM [Ujsurvey].[dbo].[Login] WHERE Username = ? AND Survey_ID = ?', (username, survey_id))
        user = cursor.fetchone()
        
        if not user:
            Password_error = "User not found for the provided username and survey ID"
        else:
            # Update the active status
            cursor.execute('UPDATE [Ujsurvey].[dbo].[Login] SET Active = ? WHERE Username = ? AND Survey_ID = ?', (userStatus, username, survey_id))
            connection.commit()
            Password_error = "User status updated successfully"
        
        connection.close()

    return render_template('administrator.html', Password_error=Password_error, page=page, total_pages=total_pages)


# Update user survey id 
@app.route('/update_user_survey_id', methods=['GET', 'POST'])
def updateUserSurveyId():
    Password_error = None  # Initialize Password_error
    page = request.args.get('page', 1, type=int)
    total_pages = 1  # Set the total_pages variable, update if pagination is needed

    if request.method == 'POST':
        survey_id = request.form['new_survey_id']
        username = request.form['username']
        password = request.form['password']

        connection = get_db_connection()
        cursor = connection.cursor()

        # Check if the username and password exist
        cursor.execute('SELECT Survey_ID FROM [Ujsurvey].[dbo].[Login] WHERE Username = ? AND Password = ?', (username, password))
        user = cursor.fetchone()
        
        if not user:
            Password_error = "User not found for the provided username and password"
        else:
            # Update the survey ID
            cursor.execute('UPDATE [Ujsurvey].[dbo].[Login] SET Survey_ID = ? WHERE Username = ? AND Password = ?', (survey_id, username, password))
            connection.commit()
            Password_error = "User Survey ID updated successfully"
        
        connection.close()

    return render_template('administrator.html', Password_error=Password_error, page=page, total_pages=total_pages)



# Create new survey 
@app.route('/create_new_survey', methods=['GET', 'POST'])
def add_new_survey():
    page = request.args.get('page', 1, type=int)
    total_pages = 1  # Set the total_pages variable, update if pagination is needed
    if request.method == 'POST':
        survey_id = request.form['survey_id']
        SurveyName = request.form['SurveyName']
        username = request.form['username']
        datetime_str = request.form['datetime']
        surveyStatus = int(request.form['surveyStatus'])

        # Convert the datetime string to a proper format
        try:
            datetime_obj = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            return render_template('administrator.html', error='Invalid date format. Please use YYYY-MM-DD HH:MM:SS.', page=page, total_pages=total_pages)

        connection = get_db_connection()
        cursor = connection.cursor()

        # Check if the Survey name already exists
        cursor.execute('SELECT COUNT(*) FROM [Ujsurvey].[dbo].[Survey] WHERE Survey_ID = ? AND SurveyName = ?', (survey_id, SurveyName,))
        if cursor.fetchone()[0] > 0:
            connection.close()
            return render_template('administrator.html', error='Survey name exists. Please choose a different name.', page=page, total_pages=total_pages)

        # Insert the new survey without specifying the Survey_ID
        insert_query = '''
        INSERT INTO [Ujsurvey].[dbo].[Survey]
            ([SurveyName], [Creator], [Created_Date], [Active])
        VALUES
            (?, ?, ?, ?)
        '''
        
        cursor.execute(insert_query, (SurveyName, username, datetime_obj, surveyStatus))
        connection.commit()
        connection.close()
        
        flash('Survey created successfully!')
        return redirect(url_for('dashboardAdministrator', page=page))  
    
    return render_template('administrator.html', page=page, total_pages=total_pages)



# update existing survey name 

@app.route('/update_existing_survey_name', methods=['GET', 'POST'])
def updateExistingSurveyName():
    error = None  # Initialize error variable
    page = request.args.get('page', 1, type=int)
    total_pages = 1  # Set the total_pages variable, update if pagination is needed

    if request.method == 'POST':
        survey_id = request.form['survey_id']
        username = request.form['username']
        oldsurveyname = request.form['oldsurveyname']
        newsurveyname = request.form['newsurveyname']

        connection = get_db_connection()
        cursor = connection.cursor()

        # Check if the old survey name exists for the given survey_id and username
        cursor.execute('SELECT SurveyName FROM [Ujsurvey].[dbo].[Survey] WHERE Survey_ID = ? AND Creator = ? AND SurveyName = ?', (survey_id, username, oldsurveyname))
        survey = cursor.fetchone()
        
        if not survey:
            error = "There is no such survey name in the database"
            connection.close()
            return render_template('administrator.html', error=error, page=page, total_pages=total_pages)
        else:
            # Update the survey name
            cursor.execute('UPDATE [Ujsurvey].[dbo].[Survey] SET SurveyName = ? WHERE Survey_ID = ? AND Creator = ? AND SurveyName = ?', (newsurveyname, survey_id, username, oldsurveyname))
            connection.commit()
            connection.close()
            flash('Survey name updated successfully!')

            return redirect(url_for('dashboardAdministrator', page=page))  

    return render_template('administrator.html', error=error, page=page, total_pages=total_pages)

# update existing survey status 

@app.route('/update_existing_survey_status', methods=['GET', 'POST'])
def updateExistingSurveyStatus():
    error = None  # Initialize error variable
    page = request.args.get('page', 1, type=int)
    total_pages = 1  # Set the total_pages variable, update if pagination is needed

    if request.method == 'POST':
        survey_id = request.form['survey_id']
        surveyStatus = int(request.form['surveyStatus'])

        connection = get_db_connection()
        cursor = connection.cursor()

        # Check if the survey ID exists
        cursor.execute('SELECT Survey_ID FROM [Ujsurvey].[dbo].[Survey] WHERE Survey_ID = ?', (survey_id,))
        survey = cursor.fetchone()
        
        if not survey:
            error = "There is no such survey ID in the database"
            connection.close()
            return render_template('administrator.html', error=error, page=page, total_pages=total_pages)
        else:
            # Update the survey status
            cursor.execute('UPDATE [Ujsurvey].[dbo].[Survey] SET Active = ? WHERE Survey_ID = ?', (surveyStatus, survey_id))
            connection.commit()
            connection.close()
            flash('Survey status updated successfully!')

            return redirect(url_for('dashboardAdministrator', page=page))  

    return render_template('administrator.html', error=error, page=page, total_pages=total_pages)


# add gps location 
@app.route('/create_new_gps_location', methods=['GET', 'POST'])
def create_new_gps_location():
    page = request.args.get('page', 1, type=int)
    total_pages = 1  # Set the total_pages variable, update if pagination is needed
    if request.method == 'POST':
        gps_name = request.form['gps_name']
        survey_id = request.form['survey_id']
        latitudeNumber = float(request.form['latitudeNumber'])  # Ensure the values are float
        longitudeNumber = float(request.form['longitudeNumber'])  # Ensure the values are float

        connection = get_db_connection()
        cursor = connection.cursor()

        # # Check if the GPS name already exists
        # cursor.execute('SELECT COUNT(*) FROM [Ujsurvey].[dbo].[GPS] WHERE GPS_Name = ?', (gps_name,))
        # if cursor.fetchone()[0] > 0:
        #     connection.close()
        #     return render_template('administrator.html', error='GPS Name exists.', page=page, total_pages=total_pages)

        # # Check if the Survey ID already exists
        # cursor.execute('SELECT COUNT(*) FROM [Ujsurvey].[dbo].[GPS] WHERE Survey_ID = ?', (survey_id,))
        # if cursor.fetchone()[0] > 0:
        #     connection.close()
        #     return render_template('administrator.html', error='Survey ID exists.', page=page, total_pages=total_pages)

        # Insert the new GPS record
        insert_query = '''
        INSERT INTO [Ujsurvey].[dbo].[GPS]
            ([GPS_Name], [Survey_ID], [Latitude], [Longitude])
        VALUES
            (?, ?, ?, ?)
        '''
        
        cursor.execute(insert_query, (gps_name, survey_id, latitudeNumber, longitudeNumber))
        connection.commit()
        connection.close()
        
        flash('GPS created successfully!')
        return redirect(url_for('dashboardAdministrator', page=page))  
    
    return render_template('administrator.html', page=page, total_pages=total_pages)

# update gps table 
@app.route('/update_gps_table', methods=['GET', 'POST'])
def updategpsTable():
    error = None  # Initialize error variable
    page = request.args.get('page', 1, type=int)
    total_pages = 1  # Set the total_pages variable, update if pagination is needed

    if request.method == 'POST':
        gps_name = request.form['gps_name']
        latitudeNumber = float(request.form['latitudeNumber'])  
        longitudeNumber = float(request.form['longitudeNumber'])  
        survey_id = request.form['survey_id']
        maxRange = request.form['maxRange']
        PermissionStatus = int(request.form['PermissionStatus'])

        connection = get_db_connection()
        cursor = connection.cursor()

        # Check if the GPS name exists
        cursor.execute('SELECT GPS_Name FROM [Ujsurvey].[dbo].[GPS] WHERE GPS_Name = ?', (gps_name,))
        survey = cursor.fetchone()
        
        if not survey:
            error = "There is no record of this GPS Name in the database."
            connection.close()
            return render_template('administrator.html', error=error, page=page, total_pages=total_pages)
        else:
            # Update the GPS table
            update_query = '''
            UPDATE [Ujsurvey].[dbo].[GPS]
            SET Latitude = ?, Longitude = ?, Max_Range = ?, Permission = ?, Survey_ID = ?
            WHERE GPS_Name = ?
            '''
            cursor.execute(update_query, (latitudeNumber, longitudeNumber, maxRange, PermissionStatus, survey_id, gps_name))
            connection.commit()
            connection.close()
            flash('GPS information updated successfully!')

            return redirect(url_for('dashboardAdministrator', page=page))  

    return render_template('administrator.html', error=error, page=page, total_pages=total_pages)



# view all surveys 
@app.route('/display_all_surveys', methods=['GET', 'POST'])
def displayAllSurvey():
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of items per page
    survey_creator_filter = None
    error = None

    if request.method == 'POST':
        survey_creator_filter = request.form['survey_creator']

    connection = get_db_connection()
    cursor = connection.cursor()

    # Construct the query based on the presence of a survey_creator filter
    if survey_creator_filter:
        count_query = 'SELECT COUNT(*) FROM [Ujsurvey].[dbo].[Survey] WHERE Creator LIKE ?'
        cursor.execute(count_query, ('%' + survey_creator_filter + '%',))
    else:
        count_query = 'SELECT COUNT(*) FROM [Ujsurvey].[dbo].[Survey]'
        cursor.execute(count_query)
        
    total_surveys = cursor.fetchone()[0]

    if total_surveys == 0:
        error = "No such survey creator in our records."
        return render_template('displayAllSurveys.html', surveys=[], page=page, total_pages=1, survey_creator_filter=survey_creator_filter, error=error)

    # Calculate total pages
    total_pages = (total_surveys + per_page - 1) // per_page
    offset = (page - 1) * per_page

    # Fetch surveys with pagination and optional filter
    if survey_creator_filter:
        query = 'SELECT * FROM [Ujsurvey].[dbo].[Survey] WHERE Creator LIKE ? ORDER BY Survey_ID OFFSET ? ROWS FETCH NEXT ? ROWS ONLY'
        cursor.execute(query, ('%' + survey_creator_filter + '%', offset, per_page))
    else:
        query = 'SELECT * FROM [Ujsurvey].[dbo].[Survey] ORDER BY Survey_ID OFFSET ? ROWS FETCH NEXT ? ROWS ONLY'
        cursor.execute(query, (offset, per_page))
        
    surveys = cursor.fetchall()
    connection.close()

    return render_template('displayAllSurveys.html', surveys=surveys, page=page, total_pages=total_pages, survey_creator_filter=survey_creator_filter, error=error)



# refresh gps table
@app.route('/refresh_gps_table_by_survey', methods=['GET', 'POST'])
def refreshGPSTable():
    page = request.args.get('page', 1, type=int)
    total_pages = 1  # Set the total_pages variable, update if pagination is needed

    if request.method == 'POST':
        survey_id = request.form['survey_id']

        connection = get_db_connection()
        cursor = connection.cursor()

        # Fetch GPS records for the given Survey_ID
        cursor.execute('SELECT * FROM [Ujsurvey].[dbo].[GPS] WHERE Survey_ID = ?', (survey_id,))
        gps_records = cursor.fetchall()
        connection.close()
        
        return render_template('refreshgpstable.html', gps_records=gps_records, page=page, total_pages=total_pages)

    return render_template('refreshgpstable.html', gps_records=[], page=page, total_pages=total_pages)

# update master survey 
@app.route('/update_master_survey_status', methods=['GET', 'POST'])
def updateMasterSurveyStatus():
    error = None  # Initialize error variable
    page = request.args.get('page', 1, type=int)
    total_pages = 1  # Set the total_pages variable, update if pagination is needed

    if request.method == 'POST':
        old_master_survey_id = request.form['old_master_survey_id']
        new_master_survey_id = request.form['new_matser_survey_id']

        connection = get_db_connection()
        cursor = connection.cursor()

        # Check if the old master survey ID exists
        cursor.execute('SELECT MasterSurvey FROM [Ujsurvey].[dbo].[Survey] WHERE MasterSurvey = ?', (old_master_survey_id,))
        survey = cursor.fetchone()
        
        if not survey:
            error = "There is no such Master Survey ID in the database"
            connection.close()
            return render_template('administrator.html', error=error, page=page, total_pages=total_pages)
        else:
            # Update the MasterSurvey ID
            cursor.execute('UPDATE [Ujsurvey].[dbo].[Survey] SET MasterSurvey = ? WHERE MasterSurvey = ?', (new_master_survey_id, old_master_survey_id))
            connection.commit()
            connection.close()
            flash('Master Survey ID updated successfully!')

            return redirect(url_for('dashboardAdministrator', page=page))  

    return render_template('administrator.html', error=error, page=page, total_pages=total_pages)


# add new questions 
@app.route('/add_new_question', methods=['GET', 'POST'])
def add_new_question():
    page = request.args.get('page', 1, type=int)
    total_pages = 1  # Set the total_pages variable, update if pagination is needed
    if request.method == 'POST':
        survey_id = request.form['survey_id']
        question_index = request.form['question_index']
        question_text = request.form['question_text']
        question_type = request.form['question_type']
        next_question_index = request.form['next_question_index']

        
        connection = get_db_connection()
        cursor = connection.cursor()

        
        # Insert the new survey without specifying the Survey_ID
        insert_query = '''
        INSERT INTO [Ujsurvey].[dbo].[Questions]
            ([Survey_ID], [Question_Index], [Question_Text], [Question_Type], [Next_QuestionIndex])
        VALUES
            (?, ?, ?, ?, ?)
        '''
        
        cursor.execute(insert_query, (survey_id, question_index, question_text, question_type, next_question_index))
        connection.commit()
        connection.close()
        
        flash('Question created successfully!')
        return redirect(url_for('dashboardAdministrator', page=page))  
    
    return render_template('administrator.html', page=page, total_pages=total_pages)


# Update question text and type
@app.route('/update_question_text_and_type', methods=['GET', 'POST'])
def updateQuestionTextandType():
    error = None  # Initialize error variable
    page = request.args.get('page', 1, type=int)
    total_pages = 1  # Set the total_pages variable, update if pagination is needed

    if request.method == 'POST':
        survey_id = request.form['survey_id']
        question_index = request.form['question_index']
        new_question_text = request.form['new_question_text']
        new_question_type = request.form['new_question_type']

        connection = get_db_connection()
        cursor = connection.cursor()

        # Check if the question exists for the given survey_id and question_index
        cursor.execute('SELECT * FROM [Ujsurvey].[dbo].[Questions] WHERE Survey_ID = ? AND Question_Index = ?', (survey_id, question_index))
        question = cursor.fetchone()
        
        if not question:
            error = "No such Survey ID and Question ID."
            connection.close()
            return render_template('administrator.html', error=error, page=page, total_pages=total_pages)
        else:
            # Update the question text and type
            update_query = '''
            UPDATE [Ujsurvey].[dbo].[Questions]
            SET Question_Text = ?, Question_Type = ?
            WHERE Survey_ID = ? AND Question_Index = ?
            '''
            cursor.execute(update_query, (new_question_text, new_question_type, survey_id, question_index))
            connection.commit()
            connection.close()
            flash('Question text and type updated successfully!')

            return redirect(url_for('dashboardAdministrator', page=page))

    return render_template('administrator.html', error=error, page=page, total_pages=total_pages)


# UPDATE NEXT QUESTION INDEX FOR QUESTION
@app.route('/update_next_question_index_for_question', methods=['GET', 'POST'])
def updatenextQuestionIndexForQuestion():
    error = None  # Initialize error variable
    page = request.args.get('page', 1, type=int)
    total_pages = 1  # Set the total_pages variable, update if pagination is needed

    if request.method == 'POST':
        question_id = request.form['question_id']
        survey_id = request.form['survey_id']
        current_question_index = request.form['current_question_index']
        new_question_index = request.form['new_question_index']

        connection = get_db_connection()
        cursor = connection.cursor()

        # Check if the survey_id, question_id and current question index exists
        cursor.execute('SELECT * FROM [Ujsurvey].[dbo].[Questions] WHERE Question_ID = ? AND Survey_ID = ? AND Next_QuestionIndex = ?', (question_id, survey_id, current_question_index))
        question = cursor.fetchone()
        
        if not question:
            error = "No such Data in the record."
            connection.close()
            return render_template('administrator.html', error=error, page=page, total_pages=total_pages)
        else:
            # Update the next question index
            update_query = '''
            UPDATE [Ujsurvey].[dbo].[Questions]
            SET Next_QuestionIndex = ? 
            WHERE Question_ID = ? AND Survey_ID = ? AND Next_QuestionIndex = ?
            '''
            cursor.execute(update_query, (new_question_index, question_id, survey_id, current_question_index))
            connection.commit()
            connection.close()
            flash('Next question index updated successfully!')

            return redirect(url_for('dashboardAdministrator', page=page))

    return render_template('administrator.html', error=error, page=page, total_pages=total_pages)


# UPDATE NEXT QUESTION INDEX WITH NEW VALUE
@app.route('/update_next_question_index_with_value', methods=['GET', 'POST'])
def updatenextQuestionIndexWithValue():
    error = None  # Initialize error variable
    page = request.args.get('page', 1, type=int)
    total_pages = 1  # Set the total_pages variable, update if pagination is needed

    if request.method == 'POST':
        survey_id = request.form['survey_id']
        old_question_index = request.form['old_question_index']
        new_question_index = request.form['new_question_value']

        connection = get_db_connection()
        cursor = connection.cursor()

        # Check if the survey_id and question index index exists
        cursor.execute('SELECT * FROM [Ujsurvey].[dbo].[Questions] WHERE Survey_ID = ? AND Question_Index = ?', (survey_id, old_question_index))
        question = cursor.fetchone()
        
        if not question:
            error = "No such Data in the record."
            connection.close()
            return render_template('administrator.html', error=error, page=page, total_pages=total_pages)
        else:
            # Update the question index
            update_query = '''
            UPDATE [Ujsurvey].[dbo].[Questions]
            SET Question_Index = ? 
            WHERE Survey_ID = ? AND Question_Index = ?
            '''
            cursor.execute(update_query, (new_question_index, survey_id, old_question_index))
            connection.commit()
            connection.close()
            flash('Question Index updated successfully!')

            return redirect(url_for('dashboardAdministrator', page=page))

    return render_template('administrator.html', error=error, page=page, total_pages=total_pages)












@app.route('/display_all_questions_for_the_given_survey', methods=['GET', 'POST'])
def displayAllQuestionsForGivenSurvey():
    page = request.args.get('page', 1, type=int)
    per_page = 6  # Number of items per page

    survey_id = None
    question_index_filter = None

    if request.method == 'POST':
        survey_id = request.form.get('survey_id')
        question_index_filter = request.form.get('question_index')
    else:
        survey_id = request.args.get('survey_id')
        question_index_filter = request.args.get('question_index')

    if not survey_id:
        error = "Survey ID is required."
        return render_template('displayAllQuestionsPerSurvey.html', error=error, page=page, total_pages=1, survey_id=survey_id)

    connection = get_db_connection()
    cursor = connection.cursor()

    # Construct the base query and params
    base_query = 'SELECT COUNT(*) FROM [Ujsurvey].[dbo].[Questions] WHERE Survey_ID = ?'
    params = [survey_id]

    if question_index_filter:
        base_query += ' AND Question_Index = ?'
        params.append(question_index_filter)

    # Fetch total number of questions
    cursor.execute(base_query, params)
    total_questions = cursor.fetchone()[0]

    if total_questions == 0:
        error = "No questions found for the provided criteria."
        return render_template('displayAllQuestionsPerSurvey.html', error=error, page=page, total_pages=1, survey_id=survey_id)

    # Calculate total pages
    total_pages = (total_questions + per_page - 1) // per_page
    offset = (page - 1) * per_page

    # Construct the query for fetching questions with pagination
    query = 'SELECT Question_Index, Question_Text, Question_Type, Question_Options FROM [Ujsurvey].[dbo].[Questions] WHERE Survey_ID = ?'
    if question_index_filter:
        query += ' AND Question_Index = ?'
    query += ' ORDER BY Question_Index OFFSET ? ROWS FETCH NEXT ? ROWS ONLY'

    params += [offset, per_page]
    cursor.execute(query, params)
    all_questions_per_survey = cursor.fetchall()
    connection.close()

    return render_template('displayAllQuestionsPerSurvey.html', all_questions_per_survey=all_questions_per_survey, page=page, total_pages=total_pages, survey_id=survey_id, question_index_filter=question_index_filter)



















# ADD NEW QUESTION OPTION FOR DROPDOWN (DD) OR TICKBOX (TB)	
@app.route('/add_new_new_question_options', methods=['GET', 'POST'])
def add_new_question_option():
    page = request.args.get('page', 1, type=int)
    total_pages = 1  # Set the total_pages variable, update if pagination is needed
    if request.method == 'POST':
        question_id = request.form['question_id']
        survey_id = request.form['survey_id']
        question_options = request.form['question_options']
        next_question_index = request.form['next_question_index']

        connection = get_db_connection()
        cursor = connection.cursor()

        # Check if the Survey_ID and Question_ID exist
        cursor.execute('SELECT COUNT(*) FROM [Ujsurvey].[dbo].[Questions] WHERE Survey_ID = ? AND Question_Index = ?', (survey_id, question_id))
        if cursor.fetchone()[0] == 0:
            connection.close()
            error_message = "There is no such survey id or question id in our records."
            flash(error_message, 'error')
            return render_template('administrator.html', page=page, total_pages=total_pages)

        # Insert the new question options into the question option table.
        insert_query = '''
        INSERT INTO [Ujsurvey].[dbo].[QuestionOptions]
            ([Question_Options], [Question_ID], [Survey_ID], [Next_Question])
        VALUES
            (?, ?, ?, ?)
        '''
        
        cursor.execute(insert_query, (question_options, question_id, survey_id, next_question_index))
        connection.commit()
        connection.close()
        
        flash('Question option created successfully!', 'success')
        return redirect(url_for('dashboardAdministrator', page=page))  
    
    return render_template('administrator.html', page=page, total_pages=total_pages)


# Display all responses per survey
@app.route('/display_all_responses_per_survey', methods=['GET', 'POST'])
def displayResponsesPerSurvey():
    page = request.args.get('page', 1, type=int)
    per_page = 6  # Number of items per page

    survey_id = None
    question_id = None
    error = None

    if request.method == 'POST':
        survey_id = request.form.get('survey_id')
        question_id = request.form.get('question_id')
    else:
        survey_id = request.args.get('survey_id')
        question_id = request.args.get('question_id')

    total_responses = 0  # Initialize total_responses

    if survey_id or question_id:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Construct the base query and params
        base_query = 'SELECT COUNT(*) FROM [Ujsurvey].[dbo].[Responses] WHERE 1=1'
        params = []

        if survey_id:
            base_query += ' AND Survey_ID = ?'
            params.append(survey_id)

        if question_id:
            base_query += ' AND Question_ID = ?'
            params.append(question_id)

        # Fetch total number of responses
        cursor.execute(base_query, params)
        total_responses = cursor.fetchone()[0]

        if total_responses == 0:
            error = "No responses found for the provided criteria."
            return render_template('administrator.html', error=error, page=page, total_pages=1)

        # Calculate total pages
        total_pages = (total_responses + per_page - 1) // per_page
        offset = (page - 1) * per_page

        # Construct the query for fetching responses with pagination
        query = 'SELECT * FROM [Ujsurvey].[dbo].[Responses] WHERE 1=1'
        if survey_id:
            query += ' AND Survey_ID = ?'
        if question_id:
            query += ' AND Question_ID = ?'
        query += ' ORDER BY Question_ID OFFSET ? ROWS FETCH NEXT ? ROWS ONLY'

        params += [offset, per_page]
        cursor.execute(query, params)
        responses = cursor.fetchall()
        connection.close()

    else:
        responses = []
        total_pages = 1

    return render_template('DisplayAllResponsesPerSurvey.html', responses=responses, page=page, total_pages=total_pages, survey_id=survey_id, question_id=question_id, total_responses=total_responses, error=error)



# UPDATE QUESTION OPTION WITH NEW VALUE
@app.route('/update_question_option_with_new_value', methods=['GET', 'POST'])
def UpdateQuestionOptionWithNewValue():
    error = None  # Initialize error variable
    page = request.args.get('page', 1, type=int)
    total_pages = 1  # Set the total_pages variable, update if pagination is needed

    if request.method == 'POST':
        survey_id = request.form['survey_id']
        question_id = request.form['question_id']
        old_option_value = request.form['old_option_value']
        new_option_value = request.form['new_option_value']

        connection = get_db_connection()
        cursor = connection.cursor()

        # Check if the survey_id, question_id, and old_option_value exist
        cursor.execute('SELECT * FROM [Ujsurvey].[dbo].[QuestionOptions] WHERE Survey_ID = ? AND Question_ID = ? AND Question_Options = ?', (survey_id, question_id, old_option_value))
        question_option = cursor.fetchone()
        
        if not question_option:
            error = "No such data in the record."
            connection.close()
            return render_template('administrator.html', error=error, page=page, total_pages=total_pages)
        else:
            # Update the question option
            update_query = '''
            UPDATE [Ujsurvey].[dbo].[QuestionOptions]
            SET Question_Options = ? 
            WHERE Survey_ID = ? AND Question_ID = ? AND Question_Options = ?
            '''
            cursor.execute(update_query, (new_option_value, survey_id, question_id, old_option_value))
            connection.commit()
            connection.close()
            flash('Question Option updated successfully!')

            return redirect(url_for('dashboardAdministrator', page=page))

    return render_template('administrator.html', error=error, page=page, total_pages=total_pages)

# DELETE QUESTION OPTION
@app.route('/delete_question_option', methods=['GET', 'POST'])
def DeleteQuestionOption():
    error = None  # Initialize error variable
    page = request.args.get('page', 1, type=int)
    total_pages = 1  # Set the total_pages variable, update if pagination is needed

    if request.method == 'POST':
        survey_id = request.form['survey_id']
        question_id = request.form['question_id']
        option_value = request.form['option_value']

        connection = get_db_connection()
        cursor = connection.cursor()

        # Check if the survey_id, question_id, and old_option_value exist
        cursor.execute('SELECT * FROM [Ujsurvey].[dbo].[QuestionOptions] WHERE Survey_ID = ? AND Question_ID = ? AND Question_Options = ?', (survey_id, question_id, option_value))
        question_option = cursor.fetchone()
        
        if not question_option:
            error = "No such data in the record."
            connection.close()
            return render_template('administrator.html', error=error, page=page, total_pages=total_pages)
        else:
            # Delete the question option
            delete_query = '''
            DELETE FROM [Ujsurvey].[dbo].[QuestionOptions]
            WHERE Survey_ID = ? AND Question_ID = ? AND Question_Options = ?
            '''
            cursor.execute(delete_query, (survey_id, question_id, option_value))
            connection.commit()
            connection.close()
            flash('Question Option deleted successfully!')

            return redirect(url_for('dashboardAdministrator', page=page))

    return render_template('administrator.html', error=error, page=page, total_pages=total_pages)


# Display all responses per question
@app.route('/display_all_responses_per_question', methods=['GET', 'POST'])
def displayResponsesPerQuestion():
    page = request.args.get('page', 1, type=int)
    per_page = 6  # Number of items per page

    survey_id = None
    question_id = None
    error = None

    if request.method == 'POST':
        survey_id = request.form.get('survey_id')
        question_id = request.form.get('question_id')
    else:
        survey_id = request.args.get('survey_id')
        question_id = request.args.get('question_id')

    if survey_id or question_id:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Construct the base query and params
        base_query = 'SELECT COUNT(*) FROM [Ujsurvey].[dbo].[Responses] WHERE 1=1'
        params = []

        if survey_id:
            base_query += ' AND Survey_ID = ?'
            params.append(survey_id)

        if question_id:
            base_query += ' AND Question_ID = ?'
            params.append(question_id)

        # Fetch total number of responses
        cursor.execute(base_query, params)
        total_responses = cursor.fetchone()[0]

        if total_responses == 0:
            error = "No responses found for the provided criteria."
            return render_template('administrator.html', error=error, page=page, total_pages=1)

        # Calculate total pages
        total_pages = (total_responses + per_page - 1) // per_page
        offset = (page - 1) * per_page

        # Construct the query for fetching responses with pagination
        query = 'SELECT * FROM [Ujsurvey].[dbo].[Responses] WHERE 1=1'
        if survey_id:
            query += ' AND Survey_ID = ?'
        if question_id:
            query += ' AND Question_ID = ?'
        query += ' ORDER BY Question_ID OFFSET ? ROWS FETCH NEXT ? ROWS ONLY'

        params += [offset, per_page]
        cursor.execute(query, params)
        responses_per_question = cursor.fetchall()
        connection.close()

    else:
        responses_per_question = []
        total_pages = 1

    return render_template('DisplayAllResponsesPerQuestion.html', QuestionResponse=responses_per_question, page=page, total_pages=total_pages, survey_id=survey_id, question_id=question_id, total_responses=total_responses, error=error)


# Display all usernames in the database
@app.route('/display_all_user_accounts', methods=['GET', 'POST'])
def displayAllUserAccounts():
    page = request.args.get('page', 1, type=int)
    per_page = 15  # Number of items per page

    username_filter = None
    error = None
    if request.method == 'POST':
        username_filter = request.form['username']

    connection = get_db_connection()
    cursor = connection.cursor()

    # Construct the query based on the presence of a username filter
    if username_filter:
        count_query = 'SELECT COUNT(*) FROM [Ujsurvey].[dbo].[Login] WHERE Username LIKE ?'
        cursor.execute(count_query, ('%' + username_filter + '%',))
    else:
        count_query = 'SELECT COUNT(*) FROM [Ujsurvey].[dbo].[Login]'
        cursor.execute(count_query)
        
    total_accounts = cursor.fetchone()[0]

    # Calculate total pages
    total_pages = (total_accounts + per_page - 1) // per_page
    offset = (page - 1) * per_page

    # Fetch user accounts with pagination and optional filter
    if username_filter:
        query = 'SELECT * FROM [Ujsurvey].[dbo].[Login] WHERE Username LIKE ? ORDER BY Login_ID OFFSET ? ROWS FETCH NEXT ? ROWS ONLY'
        cursor.execute(query, ('%' + username_filter + '%', offset, per_page))
    else:
        query = 'SELECT * FROM [Ujsurvey].[dbo].[Login] ORDER BY Login_ID OFFSET ? ROWS FETCH NEXT ? ROWS ONLY'
        cursor.execute(query, (offset, per_page))
        
    all_user_accounts = cursor.fetchall()
    connection.close()

    if not all_user_accounts:
        error = "No such username in our record"

    return render_template('displayingAllUserAccounts.html', all_user_accounts=all_user_accounts, page=page, total_pages=total_pages, username_filter=username_filter, error=error)




# CUSTOM STORED PROCESURE
@app.route('/execute_custom_sql', methods=['GET', 'POST'])
def execute_custom_sql():
    page = request.args.get('page', 1, type=int)
    per_page = 16  # Number of items per page

    if request.method == 'POST':
        survey_id = request.form.get('survey_id', type=int)
    else:
        survey_id = request.args.get('survey_id', type=int)

    if survey_id is None:
        return "Survey_ID is required", 400

    connection = get_db_connection()
    cursor = connection.cursor()

    # Get the total number of rows using the stored procedure
    cursor.execute("{CALL CustomSQL (?)}", survey_id)
    all_rows = cursor.fetchall()
    total_rows = len(all_rows)

    # Calculate the total pages
    total_pages = (total_rows + per_page - 1) // per_page
    offset = (page - 1) * per_page

    # Fetch only the rows for the current page
    paginated_rows = all_rows[offset:offset + per_page]

    # Get column names
    columns = [desc[0] for desc in cursor.description]

    connection.close()

    # Return the result to the client
    return render_template('DisplayAllCustomStockproceedure.html', columns=columns, rows=paginated_rows, page=page, total_pages=total_pages, survey_id=survey_id)











    







































if __name__ == '__main__':
    app.run(debug=True)

 