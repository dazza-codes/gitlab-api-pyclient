# Gitlab API Tools

Simple script to interact with gitlab runners API.

```sh
git clone https://github.com/dazza-codes/gitlab-api-pyclient.git
cd gitlab-api-pyclient
poetry install
```

Then copy and edit `.env.example` into `.env` to setup gitlab API
access and to define other parameters to enable or disable gitlab
runners (based on runner_id).  Then run the update script:

```sh
python ./gitlab_api/runner.py
```

It has a dry run mode to just print activity that would be done.

The project could be improved in many respects.  The primary
purpose to enable or disable gitlab runners across many projects
is working OK.
