# jrcms
a simple python cms using Markdown to write, compatible with **python2.7** and **3.4**(may be 2.6 or 3.3 but they're not tested)

## deploy

    nohup python runserver.py &
  
It defaults to listen on `0.0.0.0:5000` using a tornado server, you can bind your domain with usual web server with proxypass like nginx.

## add the first author

Out of security, it does not have a web interface for author controlling. I offer a handy python script at root director `author.py`.

    ./author.py -au AUTHOR_NAME

To see ther options, type `./author.py -h`.

Use above command to add a new author and you can login at `<blog-url>/login`. 
