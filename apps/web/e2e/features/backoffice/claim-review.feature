@backoffice @pendiente
Feature: Back-office claim review

  @HU-26 @SOLV-119
  Scenario: Evaluate a case
    Given a claim notice created by the customer
    When the operador opens the case
    Then the operador sees evidence, policy and status on one screen
    And the operador cannot edit the photo attached by the customer

  @HU-26 @SOLV-119
  Scenario: Queue without pending notices
    Given an operador with an up-to-date queue
    When the operador opens the Avisos destination
    Then the Pendientes chip shows zero
    And the empty queue state shows the "Actualizar" action
    And neither the table nor the detail panel are shown

  @HU-27 @SOLV-120
  Scenario: Decision audit
    Given a claim notice under evaluation
    When the operador approves or rejects it
    Then who, when and why are recorded
    And the customer sees the new status in Mis siniestros

  @HU-27 @SOLV-120
  Scenario: Rejection without reason
    Given a claim notice under evaluation with the rejection dialog open
    When the operador tries to confirm without a reason
    Then the reason field is marked as an error
    And the "Rechazar aviso" button stays disabled
    And the notice keeps its under-review status

  @HU-28 @SOLV-121
  Scenario: Complex case
    Given a claim notice that is not low amount
    When the operador routes the case to an adjuster
    Then the status changes to routed
    And no workshop network is required
