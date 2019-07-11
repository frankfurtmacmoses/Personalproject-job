# tests/features/steps/spectre_steps.py
#
# Author: Harrison Lee
# Date: 06/27/2019
# Description: Utilizing Cucumber framework to test Watchmen (Spectre).

from behave import given, when, then
from watchmen.common.watchman import Watchman
from watchmen.models.spectre import Spectre

@given('the Spectre Watchman')
def step_impl(context):
    context.spectre = Spectre()

@when('Spectre monitors S3')
def step_impl(context):
    context.status = context.spectre.monitor()

@then('it should return a result explaining success or failure')
def step_impl(context):
    states = Watchman.STATE.values()
    assert (isinstance(context.status.success, bool))
    assert (context.status.state in states)
