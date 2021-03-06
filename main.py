import os
from flask import Flask, Response, request, send_file, session, jsonify, redirect
import requests

import Login
import Job
import Register
import Account
import Admin

app = Flask(__name__, static_url_path='/static', static_folder="static")
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

def addDefaultParameters(parameters):
	default_parameters = {
		"sim_type":"MD",
		"max_density_multiplier":10,
		"verlet_skin":0.5,
		"time_scale":"linear",
		"ensemble":"NVT",
		"thermostat":"john",
		"dt":"0.001",
		"diff_coeff":2.5,
		"backend_precision":"double",
		"lastconf_file":"last_conf.dat",
		"trajectory_file":"trajectory.dat",
		"energy_file":"energy.dat",
		"refresh_vel":1,
		"restart_step_counter":1
	}

	for (key, value) in default_parameters.items():
		if key not in parameters:
			parameters[key] = default_parameters[key]

@app.route('/create_job', methods=['POST'])
def handle_form():

	if session.get("user_id") is None:
		return "You must be logged in to submit a job!"

	user_id = session["user_id"]
	print("Now creating a job on behalf of:", user_id)

	json_data = request.get_json()

	parameters = {}

	for (file_name, _) in json_data["files"].items():
		if(".top" in file_name):
			parameters.update({"topology": file_name})
		if(".dat" in file_name or ".conf" in file_name or ".oxdna" in file_name):
			parameters.update({"conf_file": file_name})

	parameters.update(json_data["parameters"])
	files = json_data["files"]

	addDefaultParameters(parameters)

	metadata = {}

	job_data = {
		"metadata":metadata,
		"parameters": parameters, 
		"files": files
	}

	success, error_message = Job.createJobForUserIdWithData(user_id, job_data)

	if success:
		return "Success"
	else:
		return error_message

@app.route('/cancel_job', methods=['POST'])
def cancel_job():
	print("Received Cancel Request")
	if session.get("user_id") is None:
		return "You must be logged in to cancel this job!"

	json_data = request.get_json()
	jobId = json_data["jobId"]
	print("Canceling Job " + jobId)
	Job.cancelJob(jobId)
	return "Canceled Job " + jobId

@app.route('/delete_job', methods=['POST'])
def delete_job():
	print("Received Delete Request")
	if session.get("user_id") is None:
		return "You must be logged in to delete this job!"

	json_data = request.get_json()
	job_uuid = json_data["jobId"]
	print("Deleting Job " + job_uuid)
	Job.deleteJob(job_uuid)
	return "Deleted Job " + job_uuid

@app.route('/job_status/<jobId>', methods=['GET'])
def job_status(jobId):
	status = Job.getJobStatus(jobId)
	return status


@app.route('/api/create_analysis/<jobId>', methods=['POST'])
def create_analysis(jobId):

	print("QUERIED!")

	if session.get("user_id") is None:
		return "You must be logged in to submit a job!"

	userId = session["user_id"]
	print("Now creating a analysis on behalf of:", userId, " and for job id:", jobId)

	'''
	json_data = request.get_json()

	parameters = json_data["parameters"]
	files = json_data["files"]

	addDefaultParameters(parameters)

	metadata = {}

	job_data = {
		"metadata":metadata,
		"parameters": parameters, 
		"files": files
	}

	Job.createJobForUserIdWithData(user_id, job_data)'''

	return Job.createAnalysisForUserIdWithJob(userId, jobId)

	#return "Analysis created!"
@app.route("/verify", methods = ["GET"])
def verify():
	#TODO refactor to use exceptions
	if (request.method == "GET"):
		#Two files to choose from based on html query strings
		#Success
		#Failure
		#Expecting two query strings, user id, and autogenerated verification code
		if (request.args):
			#get query strings
			args = request.args
			userId = args.get("id")
			code = args.get("verify")
			#check if query strings are present
			if (userId and code):
				#verify the user
				if(Account.verifyUser(userId, code)):
					return send_file("templates/verify/success.html")
				else:
					return send_file("templates/verify/fail.html")
			else:
				return send_file("templates/verify/fail.html")
		else:
			return send_file("templates/verify/fail.html")

@app.route("/register", methods=["GET", "POST"])
def register():

	if request.method == "GET":
		return send_file("templates/register.html")

	if request.method == "POST":
		username = request.form["username"]
		password = request.form["password"]
		firstName = request.form["firstName"]
		lastName = request.form["lastName"]
		institution = request.form["institution"]

	if username[-4:] != ".edu":
		 return "We are currently only accepting .edu registrations at this time."

	if username is not None and password is not None:
		user_id = Register.registerUser(username, password, firstName, lastName, institution)

		if(user_id > -1):
			#session["user_id"] = user_id
			return redirect("/login")
		elif(user_id == -2):
			return "Username already taken"
		else:
			return "Invalid username or password"

	return "Invalid username or password"


@app.route("/login", methods=["GET", "POST"])
def login():

	if request.method == "GET":
		return send_file("templates/login.html")

	if request.method == "POST":
		username = request.form["username"]
		password = request.form["password"]
	if username is not None and password is not None:
		user_id = Login.loginUser(username, password)
		if(user_id > -1):
			session["user_id"] = user_id
			return redirect("/")
		elif(user_id == -2):
			return "Error, user not verified. Please verify using the link sent to the email you registered with."
		else:
			return "Invalid username or password"
		
	return "Invalid username or password"

