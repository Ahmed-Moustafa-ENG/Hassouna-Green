# Hassouna Green - self-hosted image.
#
# The app runs entirely on your own server: nothing is sent to Streamlit
# Community Cloud, Vercel or any other hosting platform. Streamlit is used
# only as a Python library inside this container.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Fail the build if the reference database is missing or broken.
RUN python -c "import hassouna_db; d = hassouna_db.load_reference_data(); \
    print('plants:', len(d['plants']), '| edible:', int((d['plants']['group'] != 'ornamental').sum()))"

RUN chmod +x deploy/entrypoint.sh deploy/deploy.sh

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request, sys; \
sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=4).status == 200 else 1)"

CMD ["/app/deploy/entrypoint.sh"]
