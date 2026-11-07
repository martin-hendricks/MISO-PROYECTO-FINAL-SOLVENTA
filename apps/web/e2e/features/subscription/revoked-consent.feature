@subscription @HU-165 @SOLV-264
Feature: Acceptance after revoking the profiling consent

  Scenario: Consent revoked after quoting
    Given a mortgage offer quoted with the customer's profile
    And the customer then revoked the profiling consent
    When the customer accepts the mortgage offer
    Then the customer is told the profiling consent was revoked
    And the customer can start a new quote instead of retrying
