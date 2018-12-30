function changeShell(e) {

	/*
	Disables the install button so that it doesnt carry out the installation twice.
	Reveals the progress bar. 
	Sends a HTTP POST reqeust to the server, telling it to change the shell for the user
	(Uses the /change-shell API endpoint)
    */
    e.preventDefault();
    var opts = document.querySelector("form select");
	var request = new XMLHttpRequest()
	request.onreadystatechange = () => {
		if(request.readyState !== 4) return;
		if(request.status === 200) {
			document.getElementById("shell-success").style.display = "block";
		} else {
            var el = document.getElementById("shell-error");
            el.style.display = "block";
            el.innerHTML = request.responseText;
		}
	}
	request.open("POST", `/change-shell?shell=${opts.options[opts.selectedIndex].value}`);
    request.send();
}

