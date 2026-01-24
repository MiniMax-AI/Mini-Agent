---
name: 💡 Feature Request
description: Suggest a new feature or improvement for Mini-Agent
labels: ['enhancement', 'triage']
assignees:
  - zhaofei0923

body:
  - type: markdown
    attributes:
      value: |
        ## 💡 Feature Request

        Thank you for suggesting a new feature! Please fill out the information below to help us understand your request.

        ---

        ### 🎯 Is your feature request related to a problem?

        <!-- Describe the problem you're trying to solve -->

  - type: textarea
    id: problem
    attributes:
      label: Problem Description
      description: A clear description of the problem you're trying to solve
      placeholder: "I'm trying to do X, but currently it's difficult because..."
      required: true

  - type: markdown
    attributes:
      value: |
        ### ✨ Proposed Solution

        <!-- Describe your proposed solution -->

  - type: textarea
    id: solution
    attributes:
      label: Proposed Solution
      description: A clear description of what you want to happen
      placeholder: "I would like to see a new feature that..."
      required: true

  - type: markdown
    attributes:
      value: |
        ### 🎨 Use Cases

        <!-- Describe some use cases for this feature -->

  - type: textarea
    id: usecases
    attributes:
      label: Use Cases
      description: Describe some specific use cases for this feature
      placeholder: |
        1. As a developer, I want to...
        2. As a user, I need to...
        3. In scenario X, Y would be helpful...

  - type: markdown
    attributes:
      value: |
        ### 🔧 Suggested Implementation

        <!-- If you have ideas about how to implement this feature, describe them here -->

  - type: textarea
    id: implementation
    attributes:
      label: Suggested Implementation
      description: Any ideas you have about how this could be implemented
      placeholder: |
        - New class: FeatureX
        - Method: do_something()
        - Location: mini_agent/tools/

  - type: markdown
    attributes:
      value: |
        ### 📊 Alternatives Considered

        <!-- Describe any alternative solutions you've considered -->

  - type: textarea
    id: alternatives
    attributes:
      label: Alternatives
      description: Any alternative approaches you've considered
      placeholder: "I considered using X, but it has the following drawbacks..."

  - type: markdown
    attributes:
      value: |
        ### 📦 Additional Context

        <!-- Add any other context or screenshots about the feature request here -->

  - type: textarea
    id: additional
    attributes:
      label: Additional Context
      description: Any other context about the feature request
      placeholder: "This feature would be particularly useful for..."

  - type: markdown
    attributes:
      value: |
        ---

        ## ✅ Checklist

        - [ ] I have searched for similar feature requests
        - [ ] I have provided all the information requested
        - [ ] This feature is not already implemented
        - [ ] This feature aligns with the project roadmap

        ### Related Issues/PRs

        <!-- Link any related issues or pull requests -->

  - type: textarea
    id: related
    attributes:
      label: Related Issues/PRs
      description: Links to any related issues or pull requests
      placeholder: "Related to #123, depends on #456"

        ---

        Thank you for your contribution! 🙏
