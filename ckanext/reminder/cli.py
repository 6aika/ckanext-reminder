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
