import ckan.plugins as p
import ckan.model as model
import ckan.lib.helpers as h

g = p.toolkit.g
request = p.toolkit.request
ValidationError = p.toolkit.ValidationError
abort = p.toolkit.abort
_ = p.toolkit._

def subscribe_to_package(package_id):

    try:
        p.toolkit.get_action('subscribe_to_package')(
            context={'model': model,
                     'user': g.user or g.author},
            data_dict={'package': package_id,
                       'subscriber_email': request.values.get('subscriber_email')}
        )
        g.package_subscription_successful = True
        h.redirect_to(controller='package', action='read', id=package_id)
        return p.toolkit.render('package/read_base.html')
    except ValidationError as error:
        abort(400, _('Invalid request: {error_message}').format(error_message=str(error)))


def unsubscribe_index(subscriber_email, unsubscribe_token):
    g.subscriptions = p.toolkit.get_action('get_packages_for_user')(
        context={'model': model,
                 'user': g.user or g.author},
        data_dict={'subscriber_email': subscriber_email,
                   'unsubscribe_token': unsubscribe_token}
    )
    return p.toolkit.render('reminder/unsubscribe.html')

def unsubscribe():
    package_id = request.values.get('package_id')
    subscriber_email = request.values.get('subscriber_email')
    unsubscribe_token = request.values.get('unsubscribe_token')

    p.toolkit.get_action('unsubscribe')(
        context={'model': model,
                 'user': g.user or g.author},
        data_dict={'package_id': package_id,
                   'subscriber_email': subscriber_email,
                   'unsubscribe_token': unsubscribe_token}
    )

    return h.redirect_to(controller='ckanext.reminder.controller:ReminderController', action='unsubscribe_index',
                  subscriber_email=subscriber_email, unsubscribe_token=unsubscribe_token)


def unsubscribe_all():
    subscriber_email = request.values.get('subscriber_email')
    unsubscribe_token = request.values.get('unsubscribe_token')

    p.toolkit.get_action('unsubscribe_all')(
        context={'model': model,
                 'user': g.user or g.author},
        data_dict={'subscriber_email': subscriber_email,
                   'unsubscribe_token': unsubscribe_token}
    )
    return h.redirect_to(controller='ckanext.reminder.controller:ReminderController', action='unsubscribe_index',
                  subscriber_email=subscriber_email, unsubscribe_token=unsubscribe_token)
