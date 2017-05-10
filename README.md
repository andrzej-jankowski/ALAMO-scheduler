# ALAMO-scheduler
Scheduler service for ALAMO project

[![Build Status](https://travis-ci.org/RulersOfAsgard/ALAMO-scheduler.svg?branch=master)](https://travis-ci.org/RulersOfAsgard/ALAMO-scheduler)
[![Coverage Status](https://coveralls.io/repos/RulersOfAsgard/ALAMO-scheduler/badge.svg?branch=master&service=github)](https://coveralls.io/github/RulersOfAsgard/ALAMO-scheduler?branch=master)

## Docker
The Dockerfile is prepared to be run together with the rest of
the ALAMO suite via docker-compose so please see the [alamo-docker](https://github.com/RulersOfAsgard/alamo-docker)
repository.

### Running a single container
If you really need to run just a single container without the rest of
ALAMO, please adapt the settings in contrib/docker_config.cfg accordingly.

### Rendezvous Hashing
Implementation is based on article:
http://www.eecs.umich.edu/techreports/cse/96/CSE-TR-316-96.pdf