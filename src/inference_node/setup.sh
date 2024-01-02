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
pip install grpcio onnxruntime ezkl numpy ecdsa transformers hashlib pycryptodome diffusers transformers accelerate torch --upgrade
