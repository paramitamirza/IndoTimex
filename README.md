# IndoTimex
Time expression extraction module, including time expression recognition and normalization, for Indonesian language, written in Python.

###Requirements
* Python 2.7 or higher
* [TimeNorm for Indonesian language](https://github.com/paramitamirza/timenorm-id) (.jar is provided in lib/)
 
###Usage
_! The input file(s) must be in [TimeML annotation format](http://www.timeml.org/site/index.html) !_
```
python python TimexExtraction.py dir_name [options]        or
python python TimexExtraction.py file_name [options]

options: -o output_dir_name/file_name (default: dir_path/dir_name_Timex/ for directory and file_path/file_name_timex.tml for file)
```   
The output file(s) will be a TimeML document annotated with time expressions (with the TIMEX3 tag).

###To convert TimeML file(s) to HTML for better viewing
```
python python convertToHTML.py dir_name [options]        or
python python convertToHTML.py file_name [options]

options: -o output_dir_name/file_name (default: dir_path/dir_name_HTML/ for directory and file_path/file_name.html for file)
```   
