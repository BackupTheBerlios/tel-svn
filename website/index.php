<?php
	error_reporting(E_ALL);
	// include configuration
	include "config.php";

	// determinate the client's language
	$allowed_langs = array('en', 'de');
	if (isset($_GET["lang"])) {
		$lang = $_GET["lang"];
	}
	else {
		$lang = lang_getfrombrowser($allowed_langs, 'en', null, false);
	}
	
	include "header.php";

	// include content in the appropriate language
	if (isset($_GET['to'])) {
		$to = $_GET['to'];
		$error_file = "lang/".$lang."/"."error.php";
		if (isset($content[$to])) {
			$content_file = "lang/".$lang."/".$content[$_GET['to']];
			if (file_exists($content_file)) {
				include $content_file;
			}
			else {
				include $error_file;
			}
		}
		else {
			include $error_file;
		}
	}
	else
	{
		include "lang/".$lang."/"."home.php";
	}
	include "footer.php";
?>
