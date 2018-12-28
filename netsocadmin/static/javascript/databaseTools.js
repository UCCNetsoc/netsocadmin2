let originalTitle, originalButtonText;
$(document).ready(() => {
	originalTitle = document.querySelector("#database-form-title").innerText;
	originalButtonText = document.querySelector("#database-form-button-text").innerText;
	originalAction = document.querySelector("#database-change-form form").action;
})

// switches between the create database and delete database forms. If the database name db
// is specified, then it will pick the delete database form. Otherwise, it will pick the
// create database form.
function databaseForm(db) {
	const formTitle = document.querySelector("#database-form-title");
	const formButton = document.querySelector("#database-form-button-text");
	const form = document.querySelector("#database-change-form form");
	const dbnameInput = document.querySelector("#dbname");

	if (db) {
		form.action = "/deletedb";
		formTitle.innerText = "Delete Database:";
		formButton.innerText = "Remove";
		dbnameInput.value = db;
		Materialize.updateTextFields();
	} else {
		form.action = originalAction;
		formTitle.innerText = originalTitle;
		formButton.innerText = originalButtonText;
		dbnameInput.value = "";
		Materialize.updateTextFields();
	}
}

// replaces the database changing form. If resetCard is true, then it changes it back
function passwordReset(resetCard) {
	const formChange = document.querySelector("#database-change-form");
	const formReset = document.querySelector("#password-reset-form");
	if (!resetCard) {
		formReset.style.display = "block";
		formChange.style.display = "none";
	} else {
		formReset.style.display = "none";
		formChange.style.display = "block";
	}
}