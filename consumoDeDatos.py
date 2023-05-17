import openai
import config
import json
import re
import requests

openai.api_key = config.api_key

previousMessages = []
data = []

memmory = 5
max_tokens = 1000

def extractJson(response):
    json_match = re.search(r'\{[\s\S]*\}', response)
    if json_match:
        json_string = json_match.group()
        return json.loads(json_string)
    else:
        return None

def fetch_data(json_data):
    data_to_return = []
    if json_data is not None:
        if json_data['customers']:
            url = 'http://127.0.0.1:3000/getCustomers'
            response = requests.get(url)
            if response.status_code == 200:
                data_to_return.append(response.json())

        if json_data['sales']:
            url = 'http://127.0.0.1:3000/getSales'
            response = requests.get(url)
            if response.status_code == 200:
                data_to_return.append(response.json())

        if json_data['products']:
            url = 'http://127.0.0.1:3000/getProducts'
            response = requests.get(url)
            if response.status_code == 200:
                data_to_return.append(response.json())

        if json_data['salesDetails']:
            url = 'http://127.0.0.1:3000/getSalesDetails'
            response = requests.get(url)
            if response.status_code == 200:
                data_to_return.append(response.json())
    return data_to_return


def chat_part1(request):
    global data, max_tokens

    messages = [
        {
            "role": "system",
            "content": '''You are a virtual assistant named Pablo, working for the company Global MVM. Your main responsibility
            is to understand and address user inquiries, providing relevant information about the company based on the data available to you.

            When responding to a user inquiry, your reply should mimic the structure of a JSON object following this format:
            
            ```{
            "customers": 0 or 1,
            "sales": 0 or 1,
            "products": 0 or 1,
            "salesDetails": 0 or 1,
            "downloads": 0 or 1
            }```
            
            The values in this pseudo-JSON object should be filled as per the following guidelines:

            - "customers": Set to 1 if the user's query relates to the company's customers, otherwise 0.
            - "sales": Set to 1 if the user's query relates to the company's sales, otherwise 0.
            - "products": Set to 1 if the user's query relates to the company's products, otherwise 0.
            - "salesDetails": Set to 1 if the user's query relates to detailed aspects of the company's sales, otherwise 0.
            - "downloads": Set to 1 if the user's query relates to the downloading of the company's products, otherwise 0.
            '''
        },
        {
            "role": "user",
            "content": request
        }
    ]

    api_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=max_tokens  
    )

    response = api_response['choices'][0]['message']['content']

    json_data = extractJson(response)
    
    # print(json_data)

    return json_data


def chat_part2(request, json_data):
    global previousMessages, data, max_tokens, memmory

    new_data = fetch_data(json_data)
    if new_data:
        data.append(new_data)

    if len(previousMessages) % memmory == 0:  
        previousMessages.append({
            "role": "assistant",
             "content": '''You are a virtual assistant named Pablo, working for the company Global MVM. 
            Your main responsibility is to understand and address user inquiries, providing relevant information 
            about the company based on the data available to you. ''' + str(data)
        })

    previousMessages.append({"role": "user", "content": request})

    if len(previousMessages) > memmory:
        previousMessages = previousMessages[-memmory:]

    api_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=previousMessages,
        max_tokens=max_tokens 
    )

    response = api_response['choices'][0]['message']['content']
    previousMessages.append({"role": "assistant", "content": response})
    
    # print(data)

    return response


while True:
    request = input("What is your request? (type 'exit' to quit)\n")

    if request.lower() == 'exit':
        break

    json_data = chat_part1(request)
    response = chat_part2(request, json_data)
    print(f'\n{response}\n')
    
    
#EXAMPLE
# quiero que revises que ventas se han realizado, que customer ha realizado la compra y que producto ha comprado, dame una tabla con la el correo del comprador, el producto que compro y el precio del producto
