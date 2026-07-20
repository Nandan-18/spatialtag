FROM python:3.14-slim

WORKDIR /app

COPY docker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY spatial /app/spatial
COPY docker/app.py /app/app.py
COPY docker/templates /app/templates
COPY docker/static /app/static
COPY docker/startup.sh /app/startup.sh

RUN sed -i 's/\r$//' /app/startup.sh && chmod +x /app/startup.sh \
    && mkdir -p /app/uploads && chmod 750 /app/uploads

EXPOSE 5000

CMD ["/app/startup.sh"]
