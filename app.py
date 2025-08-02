from flask import Flask, render_template, request, redirect, session, url_for,flash
from flask_mysqldb import MySQL
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime
import random
import base64
import time
import requests


app = Flask(__name__)
app.secret_key = "jobportal123"

def send_email(subject, body, receiver_email):
    sender_email = "deeptilapy@gmail.com"
    sender_password = "ahbgohmjihgytmsm"
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

def login_location():
    try:
        ip = requests.get("https://api.ipify.org").text.strip()
        response = requests.get(f"https://get.geojs.io/v1/ip/geo/{ip}.json")
        geo_data = response.json()
        city = geo_data.get("city", "Unknown City")
        country = geo_data.get("country", "Unknown Country")
        location = f"{city}, {country}"
        return location
    except Exception as e:
        return f"Location unavailable ({e})"

# MySQL Config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'jobportal'
app.config['MYSQL_PASSWORD'] = 'deepti2@2006'  # Your MySQL password
app.config['MYSQL_DB'] = 'job_portal'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

real_datetime = datetime.datetime.now()
current_date = real_datetime.strftime("%d-%m-%Y")
current_time = real_datetime.strftime("%H:%M")
# Home
@app.route("/")
def index():
    return render_template("index.html")

# Company Signup/Login
@app.route("/signup_company", methods=["GET", "POST"])
def signup_company():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        mobile_num = request.form["mobile"]
        country_code = request.form["country_code"]
        mobile = f"{country_code} {mobile_num}"
        industry_type = request.form["industry_type"]
        company_type = request.form["company_type"]
        company_website = request.form["company_website"]
        country = request.form["country"]
        state = request.form["state"]
        city = request.form["city"]
        pin = request.form["pin"]
        adress = f"{country}, {state}, {city}, {pin}"
        contact_persion_name = request.form["contact_persion_name"]
        contact_persion_position = request.form["contact_persion_position"]
        gst = request.form["gst"]
        company_registration_date = request.form["registration_date"]

        cur = mysql.connection.cursor()
        cur.execute("SELECT 1 FROM companies WHERE email = %s LIMIT 1", (email,))
        result = cur.fetchone()
        cur.close()
        if result:
            return "The email is already taken"
        else:
            otp = str(random.randint(100000, 999999))
            session['temp_company'] = {'name': name,
                                    'email': email,
                                    'otp': otp,
                                    'mobile' : mobile,
                                    'industry_type':industry_type,
                                    'company_type':company_type,
                                    'company_website': company_website,
                                    'adress': adress,
                                    'contact_persion_name':contact_persion_name,
                                    'contact_persion_position':contact_persion_position,
                                    'gst':gst,
                                    'company_registration_date': company_registration_date
                                    }
            receiver_email = email
            subject ="!important"
            body = f"""
                    <html>
                    <body>
                        <p style="color: #000000; font-size: 20px;">Hello</p>
                        <p style="color: #000000; font-size: 15px;">your otp for signup</p><br>
                        <p style="color: #000000; font-size: 23px;"><b>{otp}<b></p><br>
                    </body>
                    </html>
                    """
            send_email(subject, body, receiver_email)
            return redirect('/verify_c')
    return render_template("signup_company.html")

@app.route('/verify_c', methods=['GET', 'POST'])
def verify_c():
    if request.method == 'POST':
        entered_otp = request.form['otp']
        if 'temp_company' in session and entered_otp == session['temp_company']['otp']:
            return redirect('/set-password_c')
        return render_template('verify_otp.html', error="Invalid OTP")
    return render_template('verify_otp.html')

@app.route('/set-password_c', methods=['GET', 'POST'])
def set_password_c():
    if request.method == 'POST':
        pwd = request.form['pass']
        confirm = request.form['password']
        if pwd == confirm:
            # image = None
            cur = mysql.connection.cursor()
            data_company = session['temp_company']
            cur.execute("INSERT INTO companies (name, email, password, mobile, industry_type, company_type, company_website, adress, contact_persion_name," \
                        "contact_persion_position, gst, company_registration_date, registration_date, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (data_company['name'], data_company['email'], pwd,  data_company['mobile'], data_company['industry_type'], data_company['company_type'], data_company['company_website'], data_company['adress'],
                        data_company['contact_persion_name'], data_company['contact_persion_position'], data_company['gst'], data_company['company_registration_date'], current_date, "pending"))
            mysql.connection.commit()
            session.pop('temp_company')
            return redirect('/success')
        return render_template('set_password.html', error="Passwords do not match.")
    return render_template('set_password.html')



@app.route("/login_company", methods=["GET", "POST"])
def login_company():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM companies WHERE email=%s AND password=%s", (email, password))
        company = cur.fetchone()
        cur.close()
        if company:
            session["company_id"] = company["id"]
            session["company_name"] = company["name"]
            session["company_email"] = company["email"]
            if company["status"] == "pending":
                session.clear()
                return "<h1>❌ your account is now not Activate	 ❌</h1>"
            if company["status"] == "blocked":
                session.clear()
                return "<h1>❌ your account is Blocked ❌</h1>"
            if not company["logo"]:
                return redirect("/company_pic")
            location = login_location()
            receiver_email = session["company_email"]
            subject ="!important"
            body = f"""
                <html>
                <body>
                    <p  style="color: #000000; font-size: 20px;">Hello</p>
                    <p  style="color: #000000; font-size: 20px;">your account is now loged in at</p><br>
                    <p style="color: ##00FFFF; font-size: 20px;"><b>{ location }</b></p>
                    <p style="color: #000000; font-size: 10px;"><b>{ current_time }</b></p><br>
                    <p style="color: #000000; font-size: 15px;">if not you please change the password</font></p>
                </body>
                </html>
                """
            login_info = f"{current_date} || {location} || {current_time}"
            send_email(subject, body, receiver_email)
            cur = mysql.connection.cursor()
            cur.execute("UPDATE companies SET login_info=%s WHERE id=%s",(login_info, session["company_id"]))
            mysql.connection.commit()
            cur.close()
            return redirect("/hbddrtye-dc")
        return render_template("login_company.html", error="Invalid email or password")
    return render_template("login_company.html")


