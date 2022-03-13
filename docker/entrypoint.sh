#!/bin/bash

set -e
[ -n "$AHRIMAN_DEBUG" ] && set -x

# configuration tune
sed -i "s|root = /var/lib/ahriman|root = $AHRIMAN_REPOSITORY_ROOT|g" "/etc/ahriman.ini"
sed -i "s|host = 127.0.0.1|host = 0.0.0.0|g" "/etc/ahriman.ini"
sed -i "s|handlers = syslog_handler|handlers = ${AHRIMAN_OUTPUT}_handler|g" "/etc/ahriman.ini.d/logging.ini"

AHRIMAN_DEFAULT_ARGS=("-a" "$AHRIMAN_ARCHITECTURE")
if [[ "$AHRIMAN_OUTPUT" == "syslog" ]]; then
    if [ ! -e "/dev/log" ]; then
        # by default ahriman uses syslog which is not available inside container
        # to make noise less we force quiet mode in case if /dev/log was not mounted
        AHRIMAN_DEFAULT_ARGS+=("-q")
    fi
fi

# create repository root inside the [[mounted]] directory and set correct ownership
[ -d "$AHRIMAN_REPOSITORY_ROOT" ] || mkdir "$AHRIMAN_REPOSITORY_ROOT"
chown "$AHRIMAN_USER":"$AHRIMAN_USER" "$AHRIMAN_REPOSITORY_ROOT"
# run initial setup
sudo -u "$AHRIMAN_USER" -- ahriman "${AHRIMAN_DEFAULT_ARGS[@]}" repo-init

# run built-in setup command
AHRIMAN_SETUP_ARGS=("--build-as-user" "$AHRIMAN_USER")
AHRIMAN_SETUP_ARGS+=("--packager" "$AHRIMAN_PACKAGER")
AHRIMAN_SETUP_ARGS+=("--repository" "$AHRIMAN_REPOSITORY")
if [ -n "$AHRIMAN_PORT" ]; then
    # in addition it must be handled in docker run command
    AHRIMAN_SETUP_ARGS+=("--web-port" "$AHRIMAN_PORT")
fi
ahriman "${AHRIMAN_DEFAULT_ARGS[@]}" repo-setup "${AHRIMAN_SETUP_ARGS[@]}"

# refresh database
runuser -u build -- yay --noconfirm -Syy &> /dev/null
# create machine-id which is required by build tools
systemd-machine-id-setup &> /dev/null

# if AHRIMAN_FORCE_ROOT is set or command is unsafe we can run without sudo
# otherwise we prepend executable by sudo command
if [ -n "$AHRIMAN_FORCE_ROOT" ]; then
    AHRIMAN_EXECUTABLE=("ahriman")
elif ahriman help-commands-unsafe | grep -Fxq "$1"; then
    AHRIMAN_EXECUTABLE=("ahriman")
else
    AHRIMAN_EXECUTABLE=("sudo" "-u" "$AHRIMAN_USER" "--" "ahriman")
fi
exec "${AHRIMAN_EXECUTABLE[@]}" "${AHRIMAN_DEFAULT_ARGS[@]}" "$@"
