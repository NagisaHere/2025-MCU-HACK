import requests

url = "http://192.168.139.201/image" # ip of the web server

response = requests.get(url)
if response.status_code == 200:
    print("message received; writing")
    with open('requests.jpg', 'wb') as file:
        file.write(response.content)
