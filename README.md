# Builder

This is the component of Gilliam that builds app images.  It currently
only supports git.  If you need any kind of special keys for git, you
need to configure those for the user that will run the builder server.

# Installation

# API

The builder provides a simple REST API normally running on port 8001.
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