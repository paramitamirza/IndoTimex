import sys
import os
import re
import subprocess

class TimexExtraction:
    def __init__(self, filepath):
        self.timeml = open(filepath, "r").read()
    
    def __tokenize(self, text):
        text = text.replace("\x94", "\"")
        text = text.replace(",", " ,")
        text = text.replace(".", " .")
        text = text.replace("?", " ?")
        text = text.replace("!", " !")
        text = text.replace(";", " ;")
        text = text.replace(":", " :")
        text = text.replace("(", "( ")
        text = text.replace(")", " )")
        text = re.sub(r"\s\.(\d+)", r".\g<1>", text)
        text = re.sub(r"\s\,(\d+)", r",\g<1>", text)
        text = re.sub(r"(\d+)\s:", r"\g<1>:", text)
        text = re.sub(r":\s(\d+)", r":\g<1>", text)
        text = re.sub(r"\(\s(\d+)", r"(\g<1>", text)
        text = re.sub(r"(\d+)\s\)", r"\g<1>)", text)
        tokens = re.findall(r"[\w'\(-/:]+|[.,!?;\"\n]", text)
        return tokens

    def __getTokenLabel(self, token):
        regex_file = open("lib/timex_regex.txt", "r")
        regex_rules = regex_file.readlines()
        for rule in regex_rules:
            label = rule.split("=")[0].strip()
            regex = "^" + rule.split("=")[1].strip() + "$"
            pattern = re.compile("^" + regex + "$")
            if re.match(regex, token): return label
        regex_file.close()
        return "O"
        
    def __readTimexFST(self):
        fst_file = open("lib/fst/timex.fst", "r")
        init_state = 0
        transition = {}
        final_state = []
        for line in fst_file.readlines():
            cols = line.split()
            if len(cols) >= 4:  #transition
                state = int(cols[0])
                if state not in transition:
                    transition[state] = {}
                transition[state][cols[2]] = (int(cols[1]), cols[3])                
            elif len(cols) == 1:    #final state
                final_state.append(int(cols[0]))
        fst_file.close()
        return (init_state, transition, final_state)
        
    def __identifyTimex(self, tokens):
        (start_idx, end_idx, curr_state, timex_type) = (-1, -1, -1, "O")
        starts = {}
        ends = []
        timex = {}
        
        (init_state, transition, final_state) = self.__readTimexFST()  #read FST from file
        
        for i in range(len(tokens)-1):
            tok_curr = tokens[i]
            cat_curr = self.__getTokenLabel(tok_curr)
            #print tok_curr, cat_curr
            
            if start_idx == -1: #timex not yet started
                if cat_curr in transition[init_state]:
                    start_idx = i
                    (curr_state, timex_type) = transition[init_state][cat_curr]
            else:   #timex has started already
                if curr_state in transition and cat_curr in transition[curr_state]:
                    end_idx = i
                    (curr_state, timex_type) = transition[curr_state][cat_curr]
                elif curr_state in transition and tok_curr in transition[curr_state]:
                    end_idx = i
                    (curr_state, timex_type) = transition[curr_state][tok_curr]
                else:   
                    if curr_state in final_state:   #timex finished
                        if end_idx == -1: end_idx = start_idx
                        starts[start_idx] = timex_type
                        ends.append(end_idx)
                        timex[start_idx] = tokens[start_idx:end_idx+1]
                    (start_idx, end_idx, curr_state, timex_type) = (-1, -1, -1, "O")
                    
        return (starts, ends, timex)
        
    def __normalizeTimex(self, starts, timex, dct):
        normalized = {}
        timex_num = 0
        timex_fail = 0
        temp_file = open("temp", "w")
        for start in timex:
            timex_num += 1
            temp_file.write(str(start) + "\t" + " ".join(timex[start]) + "\t" + starts[start] + "\t" + dct + "\n")
        temp_file.close()
        with open("log", 'w') as logfile:
            command = "java -jar lib/timenorm-id-0.9.2-jar-with-dependencies.jar lib/id.grammar temp"
            subprocess.call(command.split(" "), stderr=logfile)
        norm_file = open("temp_normalized", "r")
        fail_file = open("fail_normalized", "a")
        for line in norm_file.readlines():
            cols = line.strip().split("\t")
            normalized[int(cols[0])] = cols[3]
            if cols[3] == "FAIL":
                fail_file.write(cols[1] + "\t" + cols[2] + "\t" + cols[3] + "\n")
                timex_fail += 1
        norm_file.close()
        fail_file.close()
        os.remove("temp")
        os.remove("temp_normalized")
        return (normalized, timex_num, timex_fail)
        
    def __timexTagging(self, tokens, starts, ends, normalized):
        timex_text = ""
        tmx_id = 1
        for i in range(len(tokens)-1):
            if i in starts and i in ends: 
                timex_text += "<TIMEX3 tid=\"t"+str(tmx_id)+"\" type=\""+starts[i]+"\""
                if normalized[i] != "FAIL": timex_text += " value=\""+normalized[i]+"\""                
                else: timex_text += " value=\"UNKNOWN\""
                timex_text += ">" + tokens[i] + "</TIMEX3> "
                tmx_id += 1
            else:
                if i in starts: 
                    timex_text += "<TIMEX3 tid=\"t"+str(tmx_id)+"\" type=\""+starts[i]+"\""
                    if normalized[i] != "FAIL": timex_text += " value=\""+normalized[i]+"\""
                    else: timex_text += " value=\"UNKNOWN\""
                    timex_text += ">" + tokens[i] + " "
                    tmx_id += 1
                elif i in ends:
                    timex_text += tokens[i] + "</TIMEX3> "
                elif re.match(r"\n", tokens[i]): timex_text += tokens[i]
                else: timex_text += tokens[i] + " "
        
        timex_text = timex_text.replace(" ,", ",")
        timex_text = timex_text.replace(" .", ".")
        timex_text = timex_text.replace(" ?", "?")
        timex_text = timex_text.replace(" !", "!")
        timex_text = timex_text.replace(" ;", ";")
        timex_text = timex_text.replace(" :", ":")
        timex_text = timex_text.replace("( ", "(")
        timex_text = timex_text.replace(" )", ")")
        return timex_text
        
    def extractTimex(self):
        content = re.findall(r"<%s>(.+?)<%s>" % ('TEXT','/TEXT'), self.timeml, re.DOTALL)[0]
        dct = re.findall(r"<DCT><TIMEX3.+?value=\"(.+?)\"", self.timeml, re.DOTALL)[0]
        
        #tokenize content
        tokens = self.__tokenize(content)
        num_tokens = len(tokens)
        
        #timex extent recognition
        (starts, ends, timex) = self.__identifyTimex(tokens)
            
        #timex normalization
        (normalized, timex_num, timex_fail) = self.__normalizeTimex(starts, timex, dct)
        
        #TIMEX3 tagging
        timeml_timex = self.__timexTagging(tokens, starts, ends, normalized)
        
        #TimeML string    
        header = re.findall(r"(.+?)<TEXT>", self.timeml, re.DOTALL)[0]
        timeml_out = header + "<TEXT>" + timeml_timex + "\n</TEXT>\n\n</TimeML>"
        
        return (timeml_out, timex_num, timex_fail, num_tokens)
    
