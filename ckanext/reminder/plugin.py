import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckanext.reminder.logic import action
from ckan.lib.plugins import DefaultTranslation
from ckan.plugins.toolkit import config
from .views import get_blueprints
from ckanext.reminder import cli as cli
import logging

log = logging.getLogger(__name__)

unicode_safe = toolkit.get_validator('unicode_safe')

class ReminderPlugin(plugins.SingletonPlugin, DefaultTranslation):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IActions)
    if toolkit.check_ckan_version(min_version='2.5.0'):
        plugins.implements(plugins.ITranslation, inherit=True)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IClick)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('assets', 'reminder')

    def update_config_schema(self, schema):
        ignore_missing = toolkit.get_validator('ignore_missing')

        schema.update({
            'ckanext.reminder.email': [ignore_missing, unicode_safe],
        })

        return schema

    # IConfigurable

    def configure(self, config):
        # Raise an exception if required configs are missing
        required_keys = (
            'ckanext.reminder.site_url',
            'ckanext.reminder.email'
        )

        for key in required_keys:
            if config.get(key) is None:
                raise RuntimeError(
                    'Required configuration option {0} not found.'.format(
                        key
                    )
                )

    # IActions

    def get_actions(self):
        return {
            'send_email_reminders': action.send_email_reminders,
            'subscribe_to_package': action.subscribe_to_package,
            'get_packages_for_user': action.get_packages_for_user,
            'unsubscribe': action.unsubscribe,
            'unsubscribe_all': action.unsubscribe_all
        }

    # IPackageController

    # This function requires overriding resource_create and resource_update by adding
    # keep_deletable_attributes_in_api to context
    def after_show(self, context, data_dict):

        keep_deletable_attributes_in_api = config.get('ckanext.sixodp.keep_deletable_attributes_in_api',
                                                      context.get('keep_deletable_attributes_in_api', False))
        # Remove reminder date from api
        if (keep_deletable_attributes_in_api is False and context.get('for_edit') is not True) and data_dict.get('reminder'):
            data_dict.pop('reminder')
        return data_dict


    # IBlueprint

    def get_blueprint(self):
        return get_blueprints()


    # IClick
    def get_commands(self):
        return cli.get_commands()