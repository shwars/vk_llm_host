from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, AzureChatOpenAI
import requests
from time import time

base_url = "http://xx.xx.xx.xx/v1" # укажите IP-адрес своей виртуальной машины

print("Calling the node to get model name...")
res = requests.get(base_url+"/models")
js = res.json()
print("Supported models:")
for x in js['data']:
    print(f" + {x['id']}")
    model = x['id']

print(f"Calling langchain model {model}")

chat = ChatOpenAI(api_key="123",
                  model = model,
                  openai_api_base = base_url)

messages = [
    SystemMessage(
        content="Ты - умный ассистент по имени Робби."
    ),
    HumanMessage(
        content="Привет! Расскажи анекдот про русского и ирландца."
    ),
]

t = time()
res = chat.invoke(messages)
t = time() - t

print(res)
print(f"Time: {t}, ({len(res.content)/t} chars/sec)")

print("Trying streaming...")

t = time()
res = ""
for chunk in chat.stream("Расскажи анекдот про Ирландца и C++."):
    print(chunk.content, end="", flush=True)
    res += chunk.content

t = time() - t
print(f"Time: {t}, ({len(res)/t} chars/sec)")