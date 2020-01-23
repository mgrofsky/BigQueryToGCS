## Big Query to GCS
<hr>
<b>Description:</b>

I've been asked through various channels how to Query BigQuery programmatically in a Cloud Function, as well as how to save files in Google Cloud Storage for public consumption.

I wrote this Google Cloud Function to share some various aspects of how to combine those 2 worlds into a single function.

<b>This Python 3 script will:</b>

<ul>
	<li>Authenticate a request made to it via Basic Authentication.</li>
	<li>Execute a select statement in BigQuery for a date range covering the past month.</li>
	<li>Store the results into a CSV file located inside a Google Cloud Storage bucket.</li>
	<li>Modify that file or files into a publicly accessible url.</li>
	<li>Email the link or links to a specified list of email addresses.</li>
</ul>

<hr>

<b>Notes:</b>

This is by no means a definitive way to accomplish the tasks at hand.  Feel free to modify the script and provide a merge request for any changes you feel that could benefit someone else.

Ideally I would like to rewrite this so separate actions are put into their own functions and I did in my comments put in some notes on certain things that should be done differently if implemented in production.