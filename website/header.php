<?php
    header('content-type: text/html; charset=utf-8');
    echo '<?xml version="1.0" encoding="UTF-8"?>'."\n";

	// determinate the client's language
	$allowed_langs = array('en', 'de');
	if (isset($_GET["lang"])) {
		$lang = $_GET["lang"];
	}
	else {
		$lang = lang_getfrombrowser($allowed_langs, 'en', null, false);
	}	
?>

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="de">
<head>
<title>tel</title>
<link title="Green" rel="stylesheet" type="text/css" href="green.css"></link>
<link title="Blue" rel="alternate stylesheet" type="text/css" href="blue.css"></link>

</head>

<body>

<div id="container">
	<div id="header">
		<div style="float: left;">
			<a href="http://developer.berlios.de"><img src="http://developer.berlios.de/bslogo.php?group_id=8132" alt="BerliOS.de" /></a>
		</div>

		<div id="banner">
			<a href="index.php"><img class="banner" src="images/logo_new_rc1.png" alt="tel logo" style="border:none;"/></a><br />
            <? include("lang/".$lang."/slogan.php"); ?>
		</div>
	</div>
	
	<div id="ihv">
        <? include "lang/".$lang."/ihv.php"; ?>
	</div>

	<div id="index">
