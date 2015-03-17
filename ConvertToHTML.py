import sys
import os
import re
import subprocess

class ConvertToHTML:
    def __init__(self, filepath):
        self.timeml = open(filepath, "r").read()

    def convertHTML(self):
        docid = re.findall(r"<%s>(.+?)<%s>" % ('DOCID','/DOCID'), self.timeml, re.DOTALL)[0]
        content = re.findall(r"<%s>(.+?)<%s>" % ('TEXT','/TEXT'), self.timeml, re.DOTALL)[0]
        title = re.findall(r"<%s>(.+?)<%s>" % ('TITLE','/TITLE'), self.timeml, re.DOTALL)[0]
        dct = re.findall(r"<DCT><TIMEX3.+?\"CREATION_TIME\">(.+?)</TIMEX3>", self.timeml, re.DOTALL)[0]  
        
        content = re.sub(r"\n", "</p><p>", content)
        content = re.sub(r"<TIMEX3 tid=\"(.+?)\" type=\"(.+?)\" value=\"(.+?)\">", r"<span title='\g<1>: \g<2>, \g<3>'>", content)
        content = re.sub(r"</TIMEX3>", r"</span>", content)
        
        html_text = "<html><style>body{padding:10px;font-size:12px;font-family:Tahoma,Arial,Helvetica,sans-serif;color:#333;}span{background-color:#ccebeb;cursor:pointer;}.content{float:left;width:100%;border:1px solid #ddd;padding:5px;}.sidebar{float:left;width:20%;border:1px solid #ddd;padding:5px;}a{color:#87b212;}a:hover{color:#0eae99;}li{padding:3px;}p{line-height:1.5;}</style><body>\n"
        html_text += "<div class='content'>"
        html_text += "<h3>" + title + "</h3>"
        html_text += "<h5>" + dct + "</h5>"
        html_text += "<p>" + content + "</p>"
        html_text += "</div>"
        html_text += "</body></html>"
        
        return html_text    

    def convertHTMLDir(self, filename):
        docid = re.findall(r"<%s>(.+?)<%s>" % ('DOCID','/DOCID'), self.timeml, re.DOTALL)[0]
        content = re.findall(r"<%s>(.+?)<%s>" % ('TEXT','/TEXT'), self.timeml, re.DOTALL)[0]
        title = re.findall(r"<%s>(.+?)<%s>" % ('TITLE','/TITLE'), self.timeml, re.DOTALL)[0]
        dct = re.findall(r"<DCT><TIMEX3.+?\"CREATION_TIME\">(.+?)</TIMEX3>", self.timeml, re.DOTALL)[0]  
        
        content = re.sub(r"\n", "</p><p>", content)
        content = re.sub(r"<TIMEX3 tid=\"(.+?)\" type=\"(.+?)\" value=\"(.+?)\">", r"<span title='\g<1>: \g<2>, \g<3>'>", content)
        content = re.sub(r"</TIMEX3>", r"</span>", content)
        
        filelist = open("filelist", "r")
        
        html_text = "<html><style>body{padding:10px;font-size:12px;font-family:Tahoma,Arial,Helvetica,sans-serif;color:#333;}span{background-color:#ccebeb;cursor:pointer;}.content{float:left;width:75%;border:1px solid #ddd;padding:5px;}.sidebar{float:left;width:20%;border:1px solid #ddd;padding:5px;}a{color:#87b212;}a:hover{color:#0eae99;}li{padding:3px;}p{line-height:1.5;}</style><body>\n"
        html_text += "<div class='content'>"
        html_text += "<h3>" + title + "</h3>"
        html_text += "<h5>" + dct + "</h5>"
        html_text += "<p>" + content + "</p>"
        html_text += "</div>"
        html_text += "<div class='sidebar'><ul>"
        for fname in filelist.readlines():
            if fname.strip() == filename:
                html_text += "<li><span>" + fname.strip() + "</span></li>"
            else:
                html_text += "<li><a href='" + fname.strip().replace(".tml", ".html") + "'>" + fname.strip() + "</a></li>"
        html_text += "</ul></div>"
        html_text += "</body></html>"
        
        filelist.close()
        
        return html_text
        
#check directory existence
def ensureDir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)
    
def printUsage():
    print "usage: python ConvertToHTML.py dir_name [options]"
    print "   or: python ConvertToHTML.py file_name [options]"
    print " "
    print "       options: -o output_dir_name/file_name (default: dir_path/dir_name_HTML/ for directory and file_path/file_name.html for file)"    
  
#main
if __name__ == '__main__':
    
    if len(sys.argv) < 2:
        printUsage()
    else:
        output = ""       
        if len(sys.argv) > 2:
            for i in range(2, len(sys.argv)):
                if sys.argv[i] == "-o":
                    if i+1 < len(sys.argv): output = sys.argv[i+1]

        if os.path.isdir(sys.argv[1]):  #input is directory name
            dirpath = sys.argv[1]
            if dirpath[-1] != "/": dirpath += "/"

            if output != "":
                output_dir_name = output
            else:
                output_dir_name = os.path.dirname(dirpath) + "_HTML/"

            if output_dir_name[-1] != "/": output_dir_name += "/"
            ensureDir(output_dir_name)
            
            total_timex_num = 0
            total_timex_fail = 0
            
            filelist = open("filelist", "w")
            for r, d, f in os.walk(dirpath):
                for filename in f:
                    #print filename
                    if filename.endswith(".tml"):
                        filepath = os.path.join(r, filename)
                        filelist.write(os.path.basename(filepath) + "\n")
            filelist.close()

            for r, d, f in os.walk(dirpath):
                for filename in f:
                    #print filename
                    if filename.endswith(".tml"):
                        filepath = os.path.join(r, filename)
                        print "Converting " + filepath + "..."
                        out_file = open(output_dir_name + os.path.basename(filepath.replace(".tml", ".html")), "w")
                        
                        conv = ConvertToHTML(filepath)
                        html_text = conv.convertHTMLDir(filename)
                        out_file.write(html_text)
                        out_file.close()
                        
            os.remove("filelist")

            print "HTML file(s) are saved in " + output_dir_name

        elif os.path.isfile(sys.argv[1]):   #input is file name
            print "Converting " + sys.argv[1] + "..."

            if output != "":
                out_file_name = output
            else:
                out_file_name = os.path.splitext(os.path.basename(sys.argv[1]))[0] + ".html"
            out_file = open(out_file_name, "w")

            conv = ConvertToHTML(sys.argv[1])
            html_text = conv.convertHTML()
            out_file.write(html_text)
            out_file.close()

            print "HTML file is saved in " + out_file_name

        else:
            print "File/directory " + sys.argv[1] + " doesn't exist."
