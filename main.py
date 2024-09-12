import argparse
import sys
import requests # type: ignore
import threading
import queue


def command_line_arguments():
    parser = argparse.ArgumentParser(
                    prog='disc0ver',
                    description='Directory Enumeration Tool',
                    epilog='Text at the bottom of help')

    parser.add_argument('URL')           # psitional argument
    parser.add_argument('-w', '--wordlist')      # option that takes a value
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-r','--recursion',action='store_true')
    
    args = parser.parse_args()

    return args

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




def send_request(url):#add try - except
    response = requests.get(url)
    return response



def enumeration():
     while not word_queue.empty():
        try:
            word = word_queue.get(timeout=1)  # Get a word from the queue
        except queue.Empty:
            break
        
        # Test the word (replace with actual URL and HTTP request logic)
        url = f"https://google.com/{word}"
        response = requests.get(url)
        
        print(f"Thread {threading.current_thread().name} tested {word}: {response.status_code}")
        
        # If 200, consider this a valid path and test for recursive paths
        if response.status_code == 200:
            # Use lock to safely add recursive tasks
            with lock:
                for subword in wordlist:
                    new_word = f"{word}/{subword}"
                    word_queue.put(new_word)  # Add new word to the queue

        word_queue.task_done()
            


def main():
    args = command_line_arguments()
    #enumeration(args.wordlist,args.URL,args.recursion)
    wordlist = import_wordlist(args.wordlist)

    num_threads = 10
    threads = []
    for i in range(num_threads):
        t = threading.Thread(target=enumeration,name=f"Thread-{i+1}")
        t.start()
        threads.append(t)

    # Wait for all threads to finish
    for t in threads:
        t.join()

    #request = send_request(args.URL)
    #import_wordlist(args.wordlist)

    

    
    

if __name__ == '__main__':
    main()