@app.route("/company_pic", methods=["GET", "POST"])
def profile_pic_c():
    if request.method == "POST":
            file = request.files['photo']
            if file:
                data = None
                filename = file.filename
                image_data = file.read()
                cur = mysql.connection.cursor()
                cur.execute("UPDATE companies SET logo=%s WHERE id=%s",(data, session["company_id"]))
                cur.execute("UPDATE companies SET logo=%s WHERE id=%s",(image_data, session["company_id"]))
                mysql.connection.commit()
                cur.close()
                return redirect("/")
    return render_template("get_profile_pic.html")


@app.route("/hbddrtye-dc", methods=["GET", "POST"])
def dashboard_company():
    if "company_id" not in session:
        return redirect("/login_company")
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM jobs WHERE company_id=%s", (session["company_id"],))
    jobs = cur.fetchall()
    return render_template("dashboard_company.html", jobs=jobs)   #applications=applications



@app.route("/company_profile")
def company_profile():
        if "company_id" not in session:
            return redirect("/login_company")
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM companies WHERE id=%s",(session["company_id"],))
        company_details = cur.fetchall()
        cur.execute("SELECT logo FROM companies WHERE id=%s",(session["company_id"],))
        photo = cur.fetchone()
        cur.close()
        photo_list = []
        if photo and photo["logo"]:
            image_blob = photo["logo"]
            b64_image = base64.b64encode(image_blob).decode('utf-8')
            photo_list.append({'image_data': b64_image})
        return render_template("company_profile.html",photos=photo_list, details=company_details)




@app.route('/edit_profile_c', methods=['GET', 'POST'])
def edit_profile_c():
    if "company_id" not in session:
        return redirect("/login_company") # make sure user is logged in
    cur = mysql.connection.cursor()
    cur.execute("SELECT logo FROM companies WHERE id=%s",(session["company_id"],))
    photo = cur.fetchone()
    photo_list = []
    if photo and photo["logo"]:
        image_blob = photo["logo"]
        b64_image = base64.b64encode(image_blob).decode('utf-8')
        photo_list.append({'image_data': b64_image})
    if request.method == 'POST':
        name = request.form['name']
        mobile = request.form['mobile']
        company_type = request.form['company_type']
        company_website = request.form['company_website']
        adress = request.form['adress']
        contact_persion_name = request.form['contact_persion_name']
        contact_persion_position = request.form['contact_persion_position']
        cur = mysql.connection.cursor()
        cur.execute("UPDATE companies SET name = %s, mobile = %s, company_type=%s, company_website=%s, adress = %s, contact_persion_name=%s, " \
        "contact_persion_position=%s WHERE id = %s ",
                    (name, mobile, company_type, company_website, adress, contact_persion_name, contact_persion_position, session["company_id"]))
        mysql.connection.commit()
        cur.close()
        return render_template("sucessfull_update.html")
    # GET: fetch existing profile data
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM companies WHERE id = %s", ( session["company_id"],))
    user = cur.fetchone()
    cur.close()
    return render_template('edit_profile_c.html', user=user, photos=photo_list)



@app.route("/edit_company_logo", methods=["GET", "POST"])
def edit_profile_pic_c():
    if "company_id" not in session:
        return redirect("/login_company")
    
    photo_list = []  # ✅ Always define it
    
    if request.method == "POST":
        file = request.files.get('photo')
        if file and file.filename != '':
            image_data = file.read()
            cur = mysql.connection.cursor()
            cur.execute("UPDATE companies SET logo=%s WHERE id=%s", (image_data, session["company_id"]))
            mysql.connection.commit()
            cur.close()
            
            # b64_image = base64.b64encode(image_data).decode('utf-8')
            # photo_list.append({'image_data': b64_image})
            
            time.sleep(3)
            return redirect("/edit_profile_c")
    # On GET, fetch the current photo to show
    cur = mysql.connection.cursor()
    cur.execute("SELECT logo FROM companies WHERE id=%s", (session["company_id"],))
    photo = cur.fetchone()
    cur.close()
    if photo and photo["logo"]:
        image_blob = photo["logo"]
        b64_image = base64.b64encode(image_blob).decode('utf-8')
        photo_list.append({'image_data': b64_image})

    return render_template("get_profile_pic.html", photos=photo_list)


