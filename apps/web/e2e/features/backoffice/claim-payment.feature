@backoffice @pendiente @HU-29 @SOLV-122
Feature: Low amount claim payment

  Scenario: Single disbursement
    Given an approved low amount claim notice
    When the operador authorizes the stub payment
    Then the simulated disbursement happens only once
    And a retry does not duplicate the movement

  Scenario: Idempotent retry
    Given a low amount payment already executed with its idempotency key
    When the operador retries the disbursement with the same key
    Then no second disbursement or accounting entry is created
    And the original payment receipt is returned
    And the trace records the retry and the returned response
