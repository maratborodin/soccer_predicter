FROM python:3.11

RUN mkdir app
RUN cd app
WORKDIR app
ENV VIRTUAL_ENV=venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH=$VIRTUAL_ENV/bin:$PATH
RUN mkdir src
RUN cd src
WORKDIR src
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8000
CMD python3 reload.py telegram_bot.py