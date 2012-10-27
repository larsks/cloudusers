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

Users can use the *cloudusers* interface to re-generate their
OpenStack password at any time.

