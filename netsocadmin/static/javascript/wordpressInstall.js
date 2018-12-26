function installWordpress() {

	/*
	Disables the install button so that it doesnt carry out the installation twice.
	Reveals the progress bar. 
	Sends a HTTP GET reqeust to the server, telling it to install wordpress to the user's directory
	(Uses the /wordpressinstall API endpoint)
	Progress bar times out after 15 seconds and reveals 
	Changes text to be relevant during install and after install, so as to reveal wordpress link.
	*/

	document.getElementById("wordpress-install-button").style.display = "none";
	document.getElementById("wordpress-install-description").innerHTML = "Installing WordPress...";
	document.getElementById("wordpress-progress").style.display = "block";

	var request = new XMLHttpRequest()
	request.onreadystatechange = () => {
		if(request.readyState !== 4) return;
		document.getElementById("wordpress-progress").style.display = "none";
		document.getElementById("wordpress-install-description").style.display = "none";
		if(request.status === 200) {
			document.getElementById("wordpress-setup-link").style.display = "block";
			console.log("Wordpress install complete");
		} else {
			document.getElementById("wordpress-setup-fail").style.display = "block";
		}
	}
	request.open("GET", "/wordpressinstall");
	request.send();
}

