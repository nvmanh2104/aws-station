import os
import shutil
import psutil
from subprocess import check_output
import subprocess

def kill_process(name):
    for proc in psutil.process_iter():
        try:
            # Get process name & pid from process object.
            processName = proc.cmdline()#proc.name()
            processID = proc.pid
            if name in processName:
                p = psutil.Process(processID)
                p.terminate()
            print(processName, ' ::: ', processID)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
def main():
    number_client = 2
    #copy n client
    for i in range(number_client):
        shutil.copy("test_emqtt.py","test_emqtt_" + str(i) + ".py")
    #find all process and stop it
    kill_process("note")
    # call n client run in background
    for i in range(number_client):
        filename = "test_emqtt_" + str(i) + ".py"
        cmd = "nohup python " + filename
        subprocess.Popen(cmd)
    print "Start %s clients successfully!", number_client
if __name__ == '__main__':
    main()