@app.route("/logout")
def logout():
	session["user_id"] = None
	return "You have logged out"


@app.route("/account", methods=["GET"])
def account():

	if session.get("user_id") is None:
		return "You must be logged in to modify your account"

	if request.method == "GET":
		return send_file("templates/account.html")

@app.route("/account/update_password", methods=["POST"])
def updatePassword():
	if session.get("user_id") is None:
		return "You must be logged in to modify your account"

	user_id = int(session["user_id"])

	old_password = request.json["old_password"]
	new_password = request.json["new_password"]

	return Login.updatePasssword(user_id, old_password, new_password)

@app.route("/account/get_email", methods=["GET"])
def getEmail():
	if session.get("user_id") is None:
		return "You must be logged in to modify your account"

	user_id = int(session["user_id"])
	
	return Account.getEmail(user_id)

@app.route("/account/set_email", methods=["POST"])
def updateEmail():
	if session.get("user_id") is None:
		return "You must be logged in to modify your account"

	user_id = int(session["user_id"])
	email_new = string(session["email"])
	
	return Account.setEmail(user_id, email_new)

@app.route("/account/get_status", methods=["GET"])
def getStatus():
	if session.get("user_id") is None:
		return "You must be logged in to modify your account"

	user_id = int(session["user_id"])
	
	return Account.getStatus(user_id)

@app.route("/account/get_creation_date", methods=["GET"])
def getCreationDate():
	if session.get("user_id") is None:
		return "You must be logged in to modify your account"

	user_id = int(session["user_id"])
	
	return Account.get_creation_date(user_id)

@app.route("/jobs")
def jobs():

	if session.get("user_id") is None:
		return redirect("/login")
	else:
		return send_file("templates/jobs.html")

@app.route("/job/<job_id>")
def view_job(job_id):

	if session.get("user_id") is None:
		return redirect("/login")
	else:
		return send_file("templates/job.html")


@app.route("/api/job/<job_id>")
def get_job_data(job_id):

	if session.get("user_id") is None:
		return redirect("/login")

	job_data = Job.getJobForUserId(job_id, session.get("user_id"))

	if(job_data is not None):
		return jsonify(job_data)
	else:
		return "No job data."



@app.route("/all_jobs")
def getJobs():

	if session.get("user_id") is None:
		return "You must be logged in to view your jobs"

	user_id = int(session["user_id"])

	jobs = Job.getJobsForUserId(user_id)

	return jsonify(jobs)


@app.route("/job_output/<uuid>/<desired_output>")
def getJobOutput(uuid, desired_output):

	if session.get("user_id") is None:
		return "You must be logged in to view the output of a job"

	desired_output_map = {
		"energy":"energy.dat",
		"trajectory":"trajectory.dat",
                "topology": "output.top",
		"log":"job_out.log",
		"analysis_log":"analysis_out.log",
		"input":"input",
		"mean":"mean.dat",
		"deviations":"deviations.json"
	}

	if desired_output not in desired_output_map:
		return "You must specify a valid desired output"
	

	user_directory = "/users/" + str(session["user_id"]) + "/"
	job_directory =  user_directory + uuid + "/"
	desired_file_path = job_directory + desired_output_map[desired_output]

	desired_file = open(desired_file_path, "r")




	desired_file_contents = desired_file.read()

	return Response(desired_file_contents, mimetype='text/plain')

@app.route("/admin")
def admin():
	userID = session.get("user_id")
	isAdmin = Admin.checkIfAdmin(userID)
	if isAdmin == 1:
		return send_file("templates/admin.html")
	else:
		return "You must be an admin to access this page."

@app.route("/admin/recentlyaddedusers")
def recentlyAddedUsers():
	newUsers = Admin.getRecentlyAddedUsers()
	users = tuple(newUsers)
	return jsonify(users)

@app.route("/admin/promoteToAdmin/<username>")
def promoteToAdmin(username):
	loggedInUserID = session.get("user_id")
	isAdmin = Admin.checkIfAdmin(loggedInUserID)
	if isAdmin == 1:
		userID = Admin.getID(username)
		Admin.promoteToAdmin(userID)
		return username + " promoted to Admin"

@app.route("/admin/promoteToPrivaleged/<username>")
def promoteToPrivaleged(username):
	loggedInUserID = session.get("user_id")
	isAdmin = Admin.checkIfAdmin(loggedInUserID)
	if isAdmin == 1:
		userID = Admin.getID(username)
		Admin.promoteToPrivaleged(userID)
		return username + " promoted to privaleged"

@app.route("/admin/getUserID/<username>")
def getUserID(username):
	userID = Admin.getID(username)
	return jsonify(userID)


@app.route("/admin/getUserInfo/<username>")
def getUserInfo(username):
	userID = Admin.getID(username)
	#jobCount = Admin.getUserJobCount(uuid)
	isAdmin = Admin.checkIfAdmin(userID)
	if isAdmin == 1:
		isAdmin = "True"
	else:
		isAdmin = "False"
	isPrivaleged = Admin.checkIfPrivaleged(userID)
	if isPrivaleged == 1:
		isPrivaleged = "True"
	else:
		isPrivaleged = "False"
	jobCount = Admin.getUserJobCount(userID)
	info = (jobCount, isAdmin, isPrivaleged)
	return jsonify(info)

@app.route("/")
def index():

	if session.get("user_id") is not None:
		return send_file("templates/index.html")
	else:
		return redirect("/login")

app.run(host="0.0.0.0", port=9000)
