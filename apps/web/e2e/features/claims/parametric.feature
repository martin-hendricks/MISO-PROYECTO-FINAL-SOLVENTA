@claims @pendiente @HU-37 @SOLV-130
Feature: Parametric payment

  Scenario: Stored summary
    Given a parametric trigger
    When the customer opens the parametric summary
    Then the customer sees the policy, threshold and amount stored by Solventa
    And the customer does not see the raw third-party message
