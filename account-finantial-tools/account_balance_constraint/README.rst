.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

==========================
Account Balance Constraint
==========================

Add fields for minimun balance on accounts.
Add constraint on account.move validation to check account balance don't get that minimun

Installation
============

To install this module, you need to:

#. Just install this module

Configuration
=============

To configure this module, you need to:

#. Go to Accounting / Advisor / Chart of Accounts
#. Choose the account you want to restrict
#. Set restrict balance = True and set minimun balance

Usage
=====

To use this module, you need to:

#. When posting a journal entry, minimun balance constrains are going to be checked


.. repo_id is available in https://github.com/OCA/maintainer-tools/blob/master/tools/repos_with_ids.txt
.. branch is "8.0" for example

Known issues / Roadmap
======================

* ...

Bug Tracker
===========



Credits
=======

Images
------

* Moogah: `Icon <http://www.moogah.com/logo.png>`_.

Contributors
------------


Maintainer
----------

.. image:: http://www.moogah.com/logo.png
   :alt: Odoo Community Association
   :target: https://www.moogah.com

This module is maintained by Moogah.

