from flask import Flask, render_template, request, session, url_for, redirect
from sqlalchemy import Column, INTEGER, String, Numeric, Float, create_engine, text

app = Flask(__name__)
# CODE
db_url = 'mysql://root:Tallb0y515@localhost/test_management'
engine = create_engine(db_url, echo=True)
conn = engine.connect()


@app.route('/', methods=['GET'])
def home_page():
    return render_template('index.html')



@app.route('/register', methods=['GET'])
def show_register_form():
    print()
    return render_template('register.html')


@app.route('/register', methods=['POST'])
def add_account():
    user_nums = conn.execute(text(f'SELECT user_no from accounts'))
    next_user = max(user_nums)[0] + 1
    input_email = request.form.get('email')
    dupe_email = conn.execute(text(f'SELECT email from accounts where email = \'{input_email}\'')).all()
    if len(dupe_email) < 1:
        status = 'Account Added'
        conn.execute(text(f'INSERT INTO accounts VALUES ({next_user},:first_name,:last_name,:email,:password,:type)'),
                     request.form)
        conn.commit()
        return render_template('register.html', status=status)
    else:
        status = f'Account not added. Try Again. '
        return render_template('register.html', status=status)


@app.route('/accounts')
def show_accounts():
    types = ['STUDENT', 'TEACHER']
    users = conn.execute(text('SELECT * FROM accounts')).all()
    return render_template('all_accounts.html', users=users, types=types)


@app.route('/accounts_<type>')
def show_type_accounts(type):
    types = ['STUDENT', 'TEACHER']
    accounts = conn.execute(text(f'SELECT * FROM accounts where type = \'{type}\'')).all()
    return render_template('all_accounts.html', users=accounts, types=types)


@app.route('/tests')
def show_test_options():
    return render_template('test_options.html')


@app.route('/tests/view')
def show_all_tests():
    tests = conn.execute(text(
        'select test_no,concat(a.first_name, \' \', a.last_name)as name,num_questions from tests join accounts a on (user_no = assigned_by);')).all()
    questions = conn.execute(text('Select * from test_questions')).all()
    print(tests)
    return render_template('all_tests.html', tests=tests, questions=questions)


@app.route('/tests/delete', methods=['GET'])
def show_delete_form():
    return render_template('delete_test.html')


@app.route('/tests/delete', methods=['POST'])
def delete_test():
    test_no = request.form.get('test_no')
    exists = conn.execute(text(f'Select * from tests where test_no = {test_no}')).all()
    if len(exists) > 0:
        success = 'Test Deleted'
        conn.execute(text(f'Delete from test_questions where test_no = {test_no}'))
        conn.execute(text(f'Delete from student_test where test_no = {test_no}'))
        conn.execute(text(f'Delete from tests where test_no = {test_no}'))
        conn.commit()
        return render_template('delete_test.html', success=success)
    else:
        success = 'Test Number Doesnt Exist'
        return render_template('delete_test.html', success=success)


@app.route('/tests/create', methods=["GET"])
def show_create_form():
    return render_template('create_test.html')


@app.route('/tests/create', methods=['POST'])
def create_test():
    test_no = conn.execute(text('select test_no from tests')).all()
    next_test_no = max(test_no)[0] + 1
    input_email = request.form.get('email')
    input_num_ques = request.form.get('num_questions')
    dupe_test = conn.execute(text(f'Select test_no from tests where test_no = {next_test_no}')).all()
    is_teach = conn.execute(
        text(f'Select user_no from accounts where email = \'{input_email}\' and type = \'TEACHER\'')).all()
    if len(dupe_test) < 1 and len(is_teach) > 0 and int(input_num_ques) > 0:
        conn.execute(text(f'Insert into tests values ({next_test_no}, {is_teach[0][0]}, :num_questions)'), request.form)
        conn.commit()
        return redirect(url_for('show_create_questions', test_no=next_test_no, num_questions=input_num_ques))
    elif len(dupe_test) < 1 and len(is_teach) < 1 and int(input_num_ques) > 0:
        success = 'Only Teachers can create Tests.'
        return render_template('create_test.html', success=success)
    elif len(dupe_test) < 1 and len(is_teach) > 0 and int(input_num_ques) < 1:
        success = 'Number of questions must be greater than 0.'
        return render_template('create_test.html', success=success)
    else:
        success = 'Test Number already exists'
        return render_template('create_test.html', success=success)


