import uuid
import datetime

from sqlalchemy import Column, ForeignKey, types
from sqlalchemy.ext.declarative import declarative_base
from ckan.lib import dictization
from ckan.model.meta import Session
from ckan import model
from sqlalchemy.orm import load_only
from ckan.logic import ValidationError
from ckan.model.package import Package

log = __import__('logging').getLogger(__name__)

Base = declarative_base()

package_association_table = None


def make_uuid():
    return uuid.uuid4()


class Reminder(Base):
    __tablename__ = 'reminder_subscription'

    id = Column(types.UnicodeText, primary_key=True, default=make_uuid)
    subscriber_email = Column(types.UnicodeText, nullable=False)
    previous_reminder_sent = Column(types.DateTime, default=datetime.datetime.now)
    unsubscribe_token = Column(types.UnicodeText, nullable=False, default=make_uuid)
    created = Column(types.DateTime, default=datetime.datetime.now)
    updated = Column(types.DateTime, default=datetime.datetime.now)

    def as_dict(self):
        context = {'model': model}
        dictized_cls = dictization.table_dictize(self, context)
        return dictized_cls

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
    def get(cls, id):
        instance = model.Session.query(cls).filter(cls.id == id).first()
        return instance.as_dict()

    @classmethod
    def all(cls):
        q = model.Session.query(cls)
        return q.all()

    @classmethod
    def remove(cls, id):
        instance = model.Session.query(cls).filter(cls.id == id)
        instance.delete()
        model.repo.commit()

    @classmethod
    def get_subscribed_users(cls):
        return model.Session.query(cls).all()

    @classmethod
    def get_subscriber_dict(cls, subscriber_email):
        return model.Session.query(cls).filter(cls.subscriber_email == subscriber_email).first().as_dict()

    @classmethod
    def get_or_add_subscriber(cls, subscriber_email):
        subscriber = model.Session.query(cls) \
            .filter(cls.subscriber_email == subscriber_email) \
            .first()

        if not subscriber:
            try:
                subscriber = Reminder(
                    subscriber_email=subscriber_email
                )

                model.Session.add(subscriber)
                model.repo.commit()
                log.info('Subscription added for email ' + subscriber_email)
                return subscriber.as_dict()
            except ValidationError as ex:
                log.error(ex)

        return subscriber.as_dict()

    @classmethod
    def update_previous_reminder_sent(cls, subscriber_email):
        existing_subscription = model.Session.query(cls) \
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


class ReminderSubscriptionPackageAssociation(Base):
    __tablename__ = 'reminder_subscription_package_association'

    reminder_subscription_id = Column(types.Text,
                                      ForeignKey(Reminder.id,
                                                 ondelete='CASCADE',
                                                 onupdate='CASCADE'),
                                      primary_key=True,
                                      nullable=False)
    package_id = Column(types.Text,
                        ForeignKey(Package.id,
                                   ondelete='CASCADE',
                                   onupdate='CASCADE'),
                        primary_key=True,
                        nullable=False)

    def as_dict(self):
        context = {'model': model}
        dictized_cls = dictization.table_dictize(self, context)
        return dictized_cls

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
    def all(cls):
        q = model.Session.query(cls)
        return q.all()

    @classmethod
    def create(cls, **kwargs):
        instance = cls(**kwargs)
        Session.add(instance)
        Session.commit()
        return instance.as_dict()

    @classmethod
    def get_subscriber_package_ids(cls, reminder_subscription_id):
        return model.Session.query(cls) \
            .filter(cls.reminder_subscription_id == reminder_subscription_id) \
            .options(load_only("package_id")) \
            .all()

    @classmethod
    def remove(cls, package_id, reminder_subscription_id):
        subscription = model.Session.query(cls) \
            .filter(cls.package_id == package_id) \
            .filter(cls.reminder_subscription_id == reminder_subscription_id)

        if (subscription):
            remindee = model.Session.query(Reminder).filter(Reminder.id == reminder_subscription_id)
            if remindee:
                remindee.delete()
            subscription.delete()
            model.repo.commit()
            return True
        return False


def init_tables(engine):
    Base.metadata.create_all(engine)
    log.info('Reminder database tables are set-up')
