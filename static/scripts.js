$(function(){

	//submit registration form if it valid
	$("#sbm-rg").on("click", function() {
		obj = $("#registrating");
		if (obj.validationEngine('validate')) { //form validation
			obj.submit();
		}
	});

	//submit personal form if it valid
	$("#save-pers").on("click", function() {
		obj = $("#personal");
		if (obj.validationEngine('validate')) {
			obj.submit();
		}
	});

	//send from contacts if it valid
	$("#askBtn").on("click", function() {
		obj = $("#askform");
		if (obj.validationEngine('validate')) {
			obj.submit();
		}
	});

	//ask user: are you sure you want to remove your account?
	$("#remove-page").click(function() {
		$("html").prepend('<div class="askin"></div><div class="ask-block"><sapn class="ask-quest">Вы уверены что хотите удалить вашу страницу?</sapn><button class="yes">Удалить</button><button class="no">Не удалять</button></div>');
	});

	//close window with question(remove account)
	$("html").on("click", ".askin, .no", function() {
		$(".askin, .ask-block").remove();
	});

	//remove user account
	$("html").on("click", ".yes", function() {
		$.ajax({
			url: "removePage",
			type: "POST",
			success: function(data, cmp) {
				if (cmp == "success" && data == "") {
					window.location.href = "/";
				}
			}
		});
	});

	//user authorization
	$(".log-in").click(function() {
		elem = $(this);
		obj = {
			log_in: $(".login").val(), 
			password: $(".password").val()
		}
		$.post("log_in", obj, function(data, cmp) {
			if(cmp == 'success'){
				if (data == "OK") {
					document.location.href = "/";
				} else {
					if ($(".message").length == 0) { 
						elem.after('<div class="message">'+data+'</a></div>');
						setTimeout(function() {$(".message").remove();}, 3000);
					}
				}
			}
		});
	});
});