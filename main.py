import argparse
import sys
from urllib.parse import urlparse
import requests # type: ignore
import threading
import queue
import random 
def print_header():
    print(""" ______   ___   _______  _______  _______  __   __  _______  ______   
|      | |   | |       ||       ||  _    ||  | |  ||       ||    _ |  
|  _    ||   | |  _____||       || | |   ||  |_|  ||    ___||   | ||  
| | |   ||   | | |_____ |       || | |   ||       ||   |___ |   |_||_ 
| |_|   ||   | |_____  ||      _|| |_|   ||       ||    ___||    __  |
|       ||   |  _____| ||     |_ |       | |     | |   |___ |   |  | |
|______| |___| |_______||_______||_______|  |___|  |_______||___|  |_|
""")

def command_line_arguments():
    parser = argparse.ArgumentParser(
                    prog='disc0ver',
                    description='Directory Enumeration Tool',
                    epilog='Text at the bottom of help')

    parser.add_argument('URL')           # psitional argument
    parser.add_argument('-w', '--wordlist')      # option that takes a value
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-r','--recursion',action='store_true')
    parser.add_argument('--redirect',action='store_true')
    parser.add_argument('-p','--proxies',help="Text file containing proxies (.txt)") #takes in a proxy list in .txt format
    parser.add_argument('-fs','--filter-size',nargs='+',type=int,help="Reponses of certain sizes you do not want to see.")
    parser.add_argument('-fc','--filter-code',nargs='+',type=int,help="Response codes you do not want to see.")
    parser.add_argument('-t','--threads',type=int,default=10,help="Amount of threads used in sending requests, default: 10")
    parser.add_argument('-o',"--outfile",help="Output file")
    
    args = parser.parse_args()

    return args

def print_args(args):
    print("\n")
    print('URL: '+ str(args.URL))
    print('Wordlist: '+ str(args.wordlist))
    print('Thread Count: '+str(args.threads))
    print('Size Filters: ' + ', '.join(map(str, args.filter_size)) if args.filter_size is not None else 'Size Filters: None')
    print('Response Code Filters: ' + ', '.join(map(str, args.filter_code)) if args.filter_code is not None else 'Response Code Filters: None')
    print("--------------------------------------------------")



def import_wordlist(text_file):
    wordlist = []
    with open(text_file, 'r') as file:
        wordlist = file.read().splitlines()
    return wordlist

args = command_line_arguments()
wordlist = import_wordlist(args.wordlist)


word_queue = queue.Queue()
for word in wordlist:
    word_queue.put(word)

lock = threading.Lock()

### https://stackoverflow.com/questions/5419389/how-to-overwrite-the-previous-print-to-stdout
class Printer:
    '''
    Clears the previous line and prints the next.
    '''

    max_length: int = 0

    def print_replace(self, nextline):
        '''replace the previous line'''
        print(f'{nextline}  {" " * max(0, self.max_length - len(nextline))}', end='\r')
        self.max_length = max(self.max_length, len(nextline))

    def print_new(self, nextline):
        '''adds to the print stream'''
        print(f'{nextline}  {" " * max(0, self.max_length - len(nextline))}')
        self.max_length = max(self.max_length, len(nextline))
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def send_request(url):#add try - except
    response = requests.get(url)
    return response


def enumeration(address,args):

    if args.proxies is not None:
        proxy_list = import_wordlist("valid_proxies.txt")
        proxies = {"http": random.choice(proxy_list), "https": random.choice(proxy_list)} if args.proxy else None
    else:
        proxies = None
    output_content = True
    printer = Printer()

    while not word_queue.empty():
        try:
            word = word_queue.get(timeout=1)  # Get a word from the queue
        except queue.Empty:
            break
        
        # Test the word (replace with actual URL and HTTP request logic)
        url = f"{address}/{word}"

        try:
            response = requests.get(url, allow_redirects=args.redirect, proxies=proxies)
        except:
            continue


        
        #Filters
        if args.filter_size is not None and args.filter_size == len(response.content):
            output_content= False
        if args.filter_code and response.status_code in args.filter_code:
            output_content = False
            
        if output_content == True and response.status_code == 200 and response.history:
            # Get the final redirect location from the last response in the history
            final_redirect = response.history[-1].headers.get('Location', 'Unknown')
            if "http" not in final_redirect:
                final_redirect = final_redirect.replace("/", "")
            else:
                parsed_url = urlparse(url)
                path_parts = parsed_url.path.split('/')
                desired_word = path_parts[-1] if path_parts[-1] else path_parts[-2]  # Handle trailing slash case

                if url in final_redirect:
                    final_redirect = desired_word
            if word == final_redirect.replace("/",""):
                printer.print_new(f"{bcolors.OKGREEN}{word}: {response.status_code} Size: {len(response.content)}{bcolors.ENDC}")
                output_to_outfile(word,response,False,None)
            else:
                printer.print_new(f"{bcolors.OKCYAN}{word}: 301 --> {final_redirect} Size: {len(response.content)}{bcolors.ENDC}")
                output_to_outfile(word,response,True,final_redirect)    
                
        elif output_content == True and response.status_code == 200:
            printer.print_new(f"{bcolors.OKGREEN}{word}: {response.status_code} Size: {len(response.content)}{bcolors.ENDC}")
            output_to_outfile(word,response,False,None)
       
        elif output_content == True and (response.status_code == 404 or response.status_code == 403):
            printer.print_replace(f"{bcolors.RED}{word}: {response.status_code} Size: {len(response.content)}{bcolors.ENDC}")
       
        elif output_content == True and response.status_code in [301, 302]:
            redirect_location = response.headers.get('Location', 'Unknown')
            printer.print_replace(f"{bcolors.OKCYAN}{word}: {response.status_code} -->  {redirect_location} Size: {len(response.content)}{bcolors.ENDC}")
            if args.redirect:
                output_to_outfile(word,response,True,None)

        elif output_content == True and response.status_code != 200:
            printer.print_replace(f"{bcolors.YELLOW}{word}: {response.status_code} Size: {len(response.content)}{bcolors.ENDC}")
        


        if response.status_code == 200:
            # Use lock to safely add recursive tasks
            with lock:
                for subword in wordlist:
                    if final_redirect in url:
                        continue
                    else: 
                        new_word = f"{final_redirect}/{subword}" 
                        word_queue.put(new_word)  # Add new word to the queue

            


        word_queue.task_done()

def output_to_outfile(word,response,redirect,final_redirect):
    with open(args.outfile,'a') as file:
            if redirect:
                file.write(f"{word}: 301 --> {final_redirect} Size: {len(response.content)}\n")     
            else:
                file.write(f"{word}: {response.status_code} Size: {len(response.content)}\n")      


def main():
    args = command_line_arguments()
    print_header()
    print_args(args)
    

    #enumeration(args.wordlist,args.URL,args.recursion)
    wordlist = import_wordlist(args.wordlist)
  

    num_threads = args.threads
    threads = []
    for i in range(num_threads):
        t = threading.Thread(target=enumeration,args=(args.URL,args,))
        t.start()
        threads.append(t)

    # Wait for all threads to finish
    for t in threads:
        t.join()

    #request = send_request(args.URL)
    #import_wordlist(args.wordlist)

    

    
    

if __name__ == '__main__':
    main()