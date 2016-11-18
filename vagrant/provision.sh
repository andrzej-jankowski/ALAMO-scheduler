
# Install essential packages
apt-get update
apt-get upgrade
apt-get -y install mc vim git 2> /dev/null
apt-get -y install redis-server 2> /dev/null
apt-get -y install build-essential libbz2-dev libfreetype6-dev libgdbm-dev python3-dev 2> /dev/null
apt-get -y install python3-pip 2> /dev/null

# Create virtualenv for python 3.4
pip3 install virtualenvwrapper
VIRTUALENVS='/home/ubuntu/.virtualenvs'
if [ ! -d $VIRTUALENVS ]; then
mkdir /home/ubuntu/.virtualenvs
fi
chown -R ubuntu:ubuntu $VIRTUALENVS
sudo -u ubuntu bash -c "export WORKON_HOME=$VIRTUALENVS"
if [ `grep alamo /home/ubuntu/.bashrc | wc -l` = 0 ]; then
echo "VIRTUALENVWRAPPER_PYTHON='/usr/bin/python3'" >> /home/ubuntu/.bashrc
echo 'command' >> /home/ubuntu/.bashrc
echo 'source /usr/local/bin/virtualenvwrapper.sh' >> /home/ubuntu/.bashrc
echo 'if [ `workon | grep alamo | wc -l` = 1 ]' >> /home/ubuntu/.bashrc
echo 'then' >> /home/ubuntu/.bashrc
echo 'workon alamo' >> /home/ubuntu/.bashrc
echo 'else' >> /home/ubuntu/.bashrc
echo 'mkvirtualenv alamo' >> /home/ubuntu/.bashrc
echo 'fi' >> /home/ubuntu/.bashrc
fi

# Install application environment
su -l ubuntu -c '/home/ubuntu/.virtualenvs/alamo/bin/pip install ipython tox'
su -l ubuntu -c '/home/ubuntu/.virtualenvs/alamo/bin/pip install asyncio asyncio_redis aioconsul aioamqp apscheduler'
