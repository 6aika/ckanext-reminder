import uuid
import datetime

from sqlalchemy import Column
from sqlalchemy import types
from sqlalchemy.ext.declarative import declarative_base
from ckan.lib import dictization
import ckan.model as model
from sqlalchemy.orm import load_only

log = __import__('logging').getLogger(__name__)

Base = declarative_base()

def make_uuid():
    return unicode(uuid.uuid4())

class Reminder(Base):

    __tablename__ = 'reminder'

    id = Column(types.UnicodeText, primary_key=True, default=make_uuid)
    package_id = Column(types.UnicodeText, nullable=True, index=True)
    subscriber_email = Column(types.UnicodeText, nullable=False)
    previous_reminder_sent = Column(types.DateTime, default=datetime.datetime.now)
    created = Column(types.DateTime, default=datetime.datetime.now)
    updated = Column(types.DateTime, default=datetime.datetime.now)

    def as_dict(self):
        context = {'model': model}
        reminder_dict = dictization.table_dictize(self, context)
        return reminder_dict

    @classmethod
    def get_subscribed_users(cls):
        return model.Session.query(cls).options(load_only("subscriber_email")).distinct()

    @classmethod
    def get_user_subscriptions(cls, subscriber_email):
        return model.Session.query(cls) \
            .filter(cls.subscriber_email == subscriber_email) \
            .all()

    @classmethod
    def get_user_subscription_for_package(cls, package_id, subscriber_email):
        return model.Session.query(cls) \
            .filter(cls.package_id == package_id) \
            .filter(cls.subscriber_email == subscriber_email) \
            .first()

    @classmethod
    def add_subscriber(cls, package_id, subscriber_email):

        existing_subscription = cls.get_user_subscription_for_package(package_id, subscriber_email)

        if existing_subscription:
            log.info('Subscription for package ' + package_id + ' with email ' + subscriber_email + ' already exists')
        else:
            subscription = Reminder(
                package_id = package_id,
                subscriber_email = subscriber_email
            )

            model.Session.add(subscription)
            model.repo.commit()
            log.info('Subscription added for package' + package_id + ' with email ' + subscriber_email)

def init_tables(engine):
    Base.metadata.create_all(engine)
    log.info('Reminder database tables are set-up')
