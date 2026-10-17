@subscription @pendiente @HU-112 @SOLV-236
Feature: Rejected subscription

  Scenario: Visible reason
    Given the customer accepted an offer
    When the core rejects the risk
    Then the customer sees the rejected subscription with the stored reason
    And the customer can go back to Inicio
    And the customer does not see a valid policy number
