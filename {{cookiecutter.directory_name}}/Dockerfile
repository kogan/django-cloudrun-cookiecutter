# --- Layer 1: Python dependencies ---
#
# This can be slow, and changes less frequently than the code. By installing
# deps into this layer, and just copying over the whole virtualenv, we can avoid
# the overhead of installing dependencies again if they don't change.
#
# There's one trick to this: the --no-root option to Poetry. By default, Poetry
# wants to install the source package, which means COPYing src/, which means we
# have to re-install every time anything changes.

FROM python:3.8 as pydeps
WORKDIR /app

# Set PRODUCTION=1 to skip install of dev dependencies
ARG PRODUCTION

# Pin the version of poetry to avoid potential API changes breaking the build
RUN pip install -U pip && \
    pip install poetry==1.0.0

# virtualenvs.in-project means create the virtualenv in /code/.venv, which means
# the path is predictable to COPY later.
RUN mkdir -p ${HOME}/.config/pypoetry/ && \
    poetry config virtualenvs.in-project true

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root ${PRODUCTION:+--no-dev}


# put everything together
# Copy deps over from previous layer, and run the app.

FROM python:3.8-slim
WORKDIR /app

COPY --from=pydeps /app/.venv /app/.venv/

COPY . ./code
# Explicitly put our code on PYTHONPATH to avoid having to install poetry and
# activiate it on this layer.
ENV PYTHONPATH=/app/code

# Make sure our virtualenv is used by default when we execute `python` in the
# container. This is the same as the `activate` magic, but done by hand. See
# https://pythonspeed.com/articles/activate-virtualenv-dockerfile/ for the
# technique.
ENV VIRTUAL_ENV /app/.venv
ENV PATH "/app/.venv/bin:${PATH}"

WORKDIR /app/code

RUN python manage.py collectstatic --noinput
CMD waitress-serve --threads=5 --listen=*:$PORT {{cookiecutter.application_name}}.wsgi:application
