@policy-lifecycle
Feature: Policy notices

  @HU-119 @SOLV-243
  Scenario: Expiry notice
    Given a policy about to expire
    Then the customer sees the expiry notice
    And the customer cannot renew it

  # HU-120: the renewal confirmation IS the customer's read-only policy
  # detail reflecting the new finVigencia -- already exercised end-to-end by
  # "the customer can see the renewal notice without running the command" in
  # renewal.feature. This scenario stays @pendiente until its own Given/Then
  # wording gets step definitions, to avoid duplicating that coverage under
  # different step text.
  @HU-120 @SOLV-244 @pendiente
  Scenario: Renewal notice
    Given an effective renewal
    Then the customer sees the renewal confirmation notice
