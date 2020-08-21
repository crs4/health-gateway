# How to develop Consent Manager GUI

The Consent Manager GUI is developed using ReactJS and is packaged using webpack

In order to have an environment ready to change the JS-developed gui first of all you should intall node (https://nodejs.org/)

Then go to `consent_manager/gui` and run

```bash
npm install
```

This will install all required packages listed in `package.json`

After this you can run

```bash
./node_modules/.bin/webpack-cli 
```

to pack all modules in one file. If you want to continuosly create the pack while changing the source launch

```bash
./node_modules/.bin/webpack-cli --watch
```

## Django collectstatic

If you are developing using the docker environment, you need to collectstatic files using the proper Django command. This means you need to have python and django installed in you local machine.

**NB**: to install the python environment locally, it's raccomended to use virtualenv and install the packages using pip, launching `pip install -r requirements.txt` from the root of the github repository

To generate the static files for docker go to directory `consent_manager/` and launch the command

```bash
python manage.py collectstatic 
```