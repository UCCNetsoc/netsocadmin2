function sendGET(endpoint) {
	/* A generic method used to send a HTTP GET request for asynchronous querying */

	var http = new XMLHttpRequest();
    http.open("GET", endpoint);
    http.timeout = 30000;
    http.send()
    return http.responseText;
}

function installWordpress() {

	/*
	Disables the install button so that it doesnt carry out the installation twice.
	Reveals the progress bar. 
	Sends a HTTP GET reqeust to the server, telling it to install wordpress to the user's directory
	(Uses the /wordpressinstall API endpoint)
	Progress bar times out after 15 seconds and reveals 
	Changes text to be relevant during install and after install, so as to reveal wordpress link.
	*/

	var timeout_duration = 15000; // 15 seconds

	document.getElementById("wordpress-install-button").style.display = "none";
	document.getElementById("wordpress-install-description").innerHTML = "Installing WordPress...";
	document.getElementById("wordpress-progress").style.display = "block";

	sendGET("/wordpressinstall");
	setTimeout(function() {
		document.getElementById("wordpress-progress").style.display = "none";
		document.getElementById("wordpress-install-description").style.display = "none";
		document.getElementById("wordpress-setup-link").style.display = "block";
		console.log("Wordpress install complete");
	}, timeout_duration);
}

