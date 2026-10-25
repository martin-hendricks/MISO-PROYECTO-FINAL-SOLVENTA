@quotation @HU-104 @SOLV-228
Feature: Customer quote

  Scenario: One line of business
    Given the customer is on Inicio or uses the header CTA
    When the customer opens a new quote
    Then the customer picks the line, starting on Protección de dispositivo
    And the lines the core does not quote yet are disabled as Próximamente
    And "Cotizar" goes to the offer with premium and expiry
    And "Cancelar" returns to Inicio