@app.route("/change_password_c", methods=["GET", "POST"])
def change_password_c():
    if "company_id" not in session:
        return redirect("/login_company")
    if request.method == "POST":
        current = request.form['current_password']
        new = request.form['new_password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT password FROM companies WHERE id=%s",(session["company_id"],))
        password = cur.fetchone()
        if current == password["password"]:
            cur.execute("UPDATE companies SET password=%s WHERE id=%s",(new, session["company_id"]))
            mysql.connection.commit()
            cur.close()
            flash("Sucess!  password changed!", "sucess")
            time.sleep(2)
            return redirect("/hbddrtye-dc")
        else:
            flash("Error!  Old Password Does not match!", "warning")
    return render_template("change_password_c.html")


@app.route("/forgate_password_c", methods=["GET", "POST"])
def forgate_password_c():
    if "company_id"  and "company_email" not in session:
        return redirect("/login_company")
    
    otp = str(random.randint(100000, 999999))
    session["otp"] = otp
    receiver_email = session["company_email"]
    subject ="!important"
    body =  f"""
            <html>
            <body>
                <p style="color: #000000; font-size: 20px;">Hello</p>
                <p style="color: #000000; font-size: 15px;">your otp for change password</p><br>
                <p style="color: #000000; font-size: 23px;"><b>{otp}<b></p><br>
            </body>
            </html>
            """
    send_email(subject, body, receiver_email)
    if request.method == "POST":
        otp = request.form["otp"]
        if otp == otp:
            return redirect("/new_password_c")
    return render_template("verify_otp.html")


@app.route("/new_password_c", methods=["GET", "POST"])
def new_password_c():
    if "company_id"  and "company_email" and "otp" not in session:
        return redirect("/login_company")
    
    if request.method == "POST":
        new1 = request.form["newpass1"]
        new = request.form["newpass"]
        if new1 == new:
            cur = mysql.connection.cursor()
            cur.execute("UPDATE companies SET password=%s WHERE id=%s AND email=%s",(new1, session["company_id"], session["company_email"]))
            mysql.connection.commit()
            cur.close()
            session.pop('otp', None)
            flash("Sucess!  Passwod changed!", "sucess")
            time.sleep(3)
            return redirect("/hbddrtye-dc")
        else:
            flash("Error! Password Does not match!", "warning")
    return render_template("new_password.html")



@app.route("/forgate_password_email_c", methods=["GET", "POST"])
def forgate_password_by_email_c():
    action = request.form.get('action')
    if action == 'send':
        gmail = request.form["email"]
        email_list=[]
        cur = mysql.connection.cursor()
        cur.execute("SELECT email FROM companies")
        emails = cur.fetchall()
        for email in emails:
            email_list.append(email['email'])
        print(email_list)
        if gmail in email_list:
            session["c_gmail"] = gmail
            otp = str(random.randint(100000, 999999))
            session["otp"] = otp
            receiver_email = gmail
            subject ="!important"
            body = f"""
                    <html>
                    <body>
                        <p style="color: #000000; font-size: 20px;">Hello</p>
                        <p style="color: #000000; font-size: 15px;">your otp for change password</p><br>
                        <p style="color: #000000; font-size: 23px;"><b>{otp}<b></p><br>
                    </body>
                    </html>
                    """
            send_email(subject, body, receiver_email)
        else:
            flash("Email not exist", "danger")
    if action == 'verify':
        otp_input = request.form["otp"]
        if otp_input ==  session["otp"]:
            session.pop('otp', None)
            time.sleep(2)
            return redirect("/new_password_email_c")
        else:
            flash("Invalid OTP", "danger")
    return render_template("verify_otp_by_email_c.html")


@app.route("/new_password_email_c", methods=["GET", "POST"])
def new_password_email_c():
    if "c_gmail" not in session:
        return redirect("/login_company")
    if request.method == "POST":
        new1 = request.form["newpass1"]
        new = request.form["newpass"]
        if new1 == new:
            cur = mysql.connection.cursor()
            cur.execute("UPDATE companies SET password=%s WHERE email=%s",(new1, session["c_gmail"]))
            mysql.connection.commit()
            cur.close()
            session.pop('otp', None)
            flash("Sucess!  Passwod changed!", "sucess")
            time.sleep(3)
            return redirect("/login_company")
        else:
            flash("Error! Password Does not match!", "warning")
    return render_template("new_password.html")


# Employee Signup/Login
@app.route('/signup_employee', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        mobile = request.form.get('mobile')
        dob = request.form.get('db')
        gender = request.form.get('gender')
        country = request.form.get('country')
        state = request.form.get('state')
        city = request.form.get('city')
        pin = request.form.get('pin')
        adress = f"{country}, {state}, {city}, {pin}"
        qualification = request.form.get('qualification')
        graduation = request.form.get('graduation')
        specialization = request.form.get('specialization')
        role = request.form.get('role')
        location = request.form.get('location')

        cur = mysql.connection.cursor()
        cur.execute("SELECT 1 FROM employees WHERE email = %s LIMIT 1", (email,))
        result = cur.fetchone()
        cur.close()
        if result:
            return "The email is already taken"
        
        otp = str(random.randint(100000, 999999))
        session['temp_user'] = {'name': name,
                                'email': email,
                                'otp': otp,
                                'mobile' : mobile,
                                'dob':dob,
                                'gender':gender,
                                'adress': adress,
                                'qualification': qualification,
                                'graduation':graduation,
                                'specialization':specialization,
                                'role':role,
                                'location':location
                                }
        receiver_email = email
        subject ="!important"
        body = f"""
            <html>
            <body>
                <p style="color: #000000; font-size: 20px;">Hello</p>
                <p style="color: #000000; font-size: 15px;">your otp for signup</p><br>
                <p style="color: #000000; font-size: 23px;"><b>{otp}<b></p><br>
            </body>
            </html>
            """
        send_email(subject, body, receiver_email)
        return redirect('/verify')
    return render_template('signup_employee.html')


# Step 2: Verify OTP
@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        entered_otp = request.form['otp']
        if 'temp_user' in session and entered_otp == session['temp_user']['otp']:
            return redirect('/set-password')
        return render_template('verify_otp.html', error="Invalid OTP")
    return render_template('verify_otp.html')


# Step 3: Set Password
@app.route('/set-password', methods=['GET', 'POST'])
def set_password():
    if request.method == 'POST':
        pwd = request.form['pass']
        confirm = request.form['password']
        if pwd == confirm:
            image = None
            cur = mysql.connection.cursor()
            data = session['temp_user']
            cur.execute("INSERT INTO employees (name, email, password, role, mobile, dob, gender, adress, qualification," \
                        "graduation,specialization, location, registration_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (data['name'], data['email'], pwd,  data['role'], data['mobile'], data['dob'], data['gender'],
                            data['adress'], data['qualification'], data['graduation'], data['specialization'], data['location'], current_date))
            mysql.connection.commit()
            session.pop('temp_user')
            return redirect('/success')
        return render_template('set_password.html', error="Passwords do not match.")
    return render_template('set_password.html')

# Final Page
@app.route('/success')
def success():
    return render_template('success.html')




@app.route("/login_employee", methods=["GET", "POST"])
def login_employee():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM employees WHERE email=%s AND password=%s", (email, password))
        employee = cur.fetchone()
        cur.close()
        if employee:
            session["employee_id"] = employee["id"]
            session["employee_email"] = employee["email"]
            session["employee_name"] = employee["name"]
            
            if not employee["image"]:  # Assuming 'image' is your longblob column
                return redirect("/employee_pic")
            
            if employee["status"] == "Block":
                session.clear()
                return "<h1>❌ your account is Blocked ❌</h1>"
            flash("please Wait...")
            location = login_location()
            receiver_email = session["employee_email"]
            subject ="!important"
            body = f"""
                <html>
                <body>
                    <p  style="color: #000000; font-size: 20px;">Hello</p>
                    <p  style="color: #000000; font-size: 20px;">your account is now loged in at</p><br>
                    <p style="color: ##00FFFF; font-size: 20px;"><b>{ location }</b></p>
                    <p style="color: #000000; font-size: 10px;"><b>{ current_time }</b></p><br>
                    <p style="color: #000000; font-size: 15px;">if not you please change the password</font></p>
                </body>
                </html>
                """
            login_info = f"{current_date} || {location} || {current_time}"
            send_email(subject, body, receiver_email)
            cur = mysql.connection.cursor()
            cur.execute("UPDATE employees SET login_info=%s WHERE id=%s",(login_info, session["employee_id"]))
            mysql.connection.commit()
            cur.close()
            send_email(subject, body, receiver_email)
            return redirect("/dashboard_employee")
        return render_template("login_employee.html", error="Invalid email or password")
    return render_template("login_employee.html")

@app.route("/employee_pic", methods=["GET", "POST"])
def profile_pic():
    if request.method == "POST":
            file = request.files['photo']
            if file:
                data = None
                image_data = file.read()
                cur = mysql.connection.cursor()
                cur.execute("UPDATE employees SET image=%s WHERE id=%s",(data, session["employee_id"]))
                cur.execute("UPDATE employees SET image=%s WHERE id=%s",(image_data, session["employee_id"]))
                mysql.connection.commit()
                cur.close()
                return render_template("success.html")
    return render_template("get_profile_pic.html")


@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    if "employee_id" not in session:
        return redirect("/login_employee")
    if request.method == "POST":
        current = request.form['current_password']
        new = request.form['new_password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT password FROM employees WHERE id=%s",(session["employee_id"],))
        password = cur.fetchone()
        if current == password["password"]:
            cur.execute("UPDATE employees SET password=%s WHERE id=%s",(new, session["employee_id"]))
            mysql.connection.commit()
            cur.close()
            flash("Sucess!  password changed!", "sucess")
        else:
            flash("Error!  Old Password Does not match!", "warning")
    return render_template("change_password.html")


@app.route("/forgate_password_e", methods=["GET", "POST"])
def forgate_password():
    if "employee_id"  and "employee_email" not in session: #gggh
        return redirect("/login_employee")
    
    otp = str(random.randint(100000, 999999))
    session["otp"] = otp
    receiver_email = session["employee_email"]
    subject ="!important"
    body =  f"""
            <html>
            <body>
                <p style="color: #000000; font-size: 20px;">Hello</p>
                <p style="color: #000000; font-size: 15px;">your otp for change password</p><br>
                <p style="color: #000000; font-size: 23px;"><b>{otp}<b></p><br>
            </body>
            </html>
            """
    send_email(subject, body, receiver_email)
    if request.method == "POST":
        otp = request.form["otp"]
        if otp == otp:
            return redirect("/new_password_e")
    return render_template("verify_otp.html")

@app.route("/new_password_e", methods=["GET", "POST"])
def new_password_e():
    if "employee_id"  and "employee_email" and "otp" not in session:
        return redirect("/login_employee")
    if request.method == "POST":
        new1 = request.form["newpass1"]
        new = request.form["newpass"]
        if new1 == new:
            cur = mysql.connection.cursor()
            cur.execute("UPDATE employees SET password=%s WHERE id=%s AND email=%s",(new1, session["employee_id"], session["employee_email"]))
            mysql.connection.commit()
            cur.close()
            session.pop('otp', None)
            flash("Sucess!  Passwod changed!", "sucess")
            time.sleep(3)
            return redirect("/dashboard_employee")
        else:
            flash("Error! Password Does not match!", "warning")
    return render_template("new_password.html")


@app.route("/forgate_password_email_e", methods=["GET", "POST"])
def forgate_password_by_email_e():
    action = request.form.get('action')
    if action == 'send':
        gmail = request.form["email"]
        email_list=[]
        cur = mysql.connection.cursor()
        cur.execute("SELECT email FROM employees")
        emails = cur.fetchall()
        for email in emails:
            email_list.append(email['email'])
        print(email_list)
        if gmail in email_list:
            session["gmail"] = gmail
            otp = str(random.randint(100000, 999999))
            session["otp"] = otp
            receiver_email = gmail
            subject ="!important"
            body =  f"""
                    <html>
                    <body>
                        <p style="color: #000000; font-size: 20px;">Hello</p>
                        <p style="color: #000000; font-size: 15px;">your otp for change password</p><br>
                        <p style="color: #000000; font-size: 23px;"><b>{otp}<b></p><br>
                    </body>
                    </html>
                    """
            send_email(subject, body, receiver_email)
        else:
            flash("Email not exist", "danger")
    if action == 'verify':
        otp_input = request.form["otp"]
        if otp_input ==  session["otp"]:
            session.pop('otp', None)
            time.sleep(2)
            return redirect("/new_password_email_e")
        else:
            flash("Invalid OTP", "danger")
    return render_template("verify_otp_by_email.html")


@app.route("/new_password_email_e", methods=["GET", "POST"])
def new_password_email_e():
    if "gmail" not in session:
        return redirect("/login_employee")
    if request.method == "POST":
        new1 = request.form["newpass1"]
        new = request.form["newpass"]
        if new1 == new:
            cur = mysql.connection.cursor()
            cur.execute("UPDATE employees SET password=%s WHERE email=%s",(new1, session["gmail"]))
            mysql.connection.commit()
            cur.close()
            session.pop('otp', None)
            flash("Sucess!  Passwod changed!", "sucess")
            time.sleep(3)
            return redirect("/login_employee")
        else:
            flash("Error! Password Does not match!", "warning")
    return render_template("new_password.html")



@app.route("/dashboard_employee")
def dashboard_employee():
    if "employee_id" not in session:
        return redirect("/login_employee")
    cur = mysql.connection.cursor()
    cur.execute("SELECT jobs.*, companies.name AS company_name FROM jobs JOIN companies ON jobs.company_id = companies.id")
    jobs = cur.fetchall()
    cur.close()
    return render_template("dashboard_employee.html", jobs=jobs)

@app.route("/dashboard_employee/profile")
def emp_profile():
        if "employee_id" not in session:
            return redirect("/login_employee")
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM employees WHERE id=%s",(session["employee_id"],))
        emp_details = cur.fetchall()
        cur.execute("SELECT image FROM employees WHERE id=%s",(session["employee_id"],))
        photo = cur.fetchone()
        cur.close()

        photo_list = []
        if photo and photo["image"]:
            image_blob = photo["image"]
            b64_image = base64.b64encode(image_blob).decode('utf-8')
            photo_list.append({'image_data': b64_image})

        return render_template("emp_profile.html",photos=photo_list, details=emp_details)


@app.route('/edit_profile_e', methods=['GET', 'POST'])
def edit_profile_e():
    if "employee_id" not in session:
        return redirect("/login_employee") # make sure user is logged in
    cur = mysql.connection.cursor()
    cur.execute("SELECT image FROM employees WHERE id=%s",(session["employee_id"],))
    photo = cur.fetchone()
    photo_list = []
    if photo and photo["image"]:
        image_blob = photo["image"]
        b64_image = base64.b64encode(image_blob).decode('utf-8')
        photo_list.append({'image_data': b64_image})

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        role = request.form['role']
        mobile = request.form['mobile']
        dob = request.form['dob']
        address = request.form['address']
        gender = request.form['gender']

        cur = mysql.connection.cursor()
        cur.execute("UPDATE employees SET name = %s, email = %s, role = %s, mobile = %s, dob=%s, gender=%s, adress = %s WHERE id = %s ",
                    (name, email, role, mobile, dob, gender, address, session["employee_id"]))
        mysql.connection.commit()
        cur.close()
        return render_template("sucessfull_update_e.html")

    # GET: fetch existing profile data
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM employees WHERE id = %s", ( session["employee_id"],))
    user = cur.fetchone()
    cur.close()

    return render_template('edit_profile_e.html', user=user, photos=photo_list)

@app.route("/edit_employee_pic", methods=["GET", "POST"])
def edit_profile_pic_e():
    if "employee_id" not in session:
        return redirect("/login_employee")
    
    photo_list = []  # ✅ Always define it
    
    if request.method == "POST":
        file = request.files.get('photo')
        if file and file.filename != '':
            image_data = file.read()
            cur = mysql.connection.cursor()
            cur.execute("UPDATE employees SET image=%s WHERE id=%s", (image_data, session["employee_id"]))
            mysql.connection.commit()
            cur.close()
            # b64_image = base64.b64encode(image_data).decode('utf-8')
            # photo_list.append({'image_data': b64_image})
            time.sleep(2)
            return redirect("/edit_profile_e")
    # On GET, fetch the current photo to show
    cur = mysql.connection.cursor()
    cur.execute("SELECT image FROM employees WHERE id=%s", (session["employee_id"],))
    photo = cur.fetchone()
    cur.close()
    if photo and photo["image"]:
        image_blob = photo["image"]
        b64_image = base64.b64encode(image_blob).decode('utf-8')
        photo_list.append({'image_data': b64_image})

    return render_template("get_profile_pic.html", photos=photo_list)




@app.route("/details/<int:job_id>/<int:comp_id>")
def details(job_id, comp_id):
    if "employee_id" not in session:
        return redirect("/login_employee")
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM jobs WHERE id=%s AND company_id=%s",(job_id, comp_id))
    jobs = cur.fetchall()
    cur.close()
    return render_template("view_job_details.html", jobs=jobs)


from werkzeug.utils import secure_filename
import os
from datetime import datetime

@app.route("/apply/<int:job_id>/<string:job_title>/<int:comp_id>", methods=["GET", "POST"])
def apply(job_id, job_title, comp_id):
    if "employee_id" not in session:
        return redirect("/login_employee")
    if request.method == "POST":
        row_resume = request.files.get("resume")
        resume = row_resume.read()
        # if resume and resume.filename != '':
        #     filename = secure_filename(resume.filename)
        #     resume_path = os.path.join("static/resumes", filename)
        #     resume.save(resume_path)
        # else:
        #     flash("Resume upload failed or missing.", "danger")
        #     return redirect(url_for('details', job_id=job_id, comp_id=comp_id))

        cur = mysql.connection.cursor()

        # Check if already applied
        cur.execute(
            "SELECT id FROM applications WHERE job_id=%s AND employee_id=%s",
            (job_id, session["employee_id"])
        )
        existing = cur.fetchone()
        cur.execute(
            "SELECT id FROM status WHERE job_id=%s AND employee_id=%s",
            (job_id, session["employee_id"])
        )
        existing2 = cur.fetchone()

        if existing or existing2:
            cur.close()
            flash("You have already applied for this job.", "warning")
            return redirect(url_for('details', job_id=job_id, comp_id=comp_id))

        # Insert application with resume path
        cur.execute("INSERT INTO applications (job_id, employee_id, employee_email, employee_name, job_title, comp_id, resume) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (job_id, session["employee_id"], session["employee_email"], session["employee_name"], job_title, comp_id, resume))

        # Get company name
        cur.execute("SELECT name FROM companies WHERE id=%s", (comp_id,))
        res = cur.fetchone()
        comp_name = res["name"]
        # Insert into status
        cur.execute("INSERT INTO status (employee_id, company_id, job_id, job_title, company_name, apply_date) VALUES (%s, %s, %s, %s, %s, %s)",
                    (session["employee_id"], comp_id, job_id, job_title, comp_name, current_date))
        mysql.connection.commit()
        cur.close()
        flash("Applied successfully with resume.", "success")
        return redirect(url_for('details', job_id=job_id, comp_id=comp_id))
    return render_template("view_job_details.html")


@app.route("/removehsspx/<int:job_id>")
def remove(job_id):
    print(job_id)
    if "company_id" in session:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM jobs WHERE id = %s AND company_id = %s",
                    (job_id, session["company_id"]))
        mysql.connection.commit()
        cur.close()
    return redirect("/hbddrtye-dc")


@app.route("/company_ap")
def company_ap():
    if "company_id" not in session:
        return redirect("/login_company")
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM applications WHERE job_id IN (SELECT id FROM jobs WHERE company_id=%s)", (session["company_id"],))
    applications = cur.fetchall()
    cur.close()
    # Add base64 image data to each application
    for app in applications:
        if app.get("resume"):
            image_blob = app["resume"]
            b64_image = base64.b64encode(image_blob).decode('utf-8')
            app["resume_base64"] = b64_image
        else:
            app["resume_base64"] = None

    return render_template("company_ap.html", applications=applications)

@app.route("/aprove/<string:job_title>/<string:employee_email>/<string:employee_name>/<int:job_id>/<int:employee_id>")
def aprove(job_title, employee_email, employee_name, job_id, employee_id):
    if "company_id" not in session:
        return redirect("/login_company")
    print("Received employee email:", employee_email)
    by = f"by:-{session["company_name"]}/n{current_date}"
    receiver_email = employee_email
    subject ="congraculation"
    body = f"""
        <html>
        <body>
            <p style="color: #000000; font-size: 20px;">Hello, {employee_name}</p>
            <p style="color: #000000; font-size: 15px;">your Resume is selected by our company</p>
            <p style="color: #000000; font-size: 15px;">our team contact you very soon, thanku</p><br>
            <p style="color: #000000; font-size: 23px;"><b>{by}<b></p><br>
        </body>
        </html>
        """
    send_email(subject, body, receiver_email)
    print("Email sent successfully!")
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO aproved (company_id, title, job_id, employee_name, employee_email) VALUES (%s, %s, %s, %s, %s)",
                (session["company_id"], job_title, job_id,employee_name,employee_email))
    
    cur.execute('UPDATE status SET status = %s WHERE job_id=%s AND employee_id=%s AND company_id=%s',
        ("✅Aprover", job_id, employee_id, session["company_id"]))
    
    cur.execute(
    "UPDATE status SET activity_date = %s WHERE employee_id=%s AND company_id=%s AND job_id=%s",
    (current_date,employee_id, session["company_id"], job_id))

    cur.execute("DELETE FROM applications WHERE job_id=%s AND employee_id=%s AND comp_id=%s", (job_id, employee_id, session["company_id"]))
    mysql.connection.commit()
    cur.close()
    print(employee_id)
    return redirect("/company_ap")
    return render_template("company_ap.html")


@app.route("/remove_ap/<int:job_id>/<int:employee_id>")
def remove_ap(job_id, employee_id):
    if "company_id" in session:
        cur = mysql.connection.cursor()
        cur.execute('UPDATE status SET status = %s WHERE job_id=%s AND employee_id=%s AND company_id=%s',
        ("❌Rejected", job_id, employee_id, session["company_id"]))
        
        cur.execute(
        "UPDATE status SET activity_date = %s WHERE employee_id=%s AND company_id=%s AND job_id=%s",
        (current_date, employee_id, session["company_id"], job_id))

        cur.execute("DELETE FROM applications WHERE job_id=%s AND employee_id=%s AND comp_id=%s", (job_id, employee_id, session["company_id"]))
        mysql.connection.commit()
        cur.close()
        return redirect("/company_ap")
    return render_template("company_ap.html")





@app.route("/aproved_clint")      #methods=["GET", "POST"]
def aproved_clint():
    if "company_id" not in session:
        return redirect("/login_company")
        print("hello")
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM aproved WHERE company_id=%s", (session["company_id"],))
    applications = cur.fetchall()
    cur.close()
    return render_template("aproved_clint.html",applications = applications) # , applications=applications


# Application status
@app.route("/status")
def emp_apc_status():
    if "employee_id" not in session:
        return redirect("/login_employee")
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM status WHERE employee_id=%s", (session["employee_id"],))
    status = cur.fetchall()
    cur.close()
    return render_template("emp_apc_status.html", status=status)


@app.route("/postjob", methods=["GET", "POST"])
def company_post_job():
    if "company_id" not in session:
        return redirect("/login_company")
    cur = mysql.connection.cursor()
    if request.method == "POST":
        title = request.form["title"]
        jobrole = request.form["role"]
        job_type = request.form["job_type"]
        country = request.form["country"]
        state = request.form["state"]
        city = request.form["city"]
        pin = request.form["pin"]
        location = f"{country}, {state}, {city}, {pin}"
        salary1 = request.form["slary1"]
        salary2 = request.form["slary2"]
        salarytime = request.form["salarytime"]
        work_Arrangement = request.form["Work_Arrangement"]
        salary = f"₹{salary1} - ₹{salary2}/{salarytime}"
        employment_Type = request.form["Employment_Type"]
        profesion = request.form["profesion"]
        experience = request.form["experience"]
        compskil = request.form["compskil"]
        lastdate = request.form["date"]
        description = request.form["description"]
        # print(type(lastdate))
        cur.execute("INSERT INTO jobs (company_id, title, description, job_role, job_type, country, state, city, pin, work_Arrangement, salary, employment_Type, profesion, experience, comp_skil, lastdate, company_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (session["company_id"], title, description, jobrole, job_type, country, state, city, pin, work_Arrangement, salary, employment_Type, profesion,
                    experience, compskil, lastdate, session["company_name"]))
        mysql.connection.commit()
    return render_template("company_p_job.html",)

# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")



#     <------------admin start---------->        #

@app.route("/2300", methods=["GET", "POST"])
def admin_logn():
    if request.method == "POST":
        adminid = request.form["adminid"]
        admin_password = request.form["adminpassword"]

        if adminid == "deepti" and admin_password == "rudra":
            session["a_id"] = adminid
            session["a_password"] = admin_password
            return redirect("/admin_dashboard")
        else:
            flash("Invalid password")
    return render_template("admin_login.html")

@app.route("/admin_dashboard")
def admin_dashboard():
    if "a_id"  not in session:
        return redirect("/")
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) AS total FROM companies")
    t_company = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) AS total_a FROM companies WHERE status=%s",("aproved",))
    t_a_company = cur.fetchone()["total_a"]

    cur.execute("SELECT COUNT(*) AS total_un_a FROM companies WHERE status=%s",("pending",))
    t_un_a_company = cur.fetchone()["total_un_a"]

    cur.execute("SELECT COUNT(*) AS total_e FROM employees")
    total_e = cur.fetchone()["total_e"]

    cur.execute("SELECT COUNT(*) AS total_a FROM applications")
    total_a = cur.fetchone()["total_a"]

    cur.execute("SELECT COUNT(*) AS total_j FROM jobs")
    total_j = cur.fetchone()["total_j"]
    cur.close()
    return render_template("admin_dashboard.html", t_company=t_company, t_a_company=t_a_company, t_un_a_company=t_un_a_company, total_e=total_e,
                            total_a=total_a, total_j=total_j)

