# Maintainer: test <test@test.com>

pkgname='trellodash'
pkgver="0.1.2"
pkgrel=0
pkgdesc="Install a dashboard using Dash (Python) for Trello"
arch=(any)
url="https://github.com/roytje88/TrelloDash"
license=('GPL')
depends=('python-virtualenv' 'python-numpy')

source=(https://github.com/roytje88/TrelloDash/archive/0.1.2.tar.gz)
sha512sums=('6022ac5e6f78474f03ac18e07ba3929309eac16143efed113ad508dc02e74ab9dd5ec5fc9496cc6bacbdf0a99a0cda5876856f7e7e90b171d9c7677ab7446abc')

##TODO
# create sh file for /usr/bin
# pip ignore --system-site-packages
# echo 'enable systemd service'
# replace all hardcoded folders to version-variables

package() {
    python -m venv $pkgdir/var/lib/trellodash/venv --system-site-packages
    source $pkgdir/var/lib/trellodash/venv/bin/activate
    pip install -r $srcdir/TrelloDash-0.1.2/requirements.txt --ignore-installed
    mkdir -p $pkgdir/var/lib/trellodash
    mv $srcdir/TrelloDash-0.1.2/trellodash.service $pkgdir/usr/lib/systemd/system/ 
    cp -r $srcdir/TrelloDash-0.1.2/* $pkgdir/var/lib/trellodash/
    
    
}