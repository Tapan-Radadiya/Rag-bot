FROM python:3.14

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./main.py /code/app
COPY ./input_types.py /code/app
COPY ./models.py /code/app
COPY ./database.py /code/app

CMD ["fastapi", "run", "app/main.py", "--port", "80"]