@app.route('/tests/create_<test_no>_<num_questions>', methods=['GET'])
def show_create_questions(test_no, num_questions):
    num_questions = int(num_questions)
    return render_template('create_test_questions.html', test_no=test_no, num_questions=num_questions)


@app.route('/tests/create_<test_no>_<num_questions>', methods=['POST'])
def add_questions(test_no, num_questions):
    num_questions = int(num_questions)
    questions = request.form.getlist('question')
    counter = 0
    for i in range(1, num_questions + 1):
        conn.execute(text(f'Insert into test_questions values ({test_no},{i},\'{questions[counter]}\')'))
        counter += 1
    success = 'Test Added'
    return render_template('create_test.html', success=success)


@app.route('/tests/take_<test_no>', methods=['GET'])
def show_test_form(test_no):
    questions = conn.execute(text(f'Select question_no,question from test_questions where test_no = {test_no}')).all()
    print(questions)
    return render_template('take_test.html', test_no=test_no, questions=questions)


@app.route('/tests/take_<test_no>', methods=['POST'])
def submit_student_answer(test_no):
    tests = conn.execute(text(
        'select test_no,concat(a.first_name, \' \', a.last_name)as name,num_questions from tests join accounts a '
        'on (user_no = assigned_by);')).all()
    questions = conn.execute(text('Select * from test_questions')).all()
    email = request.form.get('email', '')
    if email != '':
        is_stud = conn.execute(
            text(f'Select user_no from accounts where email = \'{email}\' and type = \'STUDENT\'')).all()
        print(is_stud)
        answers = request.form.getlist('answer')
        if len(is_stud) > 0:
            taken_already = conn.execute(
                text(f'Select * from student_test where user_no = {is_stud[0][0]} and test_no = {test_no}')).all()
            if len(taken_already) < 1:
                success = 'Test Taken'
                for i in range(1, len(answers) + 1):
                    conn.execute(text(
                        f'INSERT INTO student_test (user_no,test_no,question_no,answer) values ({is_stud[0][0]},{test_no},{i},\'{answers[i - 1]}\')'))
                    conn.commit()
                return render_template('all_tests.html', success=success, tests=tests, questions=questions)
            else:
                success = 'Test was already taken'
                return render_template('all_tests.html', success=success, tests=tests, questions=questions)
        else:
            success = 'Must be a student to take a test'
            return render_template('all_tests.html', success=success, tests=tests, questions=questions)
    else:
        success = 'Please Enter Email'
        return render_template('all_tests.html', success=success, tests=tests, questions=questions)


@app.route('/accounts/view_<user_no>', methods=['GET'])
def show_test_answers(user_no):
    conn.execute(text(f'SET sql_mode=(SELECT REPLACE(@@sql_mode,\'ONLY_FULL_GROUP_BY\',\'\'));'))
    conn.commit()
    total_questions = 0
    all_tests = conn.execute(text(
        f'select user_no,test_no,question_no,answer,question from student_test natural join test_questions where user_no = {user_no};')).all()
    amt_questions = conn.execute(
        text(f'SELECT count(test_no),test_no from student_test where user_no = {user_no} group by test_no;')).all()
    amt_tests = len(amt_questions)
    for q in amt_questions:
        total_questions += int(q[0])
    return render_template('show_test_answers.html', amt_tests=amt_tests, total_questions=total_questions,
                           amt_questions=amt_questions, all_tests=all_tests)


@app.route('/tests/edit')
def show_edit_form():
    return render_template('edit_tests.html')


@app.route('/tests/edit', methods=['POST'])
def edit_test():
    test_no = request.form.get('test_no')
    question_no = request.form.get('question_no')
    new_question = request.form.get('question')
    exists = conn.execute(
        text(f'Select * from test_questions where test_no = {test_no} and question_no = {question_no}')).all()
    if len(exists) > 0:
        success = 'Test Edited'
        conn.execute(text(
            f'Update test_questions set question = \'{new_question}\' where test_no = {test_no} and question_no = {question_no}'))
        conn.commit()
        return render_template('edit_tests.html', success=success)

    else:
        success = 'Test number or question number do not exist'
        return render_template('edit_tests.html', success=success)


if __name__ == '__main__':
    app.run(debug=True)

# Create global session variable
# Give user logged in session
