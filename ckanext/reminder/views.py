from flask import Blueprint
from ckanext.reminder import utils as utils

reminder = Blueprint('reminder', __name__)


def subscribe_to_package(package_id):
    return utils.subscribe_to_package(package_id)

def unsubscribe(subscriber_email, unsubscribe_token):
    return utils.unsubscribe(subscriber_email, unsubscribe_token)

def unsubscribe_index(subscriber_email, unsubscribe_token):
    return utils.unsubscribe_index(subscriber_email, unsubscribe_token)

def unsubscribe_all(subscriber_email, unsubscribe_token):
    return utils.unsubscribe_all(subscriber_email, unsubscribe_token)

reminder.add_url_rule('/dataset/<package_id>/subscribe', view_func=subscribe_to_package, methods=['POST'])
reminder.add_url_rule('/reminder/<subscriber_email>/unsubscribe/<unsubscribe_token>', view_func=unsubscribe, methods=['POST'])
reminder.add_url_rule('/reminder/<subscriber_email>/unsubscribe/<unsubscribe_token>', view_func=unsubscribe_index, methods=['GET'])
reminder.add_url_rule('/reminder/<subscriber_email>/unsubscribe/<unsubscribe_token>/all', view_func=unsubscribe_all, methods=['POST'])

def get_blueprints():
    return [reminder]