@app.route("/2300/admin_dashboard/new_company")
def admin_dashboard_new_companyes():
    if "a_id"  not in session:
        return redirect("/")
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM companies WHERE status =%s",("pending",))
    company = cur.fetchall()
    cur.close()
    return render_template("a_pending_company.html", companyes = company)

@app.route("/2300/admin_dashboard/companyes")
def admin_total_company():
    if "a_id"  not in session:
            return redirect("/")
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM companies WHERE status=%s",("aproved",))
    companyes = cur.fetchall()
    cur.close()
    return render_template("a_total_company.html", companyes = companyes)

@app.route("/2300/admin_dashboard/seeker")
def admin_total_employee():
    if "a_id"  not in session:
            return redirect("/")
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM employees")
    employees = cur.fetchall()
    cur.close()
    for image in employees:
        if image.get("image"):
            image_blob = image["image"]
            b64_image = base64.b64encode(image_blob).decode('utf-8')
            image["resume_base64"] = b64_image
        else:
            image["resume_base64"] = None
    return render_template("a_total_employee.html", employees = employees)

@app.route("/2300/admin_dashboard/applications")
def admin_total_applications():
    if "a_id"  not in session:
        return redirect("/")
    cur = mysql.connection.cursor()
    cur.execute("SELECT  comp_id, job_id, job_title, employee_id, employee_name, employee_email FROM applications ")
    applications = cur.fetchall()
    cur.close()
    return render_template("a_all_application.html", applications = applications)

