@customer-portal @pendiente @HU-106 @SOLV-230
Feature: Customer profile hub

  Scenario: Perfil destination
    Given the customer is signed in
    When the customer opens Perfil
    Then the customer sees name and document without editing KYC
    And each row opens a dialog closed with "Listo", "Revocar" or "Entendido"
    And signing out with confirmation returns to login
    And there is no Renovar, Modificar or Cancelar action
