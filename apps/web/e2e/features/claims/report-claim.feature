@claims @pendiente
Feature: Report a claim

  @HU-116 @SOLV-240
  Scenario: Minimum form
    Given a valid policy and the Siniestros destination
    When the customer completes the form and continues
    Then the customer goes to the evidence step

  @HU-110 @SOLV-234
  Scenario: Notice received
    Given the customer sent the form and the evidence
    When the core stores the notice
    Then the customer sees "Aviso recibido" with the claim id
    And one CTA takes the customer to Mis siniestros
    And another CTA can go to Inicio
    And the Siniestros destination stays underlined
