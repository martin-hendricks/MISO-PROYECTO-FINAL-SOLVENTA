@policy-lifecycle @pendiente
Feature: Policy notices

  @HU-119 @SOLV-243
  Scenario: Expiry notice
    Given a policy about to expire
    Then the customer sees the expiry notice
    And the customer cannot renew it

  @HU-120 @SOLV-244
  Scenario: Renewal notice
    Given an effective renewal
    Then the customer sees the renewal confirmation notice
