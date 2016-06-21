<?php
session_destroy();
ini_set('session.save_path',getcwd(). '/'. 'session/'); 
session_start();
#session_save_path('/home/ahk114/testing');
#session_start();
echo PHP_EOL;
echo 5+6;
echo PHP_EOL;
echo 100;
echo PHP_EOL;
session_destroy();
?>