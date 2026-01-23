---
name: 🐛 Bug Report
description: Report a bug in the Mini-Agent project
labels: ['bug', 'triage']
assignees:
  - zhaofei0923

body:
  - type: markdown
    attributes:
      value: |
        ## 🐛 Bug Report

        Thank you for taking the time to report a bug! Please fill out the information below to help us understand and fix the issue.

        ---

        ### 📋 Bug Description

        <!-- Describe the bug in detail. What happened? What were you expecting? -->

  - type: textarea
    id: description
    attributes:
      label: Bug Description
      description: A clear and detailed description of what the bug is
      placeholder: "I encountered a bug when..."
      required: true
    validations:
      required: true

  - type: markdown
    attributes:
      value: |
        ### 🔄 Steps to Reproduce

        <!-- Provide steps to reproduce the bug -->

  - type: textarea
    id: steps
    attributes:
      label: Steps to Reproduce
      description: List the steps to reproduce this bug
      placeholder: |
        1. First, I...
        2. Then, I...
        3. Finally, I...
      render: bash
    validations:
      required: true

  - type: markdown
    attributes:
      value: |
        ### 📱 Environment

        <!-- Tell us about your environment -->

  - type: input
    id: os
    attributes:
      label: Operating System
      description: Your operating system (e.g., Ubuntu 22.04, macOS 14, Windows 11)
      placeholder: "Ubuntu 22.04"
    validations:
      required: true

  - type: input
    id: python-version
    attributes:
      label: Python Version
      description: Python version (e.g., 3.12.0)
      placeholder: "3.12.0"
    validations:
      required: true

  - type: input
    id: mini-agent-version
    attributes:
      label: Mini-Agent Version
      description: Mini-Agent version (e.g., 0.6.0)
      placeholder: "0.6.0"

  - type: markdown
    attributes:
      value: |
        ### 💻 Expected Behavior

        <!-- What did you expect to happen? -->

  - type: textarea
    id: expected
    attributes:
      label: Expected Behavior
      description: What you expected to happen
      placeholder: "I expected the agent to..."
      required: true

  - type: markdown
    attributes:
      value: |
        ### 🚫 Actual Behavior

        <!-- What actually happened? Include any error messages -->

  - type: textarea
    id: actual
    attributes:
      label: Actual Behavior
      description: What actually happened (include error messages)
      placeholder: "The agent actually..."
      required: true

  - type: markdown
    attributes:
      value: |
        ### 📸 Screenshots / Logs

        <!-- If applicable, add screenshots or logs to help explain the problem -->

  - type: textarea
    id: logs
    attributes:
      label: Relevant Logs
      description: Include any relevant error logs or stack traces
      placeholder: |
        Error traceback:
        ...
      render: bash

  - type: textarea
    id: additional
    attributes:
      label: Additional Context
      description: Add any other context about the problem here
      placeholder: "I was using the multi-agent orchestration feature..."

  - type: markdown
    attributes:
      value: |
        ---

        ## ✅ Checklist

        - [ ] I have searched for similar issues
        - [ ] I have included all the information requested
        - [ ] I am using the latest version of Mini-Agent
        - [ ] This bug can be reproduced consistently

        Thank you for your contribution! 🙏
