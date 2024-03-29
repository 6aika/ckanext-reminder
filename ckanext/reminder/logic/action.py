from ckan.common import request, _
from ckan.plugins.toolkit import config
from ckan.lib.mailer import mail_recipient
from ckanext.reminder.model import Reminder, ReminderSubscriptionPackageAssociation
from ckan.logic import ValidationError
from ckan.lib.mailer import MailerException
import ckan.logic as logic
import datetime
import logging

log = logging.getLogger(__name__)


def send_email_reminders(context, data_dict):
    if request.environ.get('paste.command_request'):
        send_reminders()


def get_datasets_with_reminders():
    '''
    Returns a dict containing items that expire on current day
    based on a field defined in the config file.
    '''
    now = datetime.datetime.now()
    search_dict = {
        'fq': config.get('ckanext.reminder.date_field') + ":" + now.strftime("%Y-%m-%d")
    }

    return logic.get_action('package_search')({}, search_dict)


def send_reminders():
    '''
    Sends reminder emails to site admin of datasets which have a reminder date set
    '''

    items = get_datasets_with_reminders()

    try:
        recipient_email_default = config.get('ckanext.reminder.email')
        email_field_name = config.get('ckanext.reminder.email_field')
        recipient_name_field = config.get('ckanext.reminder.recipient_name')
        if (items['results']):
            log.debug('Number of datasets with reminders found: ' + str(len(items['results'])))
        else:
            log.debug('No datasets found with reminder set to current date')

        for item in items['results']:
            if (email_field_name in item and item[email_field_name] != ""):
                recipient_email = item[email_field_name]
            else:
                recipient_email = recipient_email_default

            if (recipient_name_field in item and item[recipient_name_field] != ""):
                recipient_name = item[recipient_name_field]
            else:
                recipient_name = ""
            message_body = _('This is a reminder of a dataset expiration') + ': ' + config.get(
                'ckanext.reminder.site_url') + '/dataset/' + item['name']

            try:

                mail_recipient(recipient_name, recipient_email, _('CKAN reminder'), message_body)
            except MailerException as ex:
                log.error("There was an error with sending email to the following address: " + recipient_email)
                log.exception(ex)
        log.debug("Reminder emails processed")

    # Some other error than MailerException happened
    except Exception as ex:
        log.exception(ex)
        raise


def get_packages_for_user(context, data_dict):
    '''
    Returns a list of packages for the provided email address
    Returns an empty list if the unsubscribe does not match to the subscriber's token
    '''
    subscriber_email = data_dict.get('subscriber_email')
    unsubscribe_token = data_dict.get('unsubscribe_token')
    subscriber = Reminder.get_subscriber_dict(subscriber_email)

    packages = []

    # Make sure the given unsubscribe token matches the stored one
    # Return empty list if no match, for security
    if subscriber and subscriber.get('unsubscribe_token') == unsubscribe_token:
        package_ids = ReminderSubscriptionPackageAssociation.get_subscriber_package_ids(subscriber.get('id'))

        for package_id in package_ids:
            package = logic.get_action('package_show')({}, {'name_or_id': package_id.package_id})
            if package:
                packages.append(package)
    return packages


def get_updated_packages_for_user(subscriber_id, previous_reminder_sent):
    subscriptions = ReminderSubscriptionPackageAssociation.get_subscriber_package_ids(subscriber_id)

    updated_packages = []
    for subscription in subscriptions:
        updated_package = logic.get_action('package_show')({}, {'name_or_id': subscription.package_id})

        if updated_package:
            # Notify user of an updated package if not already notified
            if updated_package['metadata_modified'] > previous_reminder_sent:
                updated_packages.append(updated_package)

    return updated_packages


def send_notifications():
    '''
    Sends notification emails to site users of dataset changes
    The user needs to subscribe to the dataset to receive emails
    '''

    subscribed_users = Reminder.get_subscribed_users()

    for subscriber in subscribed_users:
        updated_packages = get_updated_packages_for_user(subscriber.id, subscriber.as_dict()['previous_reminder_sent'])
        stringified_updated_packages_list = ''
        for package in updated_packages:
            stringified_updated_packages_list += config.get('ckanext.reminder.site_url') + '/dataset/' + package.get(
                'name') + '\n'

        if len(updated_packages) > 0:
            message_body = _('The following datasets have been updated') + ':\n' + stringified_updated_packages_list + \
                           '\nUnsubscribe from this newsletter: ' + config.get('ckanext.reminder.site_url') + '/reminder/' + \
                           subscriber.subscriber_email + '/unsubscribe/' + subscriber.unsubscribe_token

            mail_recipient("", subscriber.subscriber_email, _('Dataset has been updated'), message_body)
            Reminder.update_previous_reminder_sent(subscriber.subscriber_email)

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
        else:
            subscriber = Reminder.get_or_add_subscriber(subscriber_email)
            if not ReminderSubscriptionPackageAssociation.exists(package_id=package.id,
                                                                 reminder_subscription_id=subscriber['id']):
                ReminderSubscriptionPackageAssociation.create(package_id=package.id,
                                                              reminder_subscription_id=subscriber['id'])
    if error:
        raise ValidationError(error)


def unsubscribe(context, data_dict):
    'Unsubscribe a specific package'
    package_id = data_dict.get('package_id')
    subscriber_email = data_dict.get('subscriber_email')
    unsubscribe_token = data_dict.get('unsubscribe_token')
    subscriber = Reminder.get_subscriber_dict(subscriber_email)

    error = None
    if not package_id:
        error = _('You must supply a package id '
                  '(parameter "package_id").')
    elif not subscriber_email:
        error = _('You must supply a subscriber email (parameter "subscriber_email").')
    elif not unsubscribe_token:
        error = _('You must supply an unsubscribe token (parameter "unsubscribe_token").')

    if not error and unsubscribe_token == subscriber.get('unsubscribe_token'):
        ReminderSubscriptionPackageAssociation.remove(package_id=package_id,
                                                      reminder_subscription_id=subscriber.get('id'))
    if error:
        raise ValidationError(error)


def unsubscribe_all(context, data_dict):
    'Unsubscribe all packages'
    subscriber_email = data_dict.get('subscriber_email')
    unsubscribe_token = data_dict.get('unsubscribe_token')
    subscriber = Reminder.get_subscriber_dict(subscriber_email)

    error = None
    if not subscriber_email:
        error = _('You must supply a subscriber email (parameter "subscriber_email").')
    elif not unsubscribe_token:
        error = _('You must supply an unsubscribe token (parameter "unsubscribe_token").')

    if not error and unsubscribe_token == subscriber.get('unsubscribe_token'):

        package_ids = ReminderSubscriptionPackageAssociation.get_subscriber_package_ids(subscriber.get('id'))

        for package_id in package_ids:
            ReminderSubscriptionPackageAssociation.remove(package_id=package_id.package_id,
                                                          reminder_subscription_id=subscriber.get('id'))
    if error:
        raise ValidationError(error)
