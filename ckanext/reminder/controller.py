import ckan.plugins as p
import ckan.model as model
import ckan.logic as logic
from ckan.lib.base import h
from ckan.common import request

c = p.toolkit.c
flatten_to_string_key = logic.flatten_to_string_key

class ReminderController(p.toolkit.BaseController):

    def subscribe_to_package(self, package_id):
        p.toolkit.get_action('subscribe_to_package')(
            context = {'model': model,
                       'user': c.user or c.author},
            data_dict={'package': package_id,
                       'subscriber_email': request.POST['subscriber_email']}
        )
        c.package_subscription_successful = True
        h.redirect_to(str('/dataset/' + package_id))
        return p.toolkit.render('package/read_base.html')

    def unsubscribe_index(self, subscriber_email, unsubscribe_token):
        c.subscriptions = p.toolkit.get_action('get_packages_for_user')(
            context = {'model': model,
                       'user': c.user or c.author},
            data_dict={'subscriber_email': subscriber_email,
                       'unsubscribe_token': unsubscribe_token}
        )
        return p.toolkit.render('reminder/unsubscribe.html')

    def unsubscribe(self):
        package_id = request.POST.get('package_id')
        subscriber_email = request.POST.get('subscriber_email')
        unsubscribe_token = request.POST.get('unsubscribe_token')

        p.toolkit.get_action('unsubscribe')(
            context = {'model': model,
                       'user': c.user or c.author},
            data_dict={'package_id': package_id,
                       'subscriber_email': subscriber_email,
                       'unsubscribe_token': unsubscribe_token}
        )
        h.redirect_to(str('/reminder/' + subscriber_email + '/unsubscribe/' + unsubscribe_token))
        return p.toolkit.render('reminder/unsubscribe.html')

    def unsubscribe_all(self):
        subscriber_email = request.POST.get('subscriber_email')
        unsubscribe_token = request.POST.get('unsubscribe_token')

        p.toolkit.get_action('unsubscribe_all')(
            context = {'model': model,
                       'user': c.user or c.author},
            data_dict={'subscriber_email': subscriber_email,
                       'unsubscribe_token': unsubscribe_token}
        )
        h.redirect_to(str('/reminder/' + subscriber_email + '/unsubscribe/' + unsubscribe_token))
        return p.toolkit.render('reminder/unsubscribe.html')