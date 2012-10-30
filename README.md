cloudusers
==========

A web interface for automatically provisioning user accounts in OpenStack.

The general idea
================

- You set up *cloudusers* to authenticate against some external source
  (local LDAP or AD, or really anything else supported by your web
  server of choice).
- *cloudusers* receives the authenticated username from your
  webserver.
- *cloudusers* creates a matching account in OpenStack with a randomly
  generated password.
- Users can use the *cloudusers* interface to re-generate their
  OpenStack password at any time.

Requirements
============

- python-novaclient
- python-keystoneclient
- [Bottle][] >= 0.11.0

*Cloudusers* has explicit support for running using a Python virtual
environment.  If you create a virtual environment called `env` inside
the application folder, *cloudusers* will add the appropriate
`site-packages` directory to `sys.path`.  You can set it up like this:

    # cd cloudusers
    # virtualenv --system-site-packages env
    # ./env/bin/easy_install -U bottle

This will create a virtual environment that knows about third-party
modules installed in your system Python library but that has the most
recent version of [Bottle][], regardless of what is installed on your
system.

[bottle]: http://bottlepy.org/

Configuration
=============

Configuring Apache
------------------

*Cloudusers* is designed to be run via [mod_wsgi][].  You will need to
add something similar to the following to your Apache configuration:

    WSGIDaemonProcess cloudusers
    WSGIProcessGroup cloudusers
    WSGIScriptAlias /request /var/www/cloudusers/adapter.wsgi

    ## If you're just testing things out this may make your life
    ## easier: it prevents mod_ldap from verifying the certificate
    ## presented by your LDAP server.  In a production deployment
    ## you really want to get your certificate authorities configured
    ## correctly.
    # LDAPVerifyServerCert off

    <Location /request>
      Order allow,deny
      Allow from all
    </Location>

    ## Everything under /request/auth needs to be password
    ## protected.  This example is using LDAP, but of course you 
    ## could use anything supported by Apache.
    <Location /request/auth/>
      AuthName "Cloud"
      AuthType Basic
      AuthBasicProvider ldap

      AuthLDAPURL ldaps://ldap.example.com/ou=people,dc=example,dc=com

      Require valid-user
    </Location>

Configuring cloudusers
-----------------------

*Cloudusers* reads configuration from the file `cloudusers.yaml` in
the application directory.  The repository includes a sample file
named `cloudusers-sample.yaml` as an example:

    ---
    # This defines the security rules created for the "default" security
    # group when creating a new "user/<username>" tenant.
    security rules:
      # all icmp traffic
      - protocol: icmp
        from port: -1
        to port: -1
      # ssh
      - protocol: tcp
        from port: 22
        to port: 22
      # http and https
      - protocol: tcp
        from port: 80
        to port: 80
      - protocol: tcp
        from port: 443
        to port: 443

    # Set this to False to disable the /auth/debug screen.
    debug: True

    # Keystone endpoint and admin token.
    service_endpoint: http://127.0.0.1:35357/v2.0/
    service_token: SECRET

You will need to make sure that `service_endpoint` is pointing to your
local Keystone instance and that `service_token` is your admin token.
This example includes security rules that enable `icmp`, `ssh`, and
`http`/`https` traffic.

[mod_wsgi]: https://code.google.com/p/modwsgi/

