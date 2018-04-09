CA structure created following the tutorial at
https://jamielinux.com/docs/openssl-certificate-authority/create-the-root-pair.html

To generate all needed certs for the project, run ./generate_all.sh script. When prompted for
key password type hgwpwd

On windows you can build the docker image by running and then run it specifying the output dir

```bash
docker build -t certs_generator .
docker run -it -v out:/out/ certs_generator <list_of_additional_services>
```
