<?php
// get the browse language
function lang_getfrombrowser ($allowed_languages, $default_language, $lang_variable = null, $strict_mode = true) {
        // use server language, if no information was given
        if ($lang_variable === null) {
                $lang_variable = $_SERVER['HTTP_ACCEPT_LANGUAGE'];
        }

        if (empty($lang_variable)) {
                // return default language if no information was given
                return $default_language;
        }

        $accepted_languages = preg_split('/,\s*/', $lang_variable);

        // define default values
        $current_lang = $default_language;
        $current_q = 0;

        // iterate over all languages
        foreach ($accepted_languages as $accepted_language) {
                // get all information about the language
                $res = preg_match ('/^([a-z]{1,8}(?:-[a-z]{1,8})*)'.
                                   '(?:;\s*q=(0(?:\.[0-9]{1,3})?|1(?:\.0{1,3})?))?$/i', $accepted_language, $matches);

                // valid syntax? war die Syntax gltig?
                if (!$res) {
                        // No? then ignore it
                        continue;
                }
                
                // get the the lang code and split it immediatly
                $lang_code = explode ('-', $matches[1]);

                // quality given?
                if (isset($matches[2])) {
                        // use it
                        $lang_quality = (float)$matches[2];
                } else {
                        // compatibility mode: assume quality 1
                        $lang_quality = 1.0;
                }

                // until there is no code left
                while (count ($lang_code)) {
                        // is the language allowed?
                        if (in_array (strtolower (join ('-', $lang_code)), $allowed_languages)) {
                                // look at the quality 
                                if ($lang_quality > $current_q) {
                                        // use this language and ...
                                        $current_lang = strtolower (join ('-', $lang_code));
                                        $current_q = $lang_quality;
                                        // ... leave the inner loop
                                        break;
                                }
                        }
                        // If we're in strict mode, do _not_ try to minimize the language
                        if ($strict_mode) {
                                break;
                        }
                        // chop off the most right part of the language code
                        array_pop ($lang_code);
                }
        }

        // at last, we can return the current language
        return $current_lang;
}
?>
