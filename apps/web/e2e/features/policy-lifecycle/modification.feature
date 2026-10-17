@policy-lifecycle @pendiente @HU-60 @SOLV-153
Feature: Policy modification

  Scenario: Adjustment without reissuing
    Given a valid policy
    When the operador changes data or coverages
    Then the policy detail shows the updated status
    And no new policy is created from scratch
