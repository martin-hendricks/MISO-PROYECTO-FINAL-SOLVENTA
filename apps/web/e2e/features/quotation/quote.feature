@quotation @pendiente @HU-104 @SOLV-228
Feature: Customer quote

  Scenario: One line of business
    Given the customer is on Inicio or uses the header CTA
    When the customer opens a new quote
    Then the product is locked to Protección de dispositivo
    And "Cotizar" goes to the offer with premium and expiry
    And "Cancelar" returns to Inicio
