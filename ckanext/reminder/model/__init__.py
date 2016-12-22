import uuid
import datetime

from sqlalchemy import Column, Table, ForeignKey, types
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from ckan.lib import dictization
from ckan.model.meta import metadata, mapper, Session
from ckan import model
from ckan.model.domain_object import DomainObject
from sqlalchemy.orm import load_only
from ckan.logic import ValidationError

log = __import__('logging').getLogger(__name__)

Base = declarative_base()

package_association_table = None

def make_uuid():
    return unicode(uuid.uuid4())

class Reminder(Base):

    __tablename__ = 'reminder_subscription'

    id = Column(types.UnicodeText, primary_key=True, default=make_uuid)
    subscriber_email = Column(types.UnicodeText, nullable=False)
    previous_reminder_sent = Column(types.DateTime, default=datetime.datetime.now)
    unsubscribe_token = Column(types.UnicodeText, nullable=True, index=True)
    created = Column(types.DateTime, default=datetime.datetime.now)
    updated = Column(types.DateTime, default=datetime.datetime.now)

    def as_dict(self):
        context = {'model': model}
        reminder_dict = dictization.table_dictize(self, context)
        return reminder_dict

    @classmethod
    def filter(cls, **kwargs):
        return model.Session.query(cls).filter_by(**kwargs)

    @classmethod
    def exists(cls, **kwargs):
        if cls.filter(**kwargs).first():
            return True
        else:
            return False

    @classmethod
    def create(cls, **kwargs):
        instance = cls(**kwargs)
        Session.add(instance)
        Session.commit()
        return instance.as_dict()

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
            .filter(cls.packages.package_id == package_id) \
            .filter(cls.subscriber_email == subscriber_email) \
            .first()

    @classmethod
    def add_subscriber(cls, package_id, subscriber_email):

        existing_subscription = cls.get_user_subscription_for_package(package_id, subscriber_email)

        if existing_subscription:
            log.info('Subscription for package ' + package_id + ' with email ' + subscriber_email + ' already exists')
        else:
            try:
                subscription = Reminder(
                    subscriber_email = subscriber_email
                )

                package = model.Package.get(package_id)

                subscription.packages.append(package)
                model.Session.add(subscription)
                model.repo.commit()
                log.info('Subscription added for package' + package_id + ' with email ' + subscriber_email)
            except ValidationError, ex:
                log.error(ex)

    @classmethod
    def remove_subscriber(cls, package_id, subscriber_email):
        subscriber = model.Session.query(cls) \
            .filter(cls.package_id == package_id) \
            .filter(cls.subscriber_email == subscriber_email)

        if(subscriber):
            subscriber.delete()
            model.repo.commit()
            return True
        return False

    @classmethod
    def update_previous_reminder_sent(cls, package_id, subscriber_email):
        existing_subscription = model.Session.query(cls) \
            .filter(cls.package_id == package_id) \
            .filter(cls.subscriber_email == subscriber_email)

        if (existing_subscription.first()):
            now = datetime.datetime.now()
            existing_subscription.update({
                'previous_reminder_sent': now,
                'updated': now
            })
            model.repo.commit()
            return True
        return False

def setup():
    # setup package_association_table
    if package_association_table is None:
        define_reminder_subscription_package_association_table()
        log.debug('ReminderSubscriptionPackageAssociation table defined in memory')

    if model.package_table.exists():
        if not package_association_table.exists():
            package_association_table.create()
            log.debug('ReminderSubscriptionPackageAssociation table create')
        else:
            log.debug('ReminderSubscriptionPackageAssociation table already exists')
    else:
        log.debug('ReminderSubscriptionPackageAssociation table creation deferred')

class ReminderSubscriptionPackageAssociation(DomainObject):

    @classmethod
    def filter(cls, **kwargs):
        return model.Session.query(cls).filter_by(**kwargs)

    @classmethod
    def exists(cls, **kwargs):
        if cls.filter(**kwargs).first():
            return True
        else:
            return False

    @classmethod
    def get(cls, **kwargs):
        instance = cls.filter(**kwargs).first()
        return instance

    @classmethod
    def create(cls, **kwargs):
        instance = cls(**kwargs)
        Session.add(instance)
        Session.commit()
        return instance.as_dict()

    @classmethod
    def get_packages_for_email(cls, subscriber_email):
        return Session.query(cls) \
            .filter(cls.subscriber_email == subscriber_email) \
            .all()

def init_tables(engine):
    Base.metadata.create_all(engine)
    log.info('Reminder database tables are set-up')

def define_reminder_subscription_package_association_table():
    global package_association_table

    package_association_table = Table(
        'reminder_subscription_package_association', metadata,
        Column('reminder_subscription_id',
               types.Text,
               ForeignKey(Reminder.id,
                          ondelete='CASCADE',
                          onupdate='CASCADE'),
               primary_key=True,
               nullable=False),
        Column('package_id',
               types.Text,
               ForeignKey('package.id',
                          ondelete='CASCADE',
                          onupdate='CASCADE'),
               primary_key=True,
               nullable=False)
    )

    mapper(ReminderSubscriptionPackageAssociation, package_association_table)
