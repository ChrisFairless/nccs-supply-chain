FROM python:3.10.7

WORKDIR /app

COPY . .

RUN pip3 install -r requirements_dashboard.txt

CMD bokeh serve dashboard.py --port 5007 --use-xheaders --allow-websocket-origin="*.correntics.ch"