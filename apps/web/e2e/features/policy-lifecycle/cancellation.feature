@policy-lifecycle @HU-61 @SOLV-154
Feature: Policy cancellation

  Scenario: Coverage withdrawal
    Given a valid policy
    When the operador cancels it
    Then the policy detail shows the cancelled status
    And the customer no longer holds valid coverage

  Scenario: Policy already cancelled
    Given a policy that was already cancelled
    When the operador opens the cancel action
    Then the "Cancelar póliza" button is disabled
    And the previous cancellation is shown with date, reason and operador
    And no second premium refund is generated
