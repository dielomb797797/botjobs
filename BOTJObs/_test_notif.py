# -*- coding: utf-8 -*-
"""Test desktop notifications - 3 unique toasts with longer spacing."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from notifier import send_toast

# Notifica 1
print("[1/3] Mollie...")
send_toast(
    title="[97] Mollie - Sales Engineer I",
    message="Amsterdam | title:sales engineer, api, rest api, integration, saas, postman",
    url="https://jobs.ashbyhq.com/mollie/97255d06-2847-4579-b1fc-1aebaadc1ec5",
    tag="test-mollie-97",
)
time.sleep(5)

# Notifica 2
print("[2/3] Datadog Madrid...")
send_toast(
    title="[85] Datadog - Technical Account Manager 3",
    message="Madrid, Spain | technical account manager, onboarding, python, git, docker",
    url="https://careers.datadoghq.com/detail/7982225/?gh_jid=7982225",
    tag="test-datadog-85",
)
time.sleep(5)

# Notifica 3
print("[3/3] Mendix...")
send_toast(
    title="[87] Mendix - Solutions Engineer (Core AI)",
    message="Amsterdam | solutions engineer, api, integration, workflow, llm, ai tooling",
    url="https://jobs.lever.co/mendix/c0c545fe-53ae-4eda-869f-da2871dac697",
    tag="test-mendix-87",
)

print("\nDone. Controlla il Notification Center (Win+N):")
print("dovresti vedere 3 popup separati, ognuno con bottone 'Apply now'.")
