# Setting up IPFS
wget https://dist.ipfs.tech/ipfs-update/v1.9.0/ipfs-update_v1.9.0_linux-amd64.tar.gz
tar -xvzf ipfs-update_v1.9.0_linux-amd64.tar.gz
cd ipfs-update
sudo bash install.sh
sudo ipfs-update install latest
ipfs --version
ipfs init

# Setting up Pip 
sudo apt-get update
sudo apt install python3-pip

# Setting up Python requirements
pip install grpcio
pip install onnxruntime
pip install ezkl
pip install numpy
pip install ecdsa
pip install transformers
pip install hashlib
pip install pycryptodome
