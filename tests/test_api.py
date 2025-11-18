import requests


def  test_upload_file():
    url = 'http://127.0.0.1:8000/uploadfile'
    file = {'file': open('data/two_month_hot_mess_data.csv', 'rb')}
    resp = requests.post(url=url, files=file) 
    print(resp.json())

def test_ping():
    url = 'http://127.0.0.1:8000/'
    resp = requests.get(url=url)
    print(resp.json())

if __name__ == "__main__":
    test_upload_file()
    test_ping()