@app.route("/2300/admin_dashboard/active_jobs")
def admin_all_jobs():
    if "a_id" not in session:
        return redirect("/")
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM jobs")
    jobs = cur.fetchall()
    cur.close()
    return render_template("a_jobs.html", jobs = jobs)

@app.route("/2300/admin_dashboard/seeker/edit/<int:emp_id>",methods=["GET", "POST"])
def a_edit_profile_e(emp_id):
    if "a_id" not in session:
        return redirect("/")
    cur = mysql.connection.cursor()
    cur.execute("SELECT image FROM employees WHERE id=%s",(emp_id,))
    photo = cur.fetchone()
    photo_list = []
    if photo and photo["image"]:
        image_blob = photo["image"]
        b64_image = base64.b64encode(image_blob).decode('utf-8')
        photo_list.append({'image_data': b64_image})
        if request.method == 'POST':
            name = request.form['name']
            email = request.form['email']
            role = request.form['role']
            mobile = request.form['mobile']
            dob = request.form['dob']
            address = request.form['address']
            gender = request.form['gender']
            cur = mysql.connection.cursor()
            cur.execute("UPDATE employees SET name = %s, email = %s, role = %s, mobile = %s, dob=%s, gender=%s, adress = %s WHERE id = %s ",
                        (name, email, role, mobile, dob, gender, address, emp_id))
            mysql.connection.commit()
            cur.close()
            flash("Profile updated successfully!")
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM employees WHERE id=%s",(emp_id,))
    user = cur.fetchone()
    cur.close()
    return render_template("a_edit_pro_e.html", user=user, photos=photo_list)

