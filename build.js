var sys = require('sys')
var exec = require('child_process').exec;
function puts(error, stdout, stderr) { sys.puts(stdout) }

var os = require('os');
//control OS
//then run command depengin on the OS

if (os.type() === 'Linux') 
   exec("mjml -l skip \"templates/templated_email/source/*.mjml\" -o templates/templated_email/compiled", puts); 
else if (os.type() === 'Darwin') 
   exec("mjml -l skip \"templates/templated_email/source/*.mjml\" -o templates/templated_email/compiled", puts); 
else if (os.type() === 'Windows_NT') 
   exec("md templates\\templated_email\\compiled\\ 2>NUL && for /F \"usebackq delims=\" %A in (`dir /b /s /a-d \"*.mjml\" ^| findstr /v partials ^| findstr /v shared ^| findstr /i templates`) do mjml %A -o templates\\templated_email\\compiled\\", puts);
else
   throw new Error("Unsupported OS found: " + os.type());