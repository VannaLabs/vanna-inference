ipfs init
cp ./swarm.key ~/.ipfs/swarm.key
export LIBP2P_FORCE_PNET=1
ipfs bootstrap add /ip4/3.140.191.156/tcp/4001/p2p/12D3KooWQWntZ1RYAxBtqbPcRz1e24o9xzXkvieJnhhNAC6xKwAF 
ipfs daemon &
python3 server.py 
