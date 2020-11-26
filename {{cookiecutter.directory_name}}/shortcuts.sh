#!/usr/bin/env bash

pdb() {
    docker-compose stop django
    # shellcheck disable=SC2086
    docker-compose run $DOCKER_ARGS --service-ports django
}

show_help() {
cat << EOF
Usage: ${0##*/} [logs | bash | root | psql | lint | pdb | vscode | test | manage]

Arguments:
    logs:            Tail a docker container's logs
    bash:            Enter a bash shell on a docker container. Default is django
    root:            Enter a bash shell on a docker container with root access. Default is django
    psql:            Open a postgres shell
    pdb:             Open a debugging session with pdb
    test:            Run backend tests
    manage:          Run a django command
EOF
}


cmd="${1:-}"
shift || true

if [[ -z "$cmd" ]]; then
    show_help >&2; exit 1
fi

# map some commands so we can just pass them to manage... for now
case "$cmd" in
    shell) cmd="shell_plus"
        ;;
esac

case "$cmd" in
    logs) docker-compose logs --tail=100 -f "$@"
        ;;
    bash) docker-compose run --rm "${1:-django}" bash
        ;;
    root) docker-compose run --rm --user 0 "${1:-django}" bash
        ;;
    psql) docker-compose exec db psql -U postgres django
        ;;
    pdb) pdb
        ;;
    test) docker-compose run --rm django pytest "$@"
        ;;
    manage) docker-compose run --rm django python -Wall manage.py "$@"
        ;;

    *) docker-compose run --rm django python -Wall manage.py "$cmd" "$@"
        ;;
esac
