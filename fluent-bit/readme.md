# Update package list
sudo apt-get update

# Install dependencies
sudo apt-get install -y build-essential cmake flex bison libyaml-dev libssl-dev

# Download and build Fluent Bit
git clone https://github.com/fluent/fluent-bit.git
cd fluent-bit
cmake -DFLB_RELEASE=On -DFLB_TRACE=Off -DFLB_JEMALLOC=On -DFLB_TLS=On -DFLB_SHARED_LIB=Off -DFLB_EXAMPLES=Off .
make
sudo make install

# check if installation is successful
/usr/local/bin/fluent-bit -i cpu -o stdout -f 1