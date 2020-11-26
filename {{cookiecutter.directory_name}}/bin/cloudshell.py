#!/usr/bin/env python3

import argparse
import itertools
import json
import os
import re
import subprocess
import sys

commands = {}
flags = {"mount": False}

connection_re = re.compile(r"^postgres://(?P<user>.+?):(?P<password>.+?)@//cloudsql/(?P<host>.+)$")


def command(name):
    def decorator(f):
        commands[name] = f
        return f

    return decorator


def get_db_connection():
    p = subprocess.Popen(
        [
            "gcloud",
            "--project",
            "{{cookiecutter.project_name}}",
            "secrets",
            "versions",
            "access",
            "--secret",
            "DATABASE_URL",
            "latest",
        ],
        stdout=subprocess.PIPE,
    )
    stdout, stderr = p.communicate()
    conn = stdout.decode("utf-8")
    match = connection_re.match(conn).groupdict()
    instance_name, db_name = match["host"].rsplit("/", maxsplit=1)
    return instance_name, db_name, match["user"], match["password"]


def get_cr_env():
    p = subprocess.Popen(
        [
            "gcloud",
            "--project",
            "{{cookiecutter.project_name}}",
            "run",
            "services",
            "describe",
            "django-app",
            "--format",
            "json",
            "--platform",
            "managed",
            "--region",
            "{{cookiecutter.gcp_region}}",
        ],
        stdout=subprocess.PIPE,
    )
    stdout, stderr = p.communicate()
    details = json.loads(stdout.decode("utf-8"))
    return {
        env["name"]: env["value"]
        for env in details["spec"]["template"]["spec"]["containers"][0]["env"]
    }


def run_docker(*args):
    env = dict(os.environ)
    instance, db, user, password = get_db_connection()
    env.update(
        {
            "DB_INSTANCE": instance,
            "DB_USER": user,
            "DB_PASSWORD": password,
            "DB_NAME": db,
            "GOOGLE_CLOUD_PROJECT": "{{cookiecutter.project_name}}",
        }
    )
    subprocess.Popen(["docker-compose", "pull"], env=env).wait()
    base_args = ["docker-compose", "run", "--rm"]
    if flags["mount"]:
        base_args.extend(["-w", "/app/local/"])
    subprocess.Popen(
        [*base_args, *args], stderr=sys.stderr, stdin=sys.stdin, stdout=sys.stdout, env=env,
    ).wait()

    # stop the proxy so it's not running in the background
    # docker-compose run doesn't support stopping dependencies
    subprocess.Popen(["docker-compose", "rm", "--stop", "-f", "clouddb"]).wait()


@command("psql")
def psql():
    run_docker("cloudpsql")


@command("shell")
def shell():
    run_docker(
        # get ENV from running CR instance.
        # docker-compose -e KEY=value -e NEXT=item ...
        *itertools.chain.from_iterable(
            [["-e", f"{key}={value}"] for key, value in get_cr_env().items()]
        ),
        "-e",
        "PROJECT_ID={{cookiecutter.project_name}}",
        "cloudshell",
    )


def main():
    parser = argparse.ArgumentParser(description="Connect to a {{cookiecutter.project_name}} shell")
    parser.add_argument(
        "--mount", dest="mount", help="Mount local directory", action="store_true", default=False
    )
    parser.add_argument("command", choices=commands.keys())
    args = parser.parse_args()
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        print("env var GOOGLE_APPLICATION_CREDENTIALS is not set", file=sys.stderr)
        exit(1)
    flags["mount"] = args.mount
    commands[args.command]()


if __name__ == "__main__":
    main()
