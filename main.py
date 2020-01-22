import uuid
import smtplib
import os
from dateutil import relativedelta
from basicauth import decode
from datetime import datetime, date, time, timedelta
from os import getenv
from google.cloud import bigquery
from google.cloud import storage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
client = bigquery.Client()



def exportdata(request):
    #secure the CF with basic auth.
    #This method should not be used for large scale production deployments only dev testing
    #For large scale production deployments use a method provided here:
    #https://cloud.google.com/functions/docs/securing/authenticating
    #There are other creative options such as Kong in GCP fronting it with service account rights to access
    #but I won't go into that here. 
	try:
		encoded_str = request.headers.get('Authorization')
		username, password = decode(encoded_str)
	except:
		print('No Auth')
		raise SystemExit
		
    #If you do use this method, please at list put this in an env var
	if username == 'randomstring' and password == 'anotherrandomstring':
		print('Authenticated')
	else:
		print('Not-Authenticated')
		raise SystemExit

	now = datetime.now()
    #Create a temp table in a data set that expires tables after a day
	dataset_id = 'log_temp'
    
    #These dates are merely here to create a month period of time to pull data from the date it's executed
	enddate = now.strftime("%Y-%m-%d")
	startdate_tmp = now+relativedelta(months=-1)
	startdate = startdate_tmp.strftime("%Y-%m-%d")
    #create a unique uuid to be used as the log name
	logid = str(uuid.uuid4())
	logid = logid.replace("-", "")

	job_config = bigquery.QueryJobConfig()
	# Set the destination table
	table_ref = client.dataset(dataset_id).table(logid)
	job_config.destination = table_ref
    #The BQ query
	sql = "SELECT timestamp,logdata1,logdata2,logdata3,logdata4 FROM `logging-systems.data_lake.logs_partitioned` WHERE DATE(timestamp) >= '" + startdate + "' and DATE(timestamp) < '" + enddate + "' and account_id = '45'"
	
	# Start the query, passing in the extra configuration.
	query_job = client.query(
	sql,
	# Location must match that of the dataset(s) referenced in the query
	# and of the destination table.
	location='US',
	job_config=job_config)  # API request - starts the query
    
	query_job.result()  # Waits for the query to finish
	print('Query results loaded to table {}'.format(table_ref.path))
    
	project = "log-systems"
	dataset_id = "log_temp"
	table_id = logid
    #create a bucket with a 48 hour Object Lifecycle Management expiration rule
    #the bucket name is best named after a domain so that you reference it in the url you will generate
	bucket_name = 'exports.domain.com'
	bucket_folder = 'logs'

	destination_uri = "gs://{}/logs/{}".format(bucket_name, logid + "*.csv")
	dataset_ref = client.dataset(dataset_id, project=project)
	table_ref = dataset_ref.table(table_id)

	extract_job = client.extract_table(
		table_ref,
    	destination_uri,
    	# Location must match that of the source table.
    	location="US",
	)  	# API request
	extract_job.result()  # Waits for job to complete.
        
	storage_client = storage.Client()
	bucket = storage_client.get_bucket(bucket_name)
	
	prefix="logs/" + logid
	blobs = bucket.list_blobs(prefix="logs/" + logid)
	
	link_html = ""
    
    #Search through your GCS objects and make the file public
	print('Blobs:')
	for blob in blobs:
		print(blob.name)
		blob.make_public()
		link_html = link_html + "\nhttps://exports.domain.com/" + blob.name

    #Set up the smtplib object that will be used
	server = smtplib.SMTP('smtp.sendgrid.net', 587)
	server.ehlo()
	server.starttls()

    # Sendgrid Sign In smtppswd - smtpusr
	sendgrid_sender = 'sendgrid_username'

    #Do not store this in your code
    #Use a CI/CD tool to pass this into an env variable when you update or create the cloud function
    #then pull the env variable into your code below
	sendgrid_passwd = os.environ.get('smtppswd', 'Specified environment variable is not set.')
	server.login(sendgrid_sender, sendgrid_passwd)

	me = 'from@noreply@fromdomain.com'
	to = ['mainemail@todomain.com']
	cc = ['email2@todomain.com','email3@todomain.com','email4@todomain.com']
	
	# Create message container - the correct MIME type is multipart/alternative.
	msg = MIMEMultipart('alternative')
	msg['Subject'] = 'SAMPLE REPORT: For the period of ' + startdate + ' until ' + enddate
	msg['From'] = me
	msg['To'] = ', '.join(to)
	msg['Cc'] = ', '.join(cc)
	toAddress = to + cc

	# Create the body of the message (a plain-text and an HTML version).
	text = 'Your Logs are ready and can be downloaded by clicking the link below:\nThey will be available for 48 hours.\n\n' + link_html + '\n\n\n\n\n'
	html = """\
    <html>
      <head></head>
      <body>
        <p>Your Logs are ready and can be downloaded by clicking the link below.<br>
           They will be available for 48 hours.<br><br>
           Download: <a href=""" + link_html + """>Call Report</a><br>
        </p>
      </body>
    </html>
    """

	# Record the MIME types of both parts - text/plain and text/html.
	part1 = MIMEText(text, 'plain')
	part2 = MIMEText(html, 'html')

	# Attach parts into message container.
	# According to RFC 2046, the last part of a multipart message, in this case
	# the HTML message, is best and preferred.
	msg.attach(part1)
	msg.attach(part2)



	# Send the message via local SMTP server.
	# s = smtplib.SMTP('localhost')
	# sendmail function takes 3 arguments: sender's address, recipient's address
	# and message to send - here it is sent as one string.
	server.sendmail(me, toAddress, msg.as_string())
	server.quit()
	# server.sendmail(gmail_sender, [TO], BODY)
	print ('email sent')
