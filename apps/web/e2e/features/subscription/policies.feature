@subscription @pendiente
Feature: Customer policies

  @HU-118 @SOLV-242
  Scenario: Policy list
    Given the Pólizas destination
    Then the customer sees the policy list with a light payload
    And the customer cannot renew, modify or cancel

  @HU-18 @SOLV-111
  Scenario: Coverages
    Given a policy in the policy list
    When the customer opens its detail
    Then the customer sees coverages, validity and status
    And the customer cannot renew, modify or cancel

  @HU-18 @SOLV-111
  Scenario: Missing or foreign policy
    Given the customer is signed in
    When the customer opens the detail of a policy that does not exist or belongs to someone else
    Then the customer sees a policy not found state
    And it is not revealed whether that policy exists for another customer
    And the customer can go back to the policy list
