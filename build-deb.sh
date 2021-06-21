sudo mk-build-deps --install debian/control
dpkg-buildpackage -uc -us
mv ../metasorter*.deb ./
lintian metasorter*.deb
