@quotation @HU-105 @SOLV-229
Feature: Mortgage life offer for the customer

  Scenario: Entry from Inicio
    Given an active origination and profiling consent
    When the customer opens the Vida Crediticia card
    Then the customer sees the mortgage offer with premium and internal factors
    And if the stub failed the customer sees the degradation banner
    And "Aceptar" starts the issuance
    And Perfil does not start this flow
