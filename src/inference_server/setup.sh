wget https://dist.ipfs.tech/ipfs-update/v1.9.0/ipfs-update_v1.9.0_linux-amd64.tar.gz

tar -xvzf ipfs-update_v1.9.0_linux-amd64.tar.gz

cd ipfs-update

sudo bash install.sh

sudo ipfs-update install latest

ipfs --version
