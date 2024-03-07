# Хостинг LLM-моделей в облаке VK Cloud

Первое, с чем стоит определиться при хостинге LLM-моделей в облаке - это будем ли мы использовать GPU для ускорения работы модели:

* Для хостинга моделей на CPU на публично-доступных виртуальных машинах


### Хостинг на CPU с localllm

1. Создайте виртуальную машину (VM):
    - Рекомендуется максимально доступная комплектация (16 vCPU + 64 Gb RAM).
    - Размер диска выбирайте достаточно большим, в районе 50Gb (модели большие!)
    - В качестве операционной системы выберите **Ubuntu 22**.
    - Для входа по ssh рекомендуется на этапе создания виртуальной машины загрузить свой публичный ключ ssh. Если вы не знаете, как это делать - почитайте (например, [тут](https://www.cloud4y.ru/blog/how-to-generate-ssh/))
    - В сетевых настройках Firewall выберите группу безопасности **ssh+www**, чтобы сетевой экран пропускал HTTP-соединения по порту 80.
2. Зайдите на виртуальную машину с помощью ssh: `ssh ubuntu@xx.xx.xx.xx`, где xx.xx.xx.xx - IP-адрес вашей VM.
    > Рекомендуется сразу запустить утилиту `screen`, чтобы при разрыве связи с виртуальной машиной по таймауту работа не прекращалась. В случае разрыва связи можно будет подключиться к машине повторно, и возобновить сеанс командой `screen -rd`.
3. Установите необходимые программные пакеты:
    ```bash
    sudo apt update
    sudo apt install python-dev-is-python3 python3-pip g++
    ```
4. Клонируйте репозиторий **localllm**:
    ```bash
    git clone https://github.com/googleCloudPlatform/localllm
    ```
5. Установите утилиту `llm`:
    ```bash
    cd localllm/llm-tool
    pip3 install .
    ```
6. Теперь вам должна быть доступна для запуска команда `llm`. Если этого не произошло, вам необходимо добавить директорию в PATH:
    ```bash
    PATH=/home/ubuntu/.local/bin:$PATH
    ```
7. Скачайте модель, которую вы хотите использовать, с репозитория HuggingFace. Подходят любые модели в формате GGUF. Рекомендуется выбирать модели из [репозитория TheBloke](https://huggingface.co/TheBloke?search_models=GGUF). Например, для использования модели Saiga-Mistral:
    ```bash
    llm pull TheBloke/saiga_mistral_7b-GGUF
    ```
    В некоторых случаях может потребоваться указание имени файла с моделью, например:
    ```bash
    llm pull IlyaGusev/saiga2_13b_gguf --filename model-q2_K.gguf
    ```
8. Для запуска сервера на порте 80, разрешите интерпретатору Python осуществлять захват системных портов с помощью команды:
    ```bash
    sudo setcap 'cap_net_bind_service=+ep' /usr/bin/python3.10
    ```
9. Запустите сервер с моделью:
    ```bash
    llm run TheBloke/saiga_mistral_7b-GGUF 80
    ```
    Если вы указывали имя файла в параметре `--filename` при скачивании модели, то здесь его тоже нужно указать аналогичным образом.
10. Вы можете убедиться, что сервер работает, командой `llm ps`
11. Чтобы убедиться, что сервер доступен из внешнего интернета, введите у себя в браузере адрес `http://xx.xx.xx.xx/v1/models` (где xx.xx.xx.xx - IP-адрес виртуальной машины). Вы должны получить примерно следующий ответ:
    ```json
    {
        "object": "list",
        "data": [
            {
                "id": "/home/ubuntu/.cache/huggingface/hub/models--TheBloke--saiga_mistral_7b-GGUF/26fd/saiga_mistral_7b.Q4_K_M.gguf",
                "object": "model",
                "owned_by": "me",
                "permissions": []
            }
        ]
    }
    ```
11. Теперь вы можете подключаться к серверу с использованием OpenAI-совместимого API. Например, вы можете использовать стандартные классы фреймворка LangChain:
    ```python
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_openai import ChatOpenAI, AzureChatOpenAI

    chat = ChatOpenAI(api_key="123",
        model = "/home/ubuntu/.cache/huggingface/hub/models--TheBloke--saiga_mistral_7b-GGUF/26fd/saiga_mistral_7b.Q4_K_M.gguf",
        openai_api_base = "http://xx.xx.xx.xx/v1")

    messages = [
        SystemMessage(content="Ты - умный ассистент по имени Робби."),
        HumanMessage(content="Привет! Расскажи анекдот про русского и ирландца.")
    ]

    res = chat.invoke(messages)
    ```
    Здесь xx.xx.xx.xx необходимо заменить на IP-адрес виртуальной машины, а model - на строчку, полученную на предыдущем шаге в поле `id`.
12. Пример кода, который автоматически запрашивает имя модели и вызывает её как в синхронном режиме, так и в режиме стриминга, содержится в файле [`test/test.py`](test/test.py).
13. Наслаждайтесь!

Примерная скорость работы моделей (в скобках указана скорость работы в режиме стриминга, если отличается):

Model |  Filename | STD3-8-16** (8 vCPU, 16 RAM)
------|-----------| ----------------------------
TheBloke/saiga_mistral_7b-GGUF | saiga_mistral_7b.Q2_K.gguf | 12 char/sec 
TheBloke/saiga_mistral_7b-GGUF | - | 11 char/sec
IlyaGusev/saiga2_13b_gguf | model-q2_K.gguf | 8 char/sec
TheBloke/Mixtral-8x7B-Instruct-v0.1-LimaRP-ZLoss-DARE-TIES-GGUF | mixtral-8x7b-instruct-v0.1-limarp-zloss-dare-ties.Q2_K.gguf | 9 (18) char/sec
lmstudio-ai/gemma-2b-it-GGUF | gemma-2b-it-q4_k_m.gguf | 28 (39) char/sec
oblivious/ruGPT-3.5-13B-GGUF | ruGPT-3.5-13B-Q2_K.gguf | 