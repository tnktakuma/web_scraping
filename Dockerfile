FROM public.ecr.aws/lambda/python:3.12

RUN dnf install -y \
        atk \
        cups-libs \
        gtk3 \
        libXcomposite \
        libXcursor \
        libXdamage \
        libXext \
        libXi \
        libXrandr \
        libXScrnSaver \
        libXtst \
        pango \
        alsa-lib \
        nss \
        wget \
        unzip \
        tar \
        gzip \
    && dnf clean all

RUN CHROME_VERSION="$(wget -q -O - https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_STABLE)" \
    && wget -q -O /tmp/chrome.zip "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chrome-linux64.zip" \
    && wget -q -O /tmp/chromedriver.zip "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chromedriver-linux64.zip" \
    && unzip -q /tmp/chrome.zip -d /opt \
    && unzip -q /tmp/chromedriver.zip -d /opt \
    && mv /opt/chromedriver-linux64/chromedriver /opt/chromedriver \
    && ln -s /opt/chrome-linux64/chrome /opt/chrome \
    && chmod +x /opt/chrome-linux64/chrome \
    && chmod +x /opt/chromedriver \
    && rm -rf /tmp/chrome.zip /tmp/chromedriver.zip /opt/chromedriver-linux64

ENV CHROME_BINARY_PATH=/opt/chrome \
    CHROMEDRIVER_PATH=/opt/chromedriver \
    PYTHONUNBUFFERED=1

COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r requirements.txt

COPY lambda_app.py shinagawa_api.py tokyo_api.py ${LAMBDA_TASK_ROOT}/

CMD ["lambda_app.lambda_handler"]
