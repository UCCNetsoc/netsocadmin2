from flask import Flask, request, render_template
import register_tools as r 

import string, random, crypt 


HOST = "127.0.0.1"
PORT = "5000"
app = Flask(__name__)

"""
Route: /
    This route is for the index directory.
    If the user goes to this, it will load the register.html template.
"""
@app.route('/')
def register():
    return render_template("register.html")



"""
Route: /sendconfirmation
    Users will be lead to this route when they submit an email for server sign up from route /
    sendconfirmation() will check whether users posted data via a form.
    It then checks that form data to make sure it's a valid UCC email.
    Sends an email with a link to validate the email holder is who is registering.
"""
@app.route("/sendconfirmation", methods=["POST", "GET"])
def sendconfirmation():
    if request.method != "POST":
        return render_template("register.html")
    form = request.form           
    email = form['email']         
    if "umail.ucc.ie" not in email:
        return render_template("register.html", error_message="Must be a UCC Umail email address")
    confirmation_sent = r.send_confirmation_email(email, "%s:%s"%(HOST, PORT))
    if confirmation_sent:
        return render_template("sentconfirmation.html", email=email)
    return render_template("register.html", error_message="An error occured. Please try again or contact us")

"""
Route: signup
    This is the link which they will be taken to viw the confirmation email.
    It checks if the token they have used is valid and corresponds to the email.
"""
@app.route("/signup", methods=["GET"])
def signup():
    if request.method != "GET":
        return render_template("register.html")
    email = request.args.get('e')
    uri = request.args.get('t')
    if not r.good_token(email, uri):
        return render_template("register.html", error_message="Your token has expired or never existed. Please try again or contact us")
    return render_template("form.html", email_address=email)
    
@app.route("/registercomplete", methods=["POST", "GET"])
def completeRef():
    if request.method == "POST":
        email_address = request.form["email"]
        with open("used_emails", "r") as f:
            if any(line.strip() == email_address for line in f):
                return render_template("form.html", already_taken="You already have an account") 

        user_id = request.form["uid"]
        user_id_number = get_next_user_id_number()

        if not user_id_number:
            return render_template("form.html", error_message="Something went wrong. Please contact a Sys Admin.")

        password_string = "".join(random.choice(string.ascii_letters + string.ascii_digits) for _ in range(10))
        crypt_hashed_password = "{crypt}" + crypt.crypt(password_string)

        
        object_class = [
            "account",
            "top",
            "posixAccount",
            "mailAccount"
        ]
        attributes = {
            "cn" : user_id ,
            "gidNumber" : 422,
            "homeDirectory" : "/home/users/%s"%user_id,
            "mail" : "%s@netsoc.co"%user_id,
            "uid" : user_id,
            "uidNumber" : user_id_number, 
            "loginShell" : "/bin/bash",
            "userPassword" : crypt_hashed_password,
        }

        ldap_server = ldap3.Server("ldap.netsoc.co", get_info=ldap.ALL)
        with ldap.Connection(
                ldap_server,
                "cn=admin,dc=netsoc,dc=co",
                p.LDAP_KEY,
                auto_bind=True) as conn:
            if conn.search("cn=member,dc=netsoc,dc=co", "(objectClass=account)"):
                return render_template("form.html", already_taken="Username in use")

            success = conn.add(
                "cn=%s,cn=member,dc=netsoc,dc=co"%user_id, 
                object_class, 
                attributes)
            if success:
                with open("used_emails", "a") as f:
                    f.write(email_address + "\n")
                return render_template("some_other_page_to_tell_them_they_are_done")
            else:
                return render_template("form.html", error_message="Something went wrong. Please contact a Sys Admin.")

if __name__ == '__main__':
    app.run(host=HOST, port=int(PORT), debug=True)
