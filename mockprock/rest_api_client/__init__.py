"""
This module is copied out of edx-rest-api-client version 1.9.2.

That package was only ever meant to support Django-based clients, but
at that version happened to be generic enough to be usable from a
non-Django-based client as well. Rather than pinning the version to
the unintentionally more flexible version, we've copied the code from
the old version into this repo both to minimize dependencies pulled in
& to clarify that our use case is different from that of other
dependents on the package.
"""
