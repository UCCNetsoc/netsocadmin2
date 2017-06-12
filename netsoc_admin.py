"""
This file contains the main program for netsoc admin.
Sets up a local server running the website. Requests should
then be proxied to this address.
"""
import string, random, crypt, re
from flask import Flask, request, render_template
import register_tools as r 

HOST = "127.0.0.1"
PORT = "5050"
app = Flask(__name__)

"""
Route: /
    This route is for the index directory.
    If the user goes to this, it will load the register.html template.
"""
@app.route('/')
def register():
    app.logger.debug("Received register page request")
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
        app.logger.debug("sendconfirmation(): method not POST: %s"%request.method)
        return render_template("register.html")
    # make sure is ucc email           
    email = request.form['email']         
    if not re.match(r"[0-9]{9}@umail\.ucc\.ie", email):
        app.logger.debug("sendconfirmation(): address %s is not a valid UCC email"%email)
        return render_template("register.html", error_message="Must be a UCC Umail email address")
    
    # make sure email has not already been used to make an account
    if False: #r.has_account(email):
        caption = "Sorry!"
        message = "There is an existing account with email '%s'. Please contact us if you think this is an error."%(email)
        app.logger.debug("senconfirmation(): account already exists with email %s"%(email))
        return render_template("message.html", caption=caption, message=message)
    # send confirmation link to endure they own the email account
    confirmation_sent = r.send_confirmation_email(email, "admin.netsoc.co")
    if not confirmation_sent:
        app.logger.debug("sendconfirmation(): confirmation email failed to send")
        return render_template("register.html", error_message="An error occured. Please try again or contact us")
    
    caption = "Thank you!"
    message = "Your confirmation link has been sent to %s"%(email)
    return render_template("message.html", caption=caption, message=message)
    
"""
Route: signup
    This is the link which they will be taken to with the confirmation email.
    It checks if the token they have used is valid and corresponds to the email.
"""
@app.route("/signup", methods=["GET"])
def signup():
    if request.method != "GET":
        app.logger.debug("signup(): method was not GET: %s"%request.method)
        return render_template("register.html")
    email = request.args.get('e')
    uri = request.args.get('t')
    if not r.good_token(email, uri):
        app.logger.debug("signup(): bad token %s used for email %s"%(uri, email))
        return render_template("register.html", error_message="Your request was not valid. Please try again or contact us")
    return render_template("form.html", email_address=email, token=uri)

"""
Route: register
    This is the route which is run by the registration form
    and should only be available through POST. It adds the
    given data to the Netsoc LDAP database.
"""
@app.route("/completeregistration", methods=["POST", "GET"])
def completeregistration():
    if request.method != "POST":
        app.logger.debug("completeregistration(): method was not POST: %s"%request.method)
        return render_template("register.html")

    email = request.form["email"]
    uri = request.form["_token"]

    # make sure token is valid
    if not r.good_token(email, uri, delete=True):
        app.logger.debug("completeregistration(): invalid token %s for email %s"%(uri, email))
        return render_template("register.html", error_message="Your token has expired or never existed. Please try again or contact us")

    # add user to ldap db
    user = request.form["uid"]
    success, reason, info = r.add_ldap_user(user)
    if not success:
        if reason:
            app.logger.debug("completeregistration(): %s"%reason)
            return render_template("form.html", email_address=email, token=uri, already_taken="Username is already in use")
        app.logger.debug("completeregistration(): failed to add user to LDAP")
        return render_template("register.html", error_message="An error occured. Please try again or contact us")
    
    # add all info to Netsoc MySQL DB
    info["name"] = request.form["name"]
    info["student_id"] = request.form["student_id"]
    info["course"] = request.form["course"]
    info["grad_year"] = request.form["graduation_year"]
    info["email"] = email
    app.logger.debug("info: %s"%(info))
    if not r.add_netsoc_database(info):
        app.logger.debug("completeregistration(): failed to add data to mysql db")
        return render_template("register.html", error_message="An error occured. Please try again or contact us")

    # send user's details to them
    if not r.send_details_email(email, user, info["password"]):
        app.logger.debug("completeregistration(): failed to send confirmation email")
        return render_template("register.html", error_message="An error occured. Please try again or contact us")

    caption = "Thank you!"
    message = "An email has been sent with your log-in details. Please change your password as soon as you log in."
    return render_template("message.html", caption=caption, message=message)

if __name__ == '__main__':
    app.run(
        host=HOST,
        port=int(PORT),
        threaded=True)