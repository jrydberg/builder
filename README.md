# Builder

This is the component of Gilliam that builds app images and deploys
them to the scheduler.  All the magic is located in `scripts/build`.
If you need something special for your installation that's the file to
change.

# Installation

First checkout the required submodules (the buildpacks):

    git submodule init
    git submodule update

Install in a virtual environment:

    virtualenv .
    . bin/activate
    pip install -r requirements.txt

# Running

If not already done, activate your virtualenv in the source root
directory, and then start the service using `honcho`:

    . bin/activate
    honcho start -p 9000

If you need to change any config setting look at `.env`

# API

The builder provides a simple REST API normally running on port 9000.
It exposes two kinds of resources: build and images.  You can find
builds under `/build/' and images under '/image/{image}'.

To create a new build issue a `POST` to `/build/'.  The request body
should contain an uncompressed tarball of the app source code.  You
also need to provide the following query parameters to the request:

* `app` - name of the app.
* `commit` - hash of the commit.
* `text` - deploy message.

The server should respond with a `200 OK` once it has started
processing the request.  The body of the response is the output from
the processing steps.  Display this to your user.

Example:

    git archive --format=tar HEAD|curl "http://localhost:9000/build?app=example&commit=master&text=text" \
      -H "Content-Type: application/octet-stream" --data-binary @-
    ...
    < HTTP/1.1 200 OK
    < Content-Type: text/html; charset=UTF-8
    < Date: Thu, 31 Jan 2013 21:42:49 GMT
    < Transfer-Encoding: chunked
    < 
    -----> Python app detected
    -----> No runtime.txt provided; assuming python-2.7.3.
    -----> Preparing Python runtime (python-2.7.3)
    ...

