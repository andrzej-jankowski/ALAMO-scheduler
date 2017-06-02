
# Install essential packages
sudo apt-get update
sudo apt-get upgrade
sudo apt-get -y install mc vim git 2> /dev/null
sudo apt-get -y install redis-server 2> /dev/null
sudo apt-get -y install build-essential libbz2-dev libfreetype6-dev libgdbm-dev python3-dev 2> /dev/null
sudo apt-get -y install python3-pip 2> /dev/null

# Create virtualenv for python 3.4
sudo pip3 install virtualenvwrapper
VIRTUALENVS='/home/ubuntu/.virtualenvs'
if [ ! -d $VIRTUALENVS ]; then
mkdir /home/ubuntu/.virtualenvs
export WORKON_HOME=$VIRTUALENVS
export VIRTUALENVWRAPPER_PYTHON='/usr/bin/python3'
source /usr/local/bin/virtualenvwrapper.sh
mkvirtualenv alamo
fi


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
echo 'export ALAMO_SCHEDULERS=`hostname -f`' >> /home/ubuntu/.bashrc
fi

# Install application environment
/home/ubuntu/.virtualenvs/alamo/bin/pip install ipython tox
/home/ubuntu/.virtualenvs/alamo/bin/pip install asyncio asyncio_redis aioconsul aioamqp apscheduler
/home/ubuntu/.virtualenvs/alamo/bin/pip install -r /home/ubuntu/project/requirements.txt
/home/ubuntu/.virtualenvs/alamo/bin/pip install -e /home/ubuntu/project/.
