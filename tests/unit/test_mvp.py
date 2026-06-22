import json
from pathlib import Path
from src.outlook.normalizer import normalize_outlook_message
from src.classifier.rules import classify_email
from src.correlation.strategy import InMemoryCorrelationStore, correlate, normalized_fingerprint
from src.jira.keys import find_jira_keys
from src.jira.payloads import build_issue_payload
from src.responders.templates import render_reply

FIX = Path('tests/fixtures')

def load(name): return json.loads((FIX / name).read_text())

def category(name):
    return classify_email(normalize_outlook_message(load(name), 'devops@example.com'))

def test_required_categories_classify_correctly():
    assert category('ci_failure.json').category == 'CI Failure'
    assert category('vm_request.json').category == 'VM Request'
    assert category('license_request.json').category == 'License Request'
    assert category('access_request.json').category == 'Access Request'
    assert category('new_project.json').category == 'New Project Request'
    assert category('org_mail.json').category == 'Organizational Mail'
    assert category('org_mail.json').confidence >= .8

def test_normalization_extracts_links_and_redacts():
    payload = load('ci_failure.json'); payload['body']['content'] += '\ntoken=supersecret'
    email = normalize_outlook_message(payload, 'Mailbox@Example.COM')
    assert email.source_mailbox == 'mailbox@example.com'
    assert email.links == ['https://jenkins.example/job/payments/123']
    assert 'supersecret' not in email.body

def test_jira_key_detection_update_flow():
    email = normalize_outlook_message(load('ci_failure.json') | {'subject':'Re: OPS-123 build failed'}, 'm')
    cls = classify_email(email)
    action, key, dup, fp = correlate(email, cls, InMemoryCorrelationStore())
    assert find_jira_keys(email.subject) == ['OPS-123']
    assert action == 'update' and key == 'OPS-123' and dup is None

def test_duplicate_detection_by_message_and_fingerprint():
    store = InMemoryCorrelationStore(); email = normalize_outlook_message(load('vm_request.json'), 'm'); cls = classify_email(email)
    first = correlate(email, cls, store)
    second = correlate(email, cls, store)
    assert first[0] == 'create'
    assert second[0] == 'duplicate'
    assert second[2] is not None
    assert normalized_fingerprint(email, cls) == first[3]

def test_missing_info_reply_for_incomplete_vm():
    payload = load('vm_request.json'); payload['body']['content'] = 'Please provision a VM for project: analytics'
    cls = classify_email(normalize_outlook_message(payload, 'm'))
    assert 'environment' in cls.missing_fields
    reply = render_reply('missing_info', 'Analyst', classification=cls)
    assert 'environment' in reply and 'VM Request' in reply

def test_jira_payload_is_config_driven_and_safe():
    email = normalize_outlook_message(load('license_request.json'), 'm'); cls = classify_email(email)
    payload = build_issue_payload(email, cls, {'jira': {'project_key':'OPS','issue_type_mapping': {'License Request':'Service Request'}, 'custom_field_mapping': {'project':'customfield_1'}}})
    fields = payload['fields']
    assert fields['project']['key'] == 'OPS'
    assert fields['issuetype']['name'] == 'Service Request'
    assert fields['customfield_1'] == 'core'
    assert 'token' not in str(payload).lower()

def test_all_reply_templates_render():
    for kind in ['created','duplicate','rejected','approval_required','automation_failed','completed']:
        assert render_reply(kind, 'dev@example.com', jira_key='OPS-1', duplicate_of='abc')
