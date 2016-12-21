from ckan.common import request, _
from pylons import config
from ckan import model
from ckan.lib.mailer import mail_user
from ckan.lib.mailer import mail_recipient
from ckanext.reminder.model import Reminder
from ckan.logic import ValidationError

import ckan.logic as logic
import datetime

log = __import__('logging').getLogger(__name__)

def send_email_reminders(context, data_dict):
    if request.environ.get('paste.command_request'):
        send_reminders()

def get_datasets_with_reminders():
    now = datetime.datetime.now()
    search_dict = {
        'fq': 'reminder:' + now.strftime("%Y-%m-%d")
    }

    return logic.get_action('package_search')({}, search_dict)

def send_reminders():
    '''
    Sends reminder emails to site admin of datasets which have a reminder date set
    '''

    items = get_datasets_with_reminders()

    try:
        username = config.get('ckanext.reminder.recipient_username')
        recipient = model.User.get(username)

        if(items['results']):
            log.info('Number of datasets with reminders found: ' + len(items['results']))

        for item in items['results']:

            message_body = _('This is a reminder of a dataset expiration') + ': ' + config.get('ckanext.reminder.site_url') + '/dataset/' + item['name']
            mail_user(recipient, _('CKAN reminder'), message_body)

        if len(items['results']) == 0:
            log.debug("No pending reminders for current date")
        else:
            log.debug("Reminder emails sent")

    except Exception, ex:
        log.exception(ex)
        raise

def get_updated_packages_for_user(subscriber_email):
    subscriptions = Reminder.get_user_subscriptions(subscriber_email)

    updated_packages = []
    for subscription in subscriptions:
        updated_package = logic.get_action('package_show')({}, { 'name_or_id': subscription.package_id })

        if updated_package:
            # Notify user of an updated package if not already notified
            if updated_package['metadata_modified'] > subscription.as_dict()['previous_reminder_sent']:
                updated_packages.append(updated_package)

    return updated_packages

def send_notifications():
    '''
    Sends notification emails to site users of dataset changes
    The user needs to subscribe to the dataset to receive emails
    '''

    subscribed_users = Reminder.get_subscribed_users()

    for user in subscribed_users:
        updated_packages = get_updated_packages_for_user(user.subscriber_email)
        stringified_updated_packages_list = ''
        for package in updated_packages:
            stringified_updated_packages_list += config.get('ckanext.reminder.site_url') + '/dataset/' + package.get('name') + '\n'

        if len(updated_packages) > 0:
            message_body = _('The following datasets have been updated') + ':\n' + stringified_updated_packages_list
            mail_recipient(user.subscriber_email, user.subscriber_email, _('Dataset has been updated'), message_body)

        log.info("Notification emails sent")

def subscribe_to_package(context, data_dict):
    '''Subscribe to a specific dataset (package).
    :param package: the name or id of the dataset to subscribe to
    :type package: string
    :param subscriber_email: the email with which to subscribe
    :type subscriber_email: string
    '''
    model = context.get('model')

    package_ref = data_dict.get('package')
    subscriber_email = data_dict.get('subscriber_email')
    error = None
    if not package_ref:
        error = _('You must supply a package id or name '
                  '(parameter "package").')
    elif not subscriber_email:
        error = _('You must supply a subscriber email (parameter "subscriber_email").')
    else:
        package = model.Package.get(package_ref)
        if not package:
            error = _('Not found') + ': %r' % package_ref
    if error:
        raise ValidationError(error)

    Reminder.add_subscriber(package_ref, subscriber_email)
