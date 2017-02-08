import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckanext.reminder.logic import action

class ReminderPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IRoutes, inherit=True)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'reminder')
        toolkit.add_resource('public/css/', 'reminder_css')

    def update_config_schema(self, schema):
        ignore_missing = toolkit.get_validator('ignore_missing')

        schema.update({
            'ckanext.reminder.email': [ignore_missing, unicode],
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

    # IRoutes

    def before_map(self, map):
        map.connect('/dataset/{package_id}/subscribe',
                    controller='ckanext.reminder.controller:ReminderController',
                    action='subscribe_to_package')

        map.connect('/reminder/{subscriber_email}/unsubscribe/{unsubscribe_token}',
                    controller='ckanext.reminder.controller:ReminderController',
                    action='unsubscribe_index',
                    conditions=dict(method=['GET']))

        map.connect('/reminder/{subscriber_email}/unsubscribe/{unsubscribe_token}',
                    controller='ckanext.reminder.controller:ReminderController',
                    action='unsubscribe',
                    conditions=dict(method=['POST']))

        map.connect('/reminder/{subscriber_email}/unsubscribe/{unsubscribe_token}/all',
                    controller='ckanext.reminder.controller:ReminderController',
                    action='unsubscribe_all',
                    conditions=dict(method=['POST'])),

        return map
    
