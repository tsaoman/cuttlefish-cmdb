from nose.tools import assert_equal

from behave import given, when, then, step

ASSETS_JSON = '/api/v1/assets.json'

@given(u'I have an asset belonging to Bob')
def step_impl(context):
    url = ASSETS_JSON
    context.page = context.client.get(url)
    assert_equal(200, context.page.status_code, "The return code should be 200, eh?")
    if 'Bob' in context.page.data:
        print "we found Bob"
    else:
        response = context.client.post('/api/v1/asset/new',
                                       data={"mac": "asdfasdfdslkj",
                                        "date_issued": "28/04/2014",
                                        "date_renewal": "01/05/2016",
                                        "owner": "Bob Smith"})
        print repr(response)
        assert_equal(200, response.status_code, "I wanted the API call to be happy")
        context.page = context.client.get(url)



@when(u'I list the assets')
def step_impl(context):
    context.page = context.client.get(ASSETS_JSON)
    context.assets = context.page.data
    assert_equal(200, context.page.status_code, "The return code should be 200, eh?")

@then(u'I will see Bob\'s asset')
def step_impl(context):
    assert 'Bob' in context.assets