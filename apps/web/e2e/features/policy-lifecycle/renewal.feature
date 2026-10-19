@policy-lifecycle @pendiente @HU-59 @SOLV-152
Feature: Policy renewal

  Scenario: Continuous coverage
    Given a valid policy
    When the operador renews it
    Then the policy stays valid with a new validity
    And the customer can see the renewal notice without running the command

  Scenario: Policy no longer valid
    Given a policy cancelled longer ago than the grace window
    When the operador opens the renewal action
    Then the "Renovar" button is disabled
    And it explains that coverage cannot be restored by renewal
    And the only option offered is issuing a new policy
