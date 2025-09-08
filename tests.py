from functions.get_files_info import get_files_info
from functions.get_file_content import get_file_content
from functions.write_file import write_file
from functions.run_puthon_file import run_python_file
def main():
 
    print(run_python_file("calculator", "main.py"))
    print("-----")
    print(run_python_file("calculator", "main.py", ["10 + 10"]))
    print("-----")
    print(run_python_file("calculator", "tests.py"))
    print("-----")
    print(run_python_file("calculator", "../main.py"))
    print("-----")
    print(run_python_file("calculator", "nonexistent.py"))
  
    

main()