# the dockerfile is for localhost testing and pytest
FROM python:3.8 AS synth_data

WORKDIR /code
 
COPY ./requirements.txt /code/requirements.txt
 
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Install MBI for MST SD model
RUN git clone https://github.com/ryan112358/private-pgm.git
RUN cd private-pgm && python -m pip install .

# Install Smartnoise Synth from source to get the latest (incl MST)
RUN git clone https://github.com/opendp/smartnoise-sdk.git
RUN cd smartnoise-sdk/synth && python -m pip install .

COPY ./src/ /code/

FROM synth_data AS synth_data_test
# run tests with pytest
COPY ./tests/ /code/tests/
cmd ["python", "-m", "pytest", "tests/"]

FROM synth_data

COPY ./tests/yaml/runtime_mwem_1.yaml /usr/runtime.yaml
# run as local server
CMD ["python", "uvicorn_serve.py"]