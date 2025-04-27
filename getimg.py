import requests
import pyfirmata

url = "http://192.168.139.201/image" # ip of the web server
DIGITAL_HIGH = 1;
board = pyfirmata.Arduino('/dev/ttyACM1');
board.digital[2].mode = pyfirmata.INPUT;
iter8 = pyfirmata.util.Iterator(board);
iter8.start();


while (1):
    if board.digital[2].read() == DIGITAL_HIGH:
        response = requests.get(url)
        if response.status_code == 200:
            print("message received; writing")
            with open('requests.jpg', 'wb') as file:
                file.write(response.content)
                break;