#check directory existence
def ensureDir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)
    
def printUsage():
    print "usage: python TimexExtraction.py dir_name [options]"
    print "   or: python TimexExtraction.py file_name [options]"
    print " "
    print "       options: -o output_dir_name/file_name (default: dir_path/dir_name_Timex/ for directory and file_path/file_name_timex.tml for file)"
        
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
            output_dir_name = os.path.dirname(dirpath) + "_Timex/"

        if output_dir_name[-1] != "/": output_dir_name += "/"
        ensureDir(output_dir_name)
        
        total_timex_num = 0
        total_timex_fail = 0
        total_words = 0
        
        for r, d, f in os.walk(dirpath):
            for filename in f:
                #print filename
                if filename.endswith(".tml"):
                    filepath = os.path.join(r, filename)
                    print "Extracting from " + filepath + "..."
                    out_file = open(output_dir_name + os.path.basename(filepath), "w")
                    
                    te = TimexExtraction(filepath)
                    (timeml_out, timex_num, timex_fail, num_tokens) = te.extractTimex()
                    out_file.write(timeml_out)
                    out_file.close()
                    
                    total_timex_num += timex_num
                    total_timex_fail += timex_fail
                    total_words += num_tokens
                    
        print "TimeML file(s) are saved in " + output_dir_name
        fail = total_timex_fail*100/float(total_timex_num)
        print "Total number of words is " + str(total_words)
        print "Total number of timex is " + str(total_timex_num) + " , with " + str(total_timex_fail) + "(" + "%.2f" % fail + "%) are failed to be normalized."

    elif os.path.isfile(sys.argv[1]):   #input is file name
        print "Extracting from " + sys.argv[1] + "..."

        if output != "":
            out_file_name = output
        else:
            out_file_name = os.path.splitext(os.path.basename(sys.argv[1]))[0] + "_timex.tml"
        out_file = open(out_file_name, "w")

        te = TimexExtraction(sys.argv[1])
        (timeml_out, timex_num, timex_fail, num_tokens) = te.extractTimex()
        out_file.write(timeml_out)
        out_file.close()

        print "TimeML file is saved in " + out_file_name
        fail = timex_fail*100/float(timex_num)
        print "Total number of timex is " + str(timex_num) + " , with " + str(timex_fail) + "(" + "%.2f" % fail + "%) are failed to be normalized."

    else:
        print "File/directory " + sys.argv[1] + " doesn't exist."