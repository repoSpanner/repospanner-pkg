#!/bin/bash -xe
VERSION="0.5"
GITREV="$(GIT_DIR=~/src/repoSpanner/.git git rev-parse HEAD)"
(
	cd ~/src/repoSpanner
	trap "rm -rf repoSpanner-${VERSION}" EXIT
	FILES="`ls`"
	mkdir repoSpanner-${VERSION}
	cp -r $FILES repoSpanner-${VERSION}
	# Delete binaries
	rm -f repoSpanner-${VERSION}/{repospanner,repohookrunner,repobridge}
	(
		cd repoSpanner-${VERSION}
		# Mod vendor
		go mod vendor
	)
	tar -cavf repoSpanner-${VERSION}-${GITREV}.tar.gz repoSpanner-${VERSION}
	rm -rf repoSpanner-${VERSION}
)
mv ~/src/repoSpanner/repoSpanner-${VERSION}-${GITREV}.tar.gz .
sed -i "s/%global gcommit.*\w/%global gcommit         ${GITREV}/" repospanner.spec
rpmdev-bumpspec repospanner.spec --comment "$1"
fedpkg --release epel7 prep
vim repospanner.spec
fedpkg --release epel7 srpm
# rm -rf repoSpanner-${VERSION} repoSpanner-${VERSION}-${GITREV}.tar.gz
