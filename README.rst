=============
ckanext-reminder
=============

This extension has two main functions.

1. The extension provides simple email notifications for datasets which have a set data-expiry date. The extension relies on a
daily cronjob during which datasets are checked if the reminder-data is set to current date. The email sending process is not
retried in any way and the emails will not be sent if the cronjob fails to run for some reason.

2. The extension provides a subscription form snippet which can be added to dataset templates. Users can submit their
email address and receive notifications of these specific datasets when they are updated. The user can unsubscribe
from any datasets by clicking the link located at the bottom of the email.

------------
Requirements
------------

This extension is developed and tested with CKAN version 2.5.2 but versions starting from 2.2 should work fine.
This extension also needs Bootstrap 3+ for styling to work properly. Bootstrap 2 should mainly be fine, but styles might be a
bit off at least with the subscription_form template.


------------
Installation
------------

To install ckanext-reminder:

1. Activate your CKAN virtual environment, for example::

     . /usr/lib/ckan/default/bin/activate

2. Install the ckanext-reminder Python package into your virtual environment::

     pip install ckanext-reminder

3. Add ``reminder`` to the ``ckan.plugins`` setting in your CKAN
   config file (by default the config file is located at
   ``/etc/ckan/default/production.ini``).

4. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu::

     sudo service apache2 reload

5. Configure fields in the CKAN config file, the required configurations are listed below in the section "Config Settings". 

6. Initialize database tables used by the subscribe to email notifications functionality::

    paster --plugin=ckanext-reminder reminder init --config=YOUR_CONFIGURATION.ini

7. Call the appropriate paster commands in e.g. a cronjob to send the reminders/notifications::

    # For admin reminders of dataset expiration
    paster --plugin=ckanext-reminder reminder send --config=YOUR_CONFIGURATION.ini

    # For update notifications to subscribed users
    paster --plugin=ckanext-reminder reminder notify --config=YOUR_CONFIGURATION.ini

---------------
Config Settings
---------------

The extension supports one recipient for reminder emails. Required configs are::

    # The email links will be prefixed with this site url
    ckanext.reminder.site_url = https://<YOUR_SITE_URL>

    # This configuration can be overwritten in the admin configuration UI
    # This is the default address where emails are sent if a dataset specific email is not set
    ckanext.reminder.email = <YOUR_EMAIL_ADDRESS>
    
    # Name of the field containing a date when the user should be reminded. The date should
    # be in format year-month-day, for example "2018-05-31". The reminder is only sent
    # if current date is the same as the date in the field specified at ckanext.reminder.date_field
    ckanext.reminder.date_field = <DATE_FIELD>
    
    # Name of the field containing the email address for the person responsible for 
    # maintaining the dataset. The email is sent to this address if this is configured
    ckanext.reminder.email_field = <MAINTAINER_EMAIL_ADDRESS>

------------------------
Development Installation
------------------------

To install ckanext-reminder for development, activate your CKAN virtualenv and
do::

    git clone https://github.com/6aika/ckanext-reminder.git
    cd ckanext-reminder
    python setup.py develop
    pip install -r dev-requirements.txt


---------------
Updating translations
---------------

To extract all translatable strings run this command in the plugin root directory::

    python setup.py extract_messages

After this the updated ckanext-reminder.pot with the source language can be pushed to Transifex with the transifex client::

    tx push --source

Translate new strings in Transifex and pull them by running::

    # --force can be added if old translations can be overwritten by the ones fetched from transifex (this is usually the case)
    tx pull
