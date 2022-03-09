FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
COPY youtube_bot.py ./
COPY credentials.json ./

RUN pip install --no-cache-dir -r requirements.txt
 
CMD [ "python", "./youtube_bot.py" ]