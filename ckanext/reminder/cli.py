import click
from ckanext.reminder.logic import action

def get_commands():
    return [reminder]


@click.group()
def reminder():
    '''
    Send notification emails of datasets which have a reminder date set
    Usage:
        ckan reminder send
            - Sends emails of all the datasets which have reminder set to current date
    '''


@reminder.command()
def send():
    action.send_reminders()

@reminder.command()
def notify():
    action.send_notifications()

@reminder.command()
def init_db():
    import ckan.model as model
    from ckanext.reminder.model import init_tables
    init_tables(model.meta.engine)


@reminder.command()
def list_subscribers():
    from ckanext.reminder.model import ReminderSubscriptionPackageAssociation, Reminder
    from ckan.model import Package

    associations = ReminderSubscriptionPackageAssociation.all()
    subscriber_count = 0
    for assoc in associations:
        remindee = Reminder.get(assoc.reminder_subscription_id)
        dataset = Package.get(assoc.package_id).as_dict()
        click.echo(remindee.get('subscriber_email') + ': ' + dataset.get('name'))
        subscriber_count += 1

    click.echo("total %d" % subscriber_count)

@reminder.command()
def remove_all_subscribers():
    from ckanext.reminder.model import ReminderSubscriptionPackageAssociation, Reminder
    associations = ReminderSubscriptionPackageAssociation.all()
    removed = 0
    for assoc in associations:
        ReminderSubscriptionPackageAssociation.remove(assoc.package_id, assoc.reminder_subscription_id)
        removed += 1

    click.echo("Removed %d subscribers" % removed)

    dangling_remindees = Reminder.all()
    removed = 0
    for dangling in dangling_remindees:
        Reminder.remove(dangling.id)
        removed += 1

    click.echo("Removed %d dangling subscribers" % removed)