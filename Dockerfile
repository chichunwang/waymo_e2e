FROM python:3.10-slim-bookworm
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
COPY requirements-linux.txt ./
RUN python -m pip install -r requirements-linux.txt && python -m pip check
COPY scripts ./scripts
RUN python scripts/check_environment.py --official
EXPOSE 8888
CMD ["python", "-m", "jupyterlab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
