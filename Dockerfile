FROM archlinux:base

# image configuration
ENV AHRIMAN_ARCHITECTURE="x86_64"
ENV AHRIMAN_DEBUG=""
ENV AHRIMAN_FORCE_ROOT=""
ENV AHRIMAN_HOST="0.0.0.0"
ENV AHRIMAN_OUTPUT="syslog"
ENV AHRIMAN_PACKAGER="ahriman bot <ahriman@example.com>"
ENV AHRIMAN_PORT=""
ENV AHRIMAN_REPOSITORY="aur-clone"
ENV AHRIMAN_REPOSITORY_ROOT="/var/lib/ahriman/ahriman"
ENV AHRIMAN_USER="ahriman"

# install environment
## install minimal required packages
RUN pacman --noconfirm -Syu binutils fakeroot git make sudo
## create build user
RUN useradd -m -d /home/build -s /usr/bin/nologin build && \
    echo "build ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/build
COPY "docker/install-aur-package.sh" "/usr/local/bin/install-aur-package"
## install package dependencies
## darcs is not installed by reasons, because it requires a lot haskell packages which dramatically increase image size
RUN pacman --noconfirm -Sy devtools git pyalpm python-inflection python-passlib python-requests python-srcinfo && \
    pacman --noconfirm -Sy python-build python-installer python-wheel && \
    pacman --noconfirm -Sy breezy mercurial python-aiohttp python-boto3 python-cryptography python-jinja rsync subversion && \
    runuser -u build -- install-aur-package python-aioauth-client python-aiohttp-jinja2 python-aiohttp-debugtoolbar \
                                            python-aiohttp-session python-aiohttp-security

# cleanup unused
RUN find "/var/cache/pacman/pkg" -type f -delete

# install ahriman
## copy tree
COPY --chown=build . "/home/build/ahriman"
## create package archive and install it
RUN cd "/home/build/ahriman" && \
    make VERSION=$(python -c "from src.ahriman.version import __version__; print(__version__)") archlinux && \
    cp ./*-src.tar.xz "package/archlinux" && \
    cd "package/archlinux" && \
    runuser -u build -- makepkg --noconfirm --install --skipchecksums && \
    cd / && rm -r "/home/build/ahriman"

VOLUME ["/var/lib/ahriman"]

# minimal runtime ahriman setup
COPY "docker/entrypoint.sh" "/usr/local/bin/entrypoint"
ENTRYPOINT ["entrypoint"]
# default command
CMD ["repo-update"]
