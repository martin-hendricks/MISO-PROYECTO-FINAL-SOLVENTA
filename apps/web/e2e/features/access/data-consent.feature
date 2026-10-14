@access @pendiente @HU-115 @SOLV-239
Feature: Data processing consent

  Scenario: Consent during sign-up
    Given the customer completed sign-up
    When the customer grants data processing consent
    Then the customer lands on Inicio
    And the consent mark is auditable