@app.route("/2300/admin_dashboard/seeker/Delete/<int:emp_id>")
def a_delete_emp(emp_id):
    if "a_id" not in session:
        return redirect("/")
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM employees WHERE id=%s", (emp_id,))
    mysql.connection.commit()
    cur.close()

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM employees")
    employees = cur.fetchall()
    cur.close()
    # return render_template("a_total_employee.html", employees=employees)
    return redirect("/2300/admin_dashboard/seeker")

@app.route("/2300/admin_dashboard/seeker/status", methods=["POST"])
def a_status_emp():
    if "a_id" not in session:
        return redirect("/")
    emp_id = request.form.get("emp_id")
    action = request.form.get("action")
    if not emp_id or not action:
        return "Invalid form submission", 400
    new_status = "Block" if action == "Block" else "Unblocked"

    cur = mysql.connection.cursor()
    cur.execute("UPDATE employees SET status=%s WHERE id=%s", (new_status, emp_id))
    mysql.connection.commit()
    cur.close()
    return redirect("/2300/admin_dashboard/seeker")

@app.route("/admin_dashboardadmin_dashboard/companyes/status",methods=["POST"])
def a_aprove_company():
    if "a_id" not in session:
        return redirect("/")
    company_id = request.form.get("company_id")
    action = request.form.get("action")
    if not company_id or not action:
        return "Invalid form submission", 400
    if action == "aprove":
        cur = mysql.connection.cursor()
        cur.execute("UPDATE companies SET status = %s WHERE id=%s",("Aproved", company_id))
        mysql.connection.commit()
        cur.execute("SELECT email FROM companies WHERE id=%s",(company_id,))
        r_email = cur.fetchone()
        receiver_email = r_email["email"]
        subject = "Notice!"
        body = f"""<html>
                    <body>
                    <p style="color: #000000; font-size: 20px;">Hello,</p>
                    <p style="color: #000000; font-size: 15px;">This is a Notice from jobportal</p>
                    <p style="color: #000000; font-size: 15px;">your Accont is now Activate</p><br>
                    <p style="color: #000000; font-size: 23px;"><b>Thank you<b></p><br>
                    </body>
                    </html>
                """
        send_email(subject, body, receiver_email)
        cur.close()
    if action == "reject":
        cur = mysql.connection.cursor()
        cur.execute("UPDATE companies SET status = %s WHERE id=%s",("Rejected ",company_id))
        mysql.connection.commit()
        cur.execute("SELECT email FROM companies WHERE id=%s",(company_id,))
        r_email = cur.fetchone()
        receiver_email = r_email["email"]
        subject = "Notice!"
        body = f"""<html>
                    <body>
                    <p style="color: #000000; font-size: 20px;">Hello,</p>
                    <p style="color: #000000; font-size: 15px;">This is a Notice from jobportal</p>
                    <p style="color: #000000; font-size: 15px;">your Accont is Rejected due to some wrong information</p><br>
                    <p style="color: #000000; font-size: 15px;">You can Reapply</p><br>
                    <p style="color: #000000; font-size: 23px;"><b>Thank you<b></p><br>
                    </body>
                    </html>
                """
        send_email(subject, body, receiver_email)
        cur.execute("DELETE FROM companies WHERE id=%s",(company_id,))
        mysql.connection.commit()
        cur.close()
    return redirect("/2300/admin_dashboard/new_company")

@app.route("/admin_dashboard/companyes/status", methods=["POST"])
def a_b_unb_company():
    if "a_id" not in session:
        return redirect("/")
    company_id = request.form.get("company_id")
    action = request.form.get("action")
    if not company_id or not action:
        return "Invalid form submission", 400
    if action == "Block":
        cur = mysql.connection.cursor()
        cur.execute("UPDATE companies SET status = %s WHERE id=%s",("Block",company_id))
        mysql.connection.commit()
        cur.close()
    if action == "Unblock":
        cur = mysql.connection.cursor()
        cur.execute("UPDATE companies SET status = %s WHERE id=%s",("Unblocked",company_id))
        mysql.connection.commit()
        cur.close()
    return redirect("/admin_dashboard/companyes")


if __name__ == "__main__":
    app.run(debug=True)
