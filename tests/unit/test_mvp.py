import json
from pathlib import Path
from src.outlook.normalizer import normalize_outlook_message
from src.classifier.rules import classify_email
from src.correlation.strategy import InMemoryCorrelationStore, correlate, normalized_fingerprint, normalize_subject_for_fingerprint
from src.jira.keys import find_jira_keys
from src.jira.payloads import build_issue_payload
from src.responders.templates import render_reply
from src.intake.security import redact_mapping, redact_secrets

FIX = Path(__file__).resolve().parents[1] / 'fixtures'

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


def test_raw_payload_is_redacted_and_secret_patterns_are_covered():
    payload = load('ci_failure.json')
    payload['body']['content'] += '\nAuthorization: Bearer abc.def.ghi\nclient_secret="dontlogme"'
    email = normalize_outlook_message(payload, 'Mailbox@Example.COM')
    assert 'dontlogme' not in str(email.raw)
    assert 'abc.def.ghi' not in str(email.raw)
    assert redact_secrets('password: hunter2 token="abc123" Bearer xyz') == 'password=[REDACTED] token=[REDACTED] Bearer [REDACTED]'
    assert redact_mapping({'token': 'abc', 'nested': {'authorization': 'Bearer xyz'}})['token'] == '[REDACTED]'


def test_conversation_id_suppresses_duplicate_thread_without_jira_key():
    store = InMemoryCorrelationStore()
    first_email = normalize_outlook_message(load('vm_request.json'), 'm')
    first_cls = classify_email(first_email)
    assert correlate(first_email, first_cls, store)[0] == 'create'

    reply_payload = load('vm_request.json') | {'id': '2b', 'internetMessageId': '<vm-reply@example>', 'subject': 'Re: VM request for analytics'}
    reply_email = normalize_outlook_message(reply_payload, 'm')
    reply_cls = classify_email(reply_email)
    action, key, duplicate_of, _ = correlate(reply_email, reply_cls, store)
    assert action == 'duplicate'
    assert key is None
    assert duplicate_of is not None


def test_subject_fingerprint_normalization_removes_thread_prefixes_and_jira_keys():
    assert normalize_subject_for_fingerprint('Re: Fwd: [OPS-123] VM request for analytics') == 'vm request for analytics'


def test_commit_label_extraction_and_requester_safe_reply_text():
    payload = load('ci_failure.json')
    payload['body']['content'] = 'Repository: org/payments\nBranch: main\nCommit: abcdef123456\nBuild failed https://jenkins.example/job/payments/123'
    cls = classify_email(normalize_outlook_message(payload, 'm'))
    assert cls.extracted_fields['commit_sha'] == 'abcdef123456'
    reply = render_reply('missing_info', 'Dev', classification=cls)
    assert 'do not include passwords, tokens, or private keys' in reply
