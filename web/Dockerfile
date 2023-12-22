FROM python:3.11

RUN mkdir app
RUN cd app
WORKDIR app
ENV VIRTUAL_ENV=venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH=$VIRTUAL_ENV/bin:$PATH
RUN . $VIRTUAL_ENV/bin/activate
RUN mkdir src
RUN cd src
WORKDIR src
COPY . .
RUN /app/venv/bin/pip install -r requirements.txt
RUN apt-get update && apt-get install cron -y
COPY ./cronjob /etc/cron.d/container_cronjob
RUN chmod 644 /etc/cron.d/container_cronjob
RUN crontab /etc/cron.d/container_cronjob
EXPOSE 8000
#CMD python3 -m uvicorn web:app --reload --host 0.0.0.0 --port 8000
CMD /etc/init.d/cron start && /app/venv/bin/gunicorn web:app --bind 0.0.0.0:8000 -k uvicorn.workers.UvicornWorker