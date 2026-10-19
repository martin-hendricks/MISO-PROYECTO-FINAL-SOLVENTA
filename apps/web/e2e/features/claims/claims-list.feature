@claims @pendiente
Feature: Customer claims

  @HU-117 @SOLV-241
  Scenario: Statuses
    Given the Siniestros destination
    Then the customer sees chips and rows with the core status
    And "Reportar" opens the claim notice
    And a row opens the claim detail or the parametric summary

  @HU-111 @SOLV-235
  Scenario: Progress from the list
    Given the customer has an open claim
    When the customer opens its row in Mis siniestros
    Then the customer sees the claim detail with its current status
    And the customer sees the attached evidence
    And the customer cannot approve, reject or pay

  @HU-111 @SOLV-235
  Scenario: Parametric case opens the summary
    Given a parametric payment
    When the customer opens that case
    Then the customer sees the parametric summary, not the notice form
