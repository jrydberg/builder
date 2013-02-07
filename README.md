# Builder

This is the component of Gilliam that builds app images.  It currently
only supports git.  If you need any kind of special keys for git, you
need to configure those for the user that will run the builder server.

# Installation

Install in a virtual environment:

    $ virtualenv .
    $ . bin/activate
    $ pip install -r requirements.txt

Create your database and prepare directories for images and build
packs:

    $ sqlite3 -init schema.sql builder.db .quit
    $ mkdir images packs

Install the build packs that you want:

    $ cd packs
    $ git clone https://github.com/gilliam/buildpack-python.git

# Running

If not already done, activate your virtualenv in the source root
directory, and then start the service using `honcho`:

    $ . bin/activate
    $ honcho start -p 9000

If you need to change any config setting look at `.env`

# API

The builder provides a simple REST API normally running on port 9000.
It exposes two kinds of resources: builds and images.  You can find
builds under `/build/{app}' and images under '/image/{image}'.

To create a new build issue a `POST` to `/build/{app}'.  The request
body *MUST* contain a JSON object with the following fields:

* `repository` (string) should point to a git repository.
* `commit` (string, optional) defines the commit (branch/tag/commit) that
 should be built. 

The server should respond with a `202 Accept` once it has started
processing the request.  The `Location` header in the response points
to the build resource that will be a result of the process.  The body
of the response is the output from the processing steps.  Display this
to your user.

Example:

    $ curl --verbose http://localhost:8001/build/python-example -d '{
       "repository": "https://github.com/gilliam/python-example.git",
       "commit": "master"
    }'

    ...
    < HTTP/1.1 202 Accepted
    < Content-Type: text/html; charset=UTF-8
    < Location: http://localhost:8001/build/python-example/6dc2f9e
    < Date: Thu, 31 Jan 2013 21:42:49 GMT
    < Transfer-Encoding: chunked
    < 
    -----> Python app detected
    -----> No runtime.txt provided; assuming python-2.7.3.
    -----> Preparing Python runtime (python-2.7.3)
    ...

